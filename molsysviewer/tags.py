from __future__ import annotations

import re
from collections.abc import Callable, Iterable


class TagsManager:
    """Own one domain's tag allocation policy without duplicating its registry."""

    def __init__(
        self,
        domain: str,
        prefix: str,
        existing_tags: Callable[[], Iterable[str]],
    ) -> None:
        self.domain = str(domain)
        self.prefix = str(prefix)
        self._existing_tags = existing_tags
        self._high_water_mark = 0
        self._generated_pattern = re.compile(rf"^{re.escape(self.prefix)}(\d+)$")

    @property
    def high_water_mark(self) -> int:
        return self._high_water_mark

    def restore(self, high_water_mark: int) -> None:
        """Raise the allocation mark without allowing it to move backwards."""
        self._high_water_mark = max(self._high_water_mark, int(high_water_mark))

    def reset(self) -> None:
        self._high_water_mark = 0

    def observe(self, tag: str) -> str:
        """Record an explicit generated-looking tag for future allocations."""
        text = self._normalize(tag)
        match = self._generated_pattern.fullmatch(text)
        if match is not None:
            self.restore(int(match.group(1)))
        return text

    def validate(self, tag: str, *, current_tag: str | None = None) -> str:
        text = self._normalize(tag)
        if current_tag is not None and text == current_tag:
            return self.observe(text)
        if text in set(self._existing_tags()):
            raise ValueError(f"{self.domain.capitalize()} tag {text!r} already exists.")
        return self.observe(text)

    def allocate(self) -> str:
        existing = set(self._existing_tags())
        while True:
            self._high_water_mark += 1
            tag = f"{self.prefix}{self._high_water_mark}"
            if tag not in existing:
                return tag

    @staticmethod
    def _normalize(tag: str) -> str:
        text = str(tag).strip()
        if not text:
            raise ValueError("Tag must be a non-empty string.")
        return text


__all__ = ["TagsManager"]
