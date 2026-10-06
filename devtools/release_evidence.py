"""Read-only, candidate-bound evidence checks for the local Viewer release gate.

The input names expected identities, never supplies a PASS verdict. GitHub and
the Conda channel are queried independently. This is a local consumer profile,
not the still-proposed shared MolSysSuite release-manifest schema (#27).
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile

PLATFORMS = ("linux-64", "linux-aarch64", "osx-arm64", "win-64")
PYTHONS = ("3.11", "3.12", "3.13", "3.14")
EVIDENCE_STEPS = ("conda", "public_conda", "hosted_e2e")
LIMIT = 16 * 1024 * 1024


class MissingEvidence(Exception):
    """Required evidence cannot be acquired; this is not a passing check."""


class InvalidEvidence(Exception):
    """Available evidence contradicts the requested identity or required gate."""


def require(condition, detail):
    if not condition:
        raise InvalidEvidence(detail)


def validate_plan(plan):
    """Validate exact coordinates before reading GitHub or registry evidence."""
    require(
        isinstance(plan, dict) and plan.get("schema") == "molsysviewer.release-evidence/1",
        "unknown candidate evidence schema",
    )
    for name in ("molsysviewer", "molsysmt"):
        item = plan.get(name)
        require(isinstance(item, dict), f"missing {name} candidate")
        require(
            isinstance(item.get("version"), str)
            and re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", item["version"]),
            f"{name} version must be stable X.Y.Z",
        )
        require(
            isinstance(item.get("commit"), str) and re.fullmatch(r"[0-9a-f]{40}", item["commit"]),
            f"{name} requires a full commit SHA",
        )
        require(
            type(item.get("build_number")) is int and item["build_number"] >= 0,
            f"{name} build number must be a nonnegative integer",
        )
        files = item.get("files")
        expected = {"noarch"} if name == "molsysviewer" else set(PLATFORMS)
        require(isinstance(files, list) and len(files) == len(expected), f"incomplete {name} artifact set")
        seen = set()
        for file in files:
            require(isinstance(file, dict), f"invalid {name} file record")
            subdir, filename, digest = file.get("subdir"), file.get("filename"), file.get("sha256")
            require(
                isinstance(subdir, str) and subdir in expected and subdir not in seen,
                f"duplicate or unsupported {name} platform",
            )
            seen.add(subdir)
            build = item["build_number"]
            version = re.escape(item["version"])
            pattern = (
                rf"molsysviewer-{version}-py_{build}\.tar\.bz2"
                if name == "molsysviewer"
                else rf"molsysmt-{version}-pyabi3[a-zA-Z0-9]+_{build}\.(?:conda|tar\.bz2)"
            )
            require(
                isinstance(filename, str) and re.fullmatch(pattern, filename),
                f"{name} filename does not match version/build",
            )
            require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest), f"{name} file requires SHA-256")
    for step in EVIDENCE_STEPS:
        run = plan.get(step)
        if run is not None:
            require(
                isinstance(run, dict)
                and type(run.get("id")) is int
                and run["id"] > 0
                and type(run.get("attempt")) is int
                and run["attempt"] > 0,
                f"{step} requires a numeric run ID and attempt",
            )
    exceptions = plan.get("exceptions", [])
    require(isinstance(exceptions, list), "exceptions must be a list")
    seen = set()
    for exception in exceptions:
        require(isinstance(exception, dict), "invalid exception record")
        step = exception.get("step")
        require(
            isinstance(step, str) and step in EVIDENCE_STEPS and step not in seen,
            "exception must name one distinct evidence step",
        )
        seen.add(step)
        require(
            exception.get("version") == plan["molsysviewer"]["version"]
            and exception.get("commit") == plan["molsysviewer"]["commit"],
            "exception belongs to another candidate",
        )
        require(
            isinstance(exception.get("issue"), str)
            and re.fullmatch(r"uibcdf/[a-z0-9_-]+#[1-9][0-9]*", exception["issue"]),
            "exception requires an issue",
        )
        for key in ("reason", "approved_by"):
            require(isinstance(exception.get(key), str) and exception[key].strip(), f"exception requires {key}")
    return plan


def check_checkout(plan, root, reported_version=None):
    """Only a clean checkout of the declared Viewer commit can be qualified."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
    require(head.stdout.strip() == plan["molsysviewer"]["commit"], "Viewer checkout differs from candidate commit")
    state = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, capture_output=True, text=True, check=True
    )
    require(not state.stdout.strip(), "Viewer candidate checkout is dirty; freeze the candidate first")
    if reported_version is not None:
        require(plan["molsysviewer"]["version"] == reported_version, "Viewer package version differs from candidate")


def check_run(run, expected, repository, workflow, commit):
    require(
        isinstance(run, dict) and run.get("id") == expected["id"] and run.get("run_attempt") == expected["attempt"],
        "GitHub run ID/attempt differs",
    )
    require(run.get("repository", {}).get("full_name") == repository, "GitHub run repository differs")
    require(run.get("head_sha") == commit, "GitHub run commit differs from candidate")
    require(run.get("path", "").split("@", 1)[0] == workflow, "GitHub workflow differs")
    if run.get("status") != "completed":
        raise MissingEvidence("GitHub run is not completed")
    require(run.get("conclusion") == "success", "GitHub run did not succeed")


def check_jobs(document, run_id, attempt, *, allowed_skipped=()):
    jobs = document.get("jobs")
    require(isinstance(jobs, list) and document.get("total_count") == len(jobs), "incomplete GitHub job inventory")
    for name in allowed_skipped:
        require(sum(job.get("name") == name for job in jobs) <= 1, "ambiguous conditional control job")
    for job in jobs:
        require(job.get("run_id") == run_id and job.get("run_attempt") == attempt, "job belongs to another run/attempt")
        require(
            job.get("status") == "completed"
            and (
                job.get("conclusion") == "success"
                or (job.get("name") in allowed_skipped and job.get("conclusion") == "skipped")
            ),
            "required job did not complete successfully",
        )
    return jobs


def check_pair_run(plan, source, run, document):
    step = "conda" if source == "staging" else "public_conda"
    expected = plan[step]
    check_run(
        run, expected, "uibcdf/molsysmt", ".github/workflows/validate_conda_staging.yaml", plan["molsysmt"]["commit"]
    )
    mt, viewer = plan["molsysmt"], plan["molsysviewer"]
    title = (
        f"MT {mt['version']} build {mt['build_number']} + Viewer {viewer['version']} "
        f"build {viewer['build_number']} | Python 3.14 | all" + (" | public" if source == "public" else "")
    )
    require(run.get("display_title") == title, "installed-pair versions, builds, source or coverage differ")
    jobs = check_jobs(document, expected["id"], expected["attempt"])
    cells = {f"{platform} · Python {python}" for platform in PLATFORMS for python in PYTHONS}
    names = [job.get("name") for job in jobs]
    require(
        len(names) == len(cells) + 1 and set(names) == cells | {"Validate the requested package versions"},
        "installed-pair matrix must cover exactly four platforms and Python 3.11–3.14",
    )
    for job in jobs:
        if job["name"] in cells:
            required = "Validate versions, provenance, native code, BCIF, PDB text, and viewer resources"
            require(
                any(
                    item.get("name") == required and item.get("conclusion") == "success"
                    for item in job.get("steps", [])
                ),
                "installed scientific/resource validation was skipped",
            )


def check_registry(release, index, package, version, file, label):
    """Bind the installed MD5 to the expected SHA-256 and solver-visible file."""
    basename = f"{file['subdir']}/{file['filename']}"
    require(isinstance(release, dict) and isinstance(index, dict), "invalid registry response")
    distributions = release.get("distributions")
    require(
        isinstance(distributions, list) and all(isinstance(item, dict) for item in distributions),
        "invalid registry distribution inventory",
    )
    records = [item for item in distributions if item.get("basename") == basename]
    if not records:
        raise MissingEvidence(f"{basename} is absent from the channel release inventory")
    require(len(records) == 1, "duplicate registry file record")
    record = records[0]
    require(record.get("sha256") == file["sha256"], "registry SHA-256 differs from candidate")
    require(record.get("attrs", {}).get("subdir") == file["subdir"], "registry subdir differs")
    if label not in record.get("labels", []):
        raise MissingEvidence(f"{basename} has no {label} label")
    require(index.get("info", {}).get("subdir") == file["subdir"], "repodata subdir differs")
    section = "packages.conda" if file["filename"].endswith(".conda") else "packages"
    indexed = index.get(section, {}).get(file["filename"])
    if indexed is None:
        raise MissingEvidence(f"{basename} is not solver-visible on {label}")
    require(
        indexed.get("name") == package
        and indexed.get("version") == version
        and indexed.get("sha256") == file["sha256"],
        "solver-visible identity/SHA-256 differs",
    )
    build = file["filename"].removeprefix(f"{package}-{version}-").removesuffix(".conda").removesuffix(".tar.bz2")
    require(
        indexed.get("build") == build
        and type(indexed.get("build_number")) is int
        and indexed["build_number"] == int(build.rsplit("_", 1)[1]),
        "solver-visible build differs",
    )
    md5 = record.get("md5")
    require(isinstance(md5, str) and re.fullmatch(r"[0-9a-f]{32}", md5), "registry has no valid MD5 binding")
    require(indexed.get("md5") == md5, "registry and index MD5 differ")
    return md5


def check_environment(text, plan, platform, label, md5s):
    lines = text.splitlines()
    require("@EXPLICIT" in lines, "environment record is not an explicit installed inventory")
    for name in ("molsysviewer", "molsysmt"):
        file = next(
            item for item in plan[name]["files"] if item["subdir"] == ("noarch" if name == "molsysviewer" else platform)
        )
        entries = [
            line for line in lines if not line.startswith("#") and Path(urlsplit(line).path).name.startswith(name + "-")
        ]
        require(len(entries) == 1, f"environment must install exactly one {name} file")
        parsed = urlsplit(entries[0])
        prefix = "/uibcdf/label/staging/" if label == "staging" else "/uibcdf/"
        require(
            parsed.scheme == "https"
            and parsed.netloc == "conda.anaconda.org"
            and not parsed.query
            and parsed.path == prefix + file["subdir"] + "/" + file["filename"],
            f"installed {name} coordinate/channel differs",
        )
        require(parsed.fragment in (file["sha256"], md5s[(name, file["subdir"])]), f"installed {name} digest differs")


def read_environment_archive(payload, artifact, run, platform, python):
    require(len(payload) <= LIMIT, "environment artifact exceeds size limit")
    require(
        artifact.get("digest") == "sha256:" + hashlib.sha256(payload).hexdigest(),
        "GitHub environment artifact digest differs",
    )
    require(
        artifact.get("workflow_run", {}).get("id") == run["id"]
        and artifact["workflow_run"].get("head_sha") == run["head_sha"],
        "artifact belongs to another run/commit",
    )
    require(
        datetime.fromisoformat(artifact["created_at"]) >= datetime.fromisoformat(run["run_started_at"]),
        "artifact predates the selected run attempt",
    )
    with ZipFile(io.BytesIO(payload)) as archive:
        expected = f"conda-{platform}-py{python}.txt"
        require(archive.namelist() == [expected], "environment artifact contains unexpected files")
        require(archive.getinfo(expected).file_size <= LIMIT, "expanded environment artifact exceeds size limit")
        return archive.read(expected).decode("utf-8")


class LiveEvidence:
    """Bounded read-only GitHub and public-channel acquisition, cached per run."""

    def __init__(self):
        self.cache = {}

    def github(self, path, *, binary=False):
        if path not in self.cache:
            result = subprocess.run(["gh", "api", path], capture_output=True, timeout=45)
            if result.returncode:
                raise MissingEvidence("GitHub evidence query failed; inspect credentials/connectivity and the run")
            require(len(result.stdout) <= LIMIT, "GitHub response exceeds size limit")
            self.cache[path] = result.stdout
        return self.cache[path] if binary else json.loads(self.cache[path])

    def registry(self, url):
        if url not in self.cache:
            request = Request(url, headers={"User-Agent": "molsysviewer-release-gate/1"})
            with urlopen(request, timeout=20) as response:
                payload = response.read(LIMIT + 1)
            require(len(payload) <= LIMIT, "registry response exceeds size limit")
            self.cache[url] = json.loads(payload)
        return self.cache[url]


class CandidateEvidence:
    def __init__(self, path, root, *, pre_release=False, reader=None, reported_version=None):
        self.path, self.root, self.pre_release = path, root, pre_release
        self.reader = reader or LiveEvidence()
        self.reported_version = reported_version

    def evaluate(self, step):
        """Return PASS/FAIL/BLOCKED/EXCEPTION without treating exceptions as passes."""
        plan = None
        try:
            if self.path is None:
                raise MissingEvidence("exact-candidate evidence is missing; supply --candidate-evidence (issue #103)")
            require(self.path.stat().st_size <= LIMIT, "candidate evidence exceeds size limit")
            plan = validate_plan(json.loads(self.path.read_text(encoding="utf-8")))
            check_checkout(plan, self.root, self.reported_version)
            pre_version = plan["molsysviewer"]["version"].startswith("0.")
            require(not self.pre_release or pre_version, "pre-1.0 mode is forbidden for a 1.0 candidate")
            require(self.pre_release or not pre_version, "strict 1.0 gate refuses a pre-1.0 candidate")
            require(not plan.get("exceptions") or self.pre_release, "strict 1.0 gate forbids exceptions")
            if plan.get(step) is None:
                raise MissingEvidence(f"{step} has no exact run ID/attempt for this candidate")
            if step == "hosted_e2e":
                self._hosted(plan)
            else:
                self._pair(plan, "staging" if step == "conda" else "public")
            return "PASS", f"exact {step} evidence verified for Viewer {plan['molsysviewer']['version']}"
        except MissingEvidence as error:
            if plan and self.pre_release:
                for exception in plan.get("exceptions", []):
                    if exception["step"] == step:
                        return "EXCEPTION", (
                            f"declared pre-1.0 exception ({exception['issue']}, "
                            f"{exception['approved_by']}): {exception['reason']}; {error}"
                        )
            return "BLOCKED", str(error)
        except (InvalidEvidence, ValueError, KeyError, TypeError, AttributeError, BadZipFile) as error:
            return "FAIL", str(error)
        except (OSError, URLError, subprocess.SubprocessError) as error:
            return "BLOCKED", f"cannot acquire candidate evidence: {type(error).__name__}"

    def _run(self, repository, expected):
        base = f"repos/{repository}/actions/runs/{expected['id']}"
        return (
            self.reader.github(base),
            self.reader.github(base + f"/attempts/{expected['attempt']}/jobs?per_page=100"),
            base,
        )

    def _hosted(self, plan):
        run, document, _ = self._run("uibcdf/molsysviewer", plan["hosted_e2e"])
        check_run(
            run,
            plan["hosted_e2e"],
            "uibcdf/molsysviewer",
            ".github/workflows/CI_e2e.yaml",
            plan["molsysviewer"]["commit"],
        )
        jobs = check_jobs(document, run["id"], run["run_attempt"], allowed_skipped=("Check skipped-commit backlog",))
        core = [item for job in jobs for item in job.get("steps", []) if item.get("name") == "Run core E2E tests"]
        require(len(core) == 1 and core[0].get("conclusion") == "success", "hosted core E2E was absent or skipped")

    def _pair(self, plan, source):
        step = "conda" if source == "staging" else "public_conda"
        run, document, base = self._run("uibcdf/molsysmt", plan[step])
        check_pair_run(plan, source, run, document)
        label = "staging" if source == "staging" else "main"
        md5s = {}
        for package in ("molsysviewer", "molsysmt"):
            release = self.reader.registry(
                f"https://api.anaconda.org/release/uibcdf/{package}/{plan[package]['version']}"
            )
            for file in plan[package]["files"]:
                channel = "uibcdf/label/staging" if label == "staging" else "uibcdf"
                index = self.reader.registry(f"https://conda.anaconda.org/{channel}/{file['subdir']}/repodata.json")
                md5s[(package, file["subdir"])] = check_registry(
                    release, index, package, plan[package]["version"], file, label
                )
        inventory = self.reader.github(base + "/artifacts?per_page=100")
        artifacts = inventory.get("artifacts", [])
        require(inventory.get("total_count") == len(artifacts), "incomplete artifact inventory")
        for platform in PLATFORMS:
            for python in PYTHONS:
                name = f"conda-{source}-{platform}-py{python}"
                matches = [item for item in artifacts if item.get("name") == name]
                if not matches:
                    raise MissingEvidence(f"missing environment artifact {name}")
                require(len(matches) == 1, f"ambiguous environment artifact {name}")
                artifact = matches[0]
                if artifact.get("expired") is not False:
                    raise MissingEvidence(f"expired environment artifact {name}; repeat the exact installed gate")
                require(type(artifact.get("id")) is int and artifact["id"] > 0, "invalid artifact ID")
                payload = self.reader.github(
                    f"repos/uibcdf/molsysmt/actions/artifacts/{artifact['id']}/zip", binary=True
                )
                text = read_environment_archive(payload, artifact, run, platform, python)
                check_environment(text, plan, platform, label, md5s)
