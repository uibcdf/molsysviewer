"""Read-only audit of Viewer packaging, environments and exact source providers.

Run before packaging: python devtools/audit_dependency_contract.py
After installing a controlled source, also pass --installed-source NAME=PATH@SHA.
Metadata consistency and installed-source identity do not prove API compatibility.
"""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

import yaml
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "devtools/dependency_contract.toml"


def _requirements(items):
    result = {}
    for raw in items:
        # Conda's single '=' selects a version prefix, unlike PEP 440's '=='.
        raw = re.sub(r"(?<![<>=!~])=(?!=)([0-9][\w.]*)", r"==\1.*", raw)
        requirement = Requirement(raw)
        name = canonicalize_name(requirement.name)
        if name in result:
            raise ValueError(f"duplicate requirement: {name}")
        if requirement.marker or requirement.url or requirement.extras:
            raise ValueError(f"unsupported conditional, URL or extra requirement: {raw}")
        _interval(requirement.specifier)
        result[name] = requirement
    return result


def _interval(specifiers):
    lower, upper = None, None
    for spec in specifiers:
        op, value = spec.operator, spec.version
        if op == "==" and value.endswith(".*"):
            parts = [int(part) for part in value[:-2].split(".")]
            stop = parts[:-1] + [parts[-1] + 1]
            bounds = [(True, (Version(value[:-2]), True)), (False, (Version(".".join(map(str, stop))), False))]
        elif op in {">=", ">", "<=", "<", "=="}:
            version = Version(value)
            bounds = (
                [(True, (version, True)), (False, (version, True))]
                if op == "=="
                else [(op.startswith(">"), (version, op in {">=", "<="}))]
            )
        else:
            raise ValueError(f"unsupported interval constraint: {spec}")
        for is_lower, bound in bounds:
            current = lower if is_lower else upper
            if current is None or (bound[0] > current[0] if is_lower else bound[0] < current[0]):
                current = bound
            elif bound[0] == current[0]:
                current = (bound[0], bound[1] and current[1])
            if is_lower:
                lower = current
            else:
                upper = current
    if lower and upper and (lower[0] > upper[0] or (lower[0] == upper[0] and not (lower[1] and upper[1]))):
        raise ValueError("empty dependency interval")
    return lower, upper


def _within(actual, expected):
    if actual == expected:
        return True
    low, high = _interval(actual)
    expected_low, expected_high = _interval(expected)
    for bound, required, is_lower in ((low, expected_low, True), (high, expected_high, False)):
        if required is None:
            continue
        if bound is None or (bound[0] < required[0] if is_lower else bound[0] > required[0]):
            return False
        if bound[0] == required[0] and bound[1] and not required[1]:
            return False
    return True


def _recipe_items(text, section):
    # A Jinja recipe is not plain YAML. Accept only this documented list block.
    match = re.search(rf"(?ms)^requirements:\n.*?^  {section}:\n(.*?)(?=^\S|^  \S|\Z)", text)
    if match is None:
        raise ValueError(f"missing requirements.{section}")
    result = []
    for line in match[1].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith("- ") or "{{" in line or re.search(r"#\s*\[", line):
            raise ValueError(f"unsupported recipe entry: {line}")
        result.append(line[2:].split("#", 1)[0].strip())
    if not result:
        raise ValueError(f"empty requirements.{section}")
    return result


def _environment_items(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("dependencies"), list):
        raise ValueError("missing dependencies list")
    items = []
    for item in data["dependencies"]:
        if isinstance(item, str):
            items.append(item)
        elif isinstance(item, dict) and set(item) == {"pip"} and isinstance(item["pip"], list):
            items.extend(item["pip"])
        else:
            raise ValueError(f"unsupported dependency entry: {item!r}")
    if not all(isinstance(item, str) for item in items):
        raise ValueError("dependencies must be strings")
    return items


def _project(root):
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    requirements = _requirements(data["dependencies"])
    if not requirements:
        raise ValueError("empty canonical runtime requirements")
    return requirements, Requirement(f"python{data['requires-python']}")


def audit(root):
    """Return diagnostic strings; malformed or unclassified routes fail closed."""
    root = root.resolve()
    contract = tomllib.loads((root / CONTRACT).read_text(encoding="utf-8"))
    if contract.get("schema") != 1:
        raise ValueError("unsupported dependency inventory schema")
    expected, python = _project(root)
    findings = []

    def check(path, supplied, *, recipe=False):
        try:
            if recipe:
                text = (root / path).read_text(encoding="utf-8")
                actual = _requirements(_recipe_items(text, "run"))
                host = _requirements(_recipe_items(text, "host"))
                if "python" not in host or host["python"].specifier != python.specifier:
                    findings.append(f"{path}: host Python differs from {python}")
                if set(actual) != set(expected) | {"python"}:
                    findings.append(f"{path}: runtime dependency names differ from pyproject.toml")
            else:
                actual = _requirements(_environment_items(root / path))
            for name, requirement in {**expected, "python": python}.items():
                if name in supplied:
                    if name in actual:
                        findings.append(f"{path}: {name} is both installed and source-supplied")
                    continue
                observed = actual.get(name)
                if observed is None:
                    findings.append(f"{path}: missing {requirement}")
                elif (
                    observed.specifier != requirement.specifier
                    if recipe
                    else not _within(observed.specifier, requirement.specifier)
                ):
                    findings.append(f"{path}: {observed} violates {requirement}")
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            findings.append(f"{path}: {exc}")

    recipe = contract["recipe"]
    recipes = {
        str(path.relative_to(root))
        for path in (root / "devtools").rglob("*.yaml")
        if path.name in {"recipe.yaml", "meta.yaml"}
    }
    if recipes != {recipe}:
        findings.append("Conda recipe inventory differs from discovered recipes")
    check(recipe, set(), recipe=True)
    classified = set()
    supplied_by_env = {}
    for entry in contract["environments"]:
        path = entry["path"]
        supplied = {canonicalize_name(name) for name in entry["source_supplied"]}
        if path in classified or not supplied <= set(expected):
            findings.append(f"{path}: duplicate environment or unknown source dependency")
        classified.add(path)
        supplied_by_env[path] = supplied
        check(path, supplied)
    for entry in contract["excluded_environments"]:
        path = entry["path"]
        if path in classified or not entry.get("reason", "").strip():
            findings.append(f"{path}: duplicate or unexplained exclusion")
        # A packaging-only exclusion must not quietly turn into a runtime route.
        names = set(_requirements(_environment_items(root / path)))
        allowed = set(entry.get("runtime_tools", []))
        if not allowed <= set(expected) or names & ((set(expected) | {"molsysviewer"}) - allowed):
            findings.append(f"{path}: excluded environment now installs runtime packages")
        classified.add(path)
    discovered = {str(path.relative_to(root)) for path in (root / "devtools/conda-envs").glob("*.y*ml")}
    if classified != discovered:
        findings.append(f"environment inventory differs: {sorted(classified ^ discovered)}")

    sources = {(item["path"], item["job"], item["package"]): item for item in contract["source_workflows"]}
    if len(sources) != len(contract["source_workflows"]):
        findings.append("duplicate source workflow inventory entry")
    audited_sources = set()
    for path in (root / ".github/workflows").glob("*.y*ml"):
        relative = str(path.relative_to(root))
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job_name, job in data.get("jobs", {}).items():
            steps = job.get("steps", [])
            checkout_prefixes = [
                s.get("with", {}).get("path", "")
                for s in steps
                if str(s.get("uses", "")).startswith("actions/checkout@") and not s.get("with", {}).get("repository")
            ]
            for step in steps:
                with_ = step.get("with", {})
                environment = with_.get("environment-file")
                if environment:
                    for prefix in checkout_prefixes:
                        if prefix and environment.startswith(prefix + "/"):
                            environment = environment[len(prefix) + 1 :]
                    if environment not in classified:
                        findings.append(f"{relative}: unclassified workflow environment {environment}")
                for name in re.findall(r"git\+https://github\.com/[^/]+/([\w.-]+)@", step.get("run", "")):
                    if canonicalize_name(name) in expected:
                        findings.append(f"{relative}: unsupported runtime VCS install route {name}")
                if not str(step.get("uses", "")).startswith("actions/checkout@"):
                    continue
                repository = with_.get("repository", "")
                package = canonicalize_name(repository.rsplit("/", 1)[-1])
                if (
                    not repository
                    or repository == "uibcdf/molsysviewer"
                    or (not repository.startswith("uibcdf/") and package not in expected)
                ):
                    continue
                key = (relative, job_name, package)
                entry = sources.get(key)
                if entry is None or package not in expected or key in audited_sources:
                    findings.append(f"{relative}: unclassified or duplicate source checkout {repository}")
                    continue
                audited_sources.add(key)
                ref = with_.get("ref", "")
                expression = rf"\$\{{\{{ inputs\.{re.escape(entry['input'])} \|\| '[0-9a-f]{{40}}' \}}\}}"
                if not re.fullmatch(expression, ref) or with_.get("path") != entry["checkout_path"]:
                    findings.append(f"{relative}: source requires an exact SHA and declared checkout path")
                checks = [s for s in steps if "--installed-source" in s.get("run", "")]
                if len(checks) != 1 or not any(
                    s.get("env", {}).get("MOLSYSMT_SHA") == ref
                    and "if" not in s
                    and f"{package}=../{entry['checkout_path']}@$MOLSYSMT_SHA" in s["run"]
                    and "audit_dependency_contract.py" in s["run"]
                    for s in checks
                ):
                    findings.append(f"{relative}: missing installed-source identity/floor audit")
                if checks:
                    position = steps.index(checks[0])
                    installs = [i for i, s in enumerate(steps) if "pip install" in s.get("run", "")]
                    consumers = [
                        i
                        for i, s in enumerate(steps)
                        if "pytest" in s.get("run", "") or "validate_installed_rust_extension" in s.get("run", "")
                    ]
                    if not installs or position <= max(installs) or (consumers and position >= min(consumers)):
                        findings.append(f"{relative}: source audit must follow installation and precede consumers")
                if package not in supplied_by_env.get(entry["environment"], set()):
                    findings.append(f"{relative}: source checkout has no matching environment exception")
    if audited_sources != set(sources):
        findings.append("source workflow inventory contains a missing checkout")
    for environment, supplied in supplied_by_env.items():
        providers = {
            entry["package"]
            for key, entry in sources.items()
            if key in audited_sources and entry["environment"] == environment
        }
        if not supplied <= providers:
            findings.append(f"{environment}: source exception lacks an audited provider")
    return findings


def check_installed_source(root, declaration):
    """Verify distribution version, local install origin and checked-out commit."""
    name, sep, identity = declaration.partition("=")
    path_text, marker, sha = identity.rpartition("@")
    if not sep or not marker or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("source declaration must be NAME=PATH@full-commit-SHA")
    name = canonicalize_name(name)
    expected, _ = _project(root)
    if name not in expected:
        raise ValueError(f"{name}: not a declared runtime dependency")
    source = Path(path_text).resolve(strict=True)
    source_project = tomllib.loads((source / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    if canonicalize_name(source_project["name"]) != name:
        raise ValueError(f"{name}: checkout contains a different project")
    head = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if head != sha or dirty:
        raise ValueError(f"{name}: source checkout differs from the exact clean commit")
    distribution = metadata.distribution(name)
    if not expected[name].specifier.contains(Version(distribution.version), prereleases=True):
        raise ValueError(f"{name}: installed {distribution.version} violates {expected[name]}")
    origin = json.loads(distribution.read_text("direct_url.json") or "null")
    if not isinstance(origin, dict) or "dir_info" not in origin:
        raise ValueError(f"{name}: no local source installation provenance")
    url = urlparse(origin.get("url", ""))
    # A file URL with a remote host is not this local checkout.
    if url.scheme != "file" or url.netloc not in {"", "localhost"}:
        raise ValueError(f"{name}: installation is not from the requested local source")
    installed_source = Path(url2pathname(url.path)).resolve()
    if installed_source != source:
        raise ValueError(f"{name}: installed from {installed_source}, expected {source}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--installed-source", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        findings = audit(args.root)
        for declaration in args.installed_source:
            try:
                check_installed_source(args.root, declaration)
            except (OSError, ValueError, subprocess.CalledProcessError, metadata.PackageNotFoundError) as exc:
                findings.append(str(exc))
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        findings = [str(exc)]
    for finding in findings:
        print(f"[DEPENDENCY_CONTRACT] {finding}")
    if findings:
        return 1
    print("Dependency contract verified; installed API compatibility remains a separate gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
