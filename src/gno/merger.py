"""Smart .gitignore merging logic."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LineType(Enum):
    """Type of line in a .gitignore file."""

    COMMENT = "comment"
    PATTERN = "pattern"
    BLANK = "blank"
    SECTION_HEADER = "section_header"


@dataclass
class GitignoreLine:
    """Represents a single line in a .gitignore file."""

    type: LineType
    content: str
    original: str

    @classmethod
    def parse(cls, line: str) -> "GitignoreLine":
        """Parse a single line into a GitignoreLine."""
        stripped = line.strip()

        if not stripped:
            return cls(LineType.BLANK, "", line)

        if stripped.startswith("#"):
            comment_text = stripped[1:].strip()
            if (
                comment_text
                and " " not in comment_text
                and comment_text[0].isupper()
                and len(comment_text) < 30
            ):
                return cls(LineType.SECTION_HEADER, comment_text, line)
            return cls(LineType.COMMENT, stripped, line)

        return cls(LineType.PATTERN, stripped, line)


def _parse_gitignore(content: str) -> list[GitignoreLine]:
    """Parse a .gitignore file into structured lines."""
    return [GitignoreLine.parse(line) for line in content.splitlines()]


def _extract_patterns(content: str) -> set[str]:
    """Extract all patterns from a .gitignore file."""
    return {
        line.content
        for line in _parse_gitignore(content)
        if line.type == LineType.PATTERN
    }


def merge_gitignores(existing: str, new: str) -> str:
    """Intelligently merge two .gitignore files without duplicates."""
    existing_patterns = _extract_patterns(existing)
    new_lines = _parse_gitignore(new)

    result_lines = [existing.rstrip()]

    new_patterns: list[str] = []
    new_comments: list[str] = []
    current_section_comments: list[str] = []

    for line in new_lines:
        if line.type == LineType.SECTION_HEADER:
            current_section_comments = [line.original]
        elif line.type == LineType.COMMENT:
            current_section_comments.append(line.original)
        elif line.type == LineType.PATTERN:
            if line.content not in existing_patterns:
                if current_section_comments and not new_patterns:
                    new_comments.extend(current_section_comments)
                elif current_section_comments:
                    new_patterns.append("")
                    new_patterns.extend(current_section_comments)
                current_section_comments = []
                new_patterns.append(line.original)
                existing_patterns.add(line.content)
        elif line.type == LineType.BLANK:
            if current_section_comments:
                current_section_comments.append(line.original)

    if new_patterns:
        result_lines.append("")
        result_lines.append("")
        result_lines.append("# Additional patterns added by gno")

        if new_comments:
            result_lines.append("")
            result_lines.extend(new_comments)

        for pattern in new_patterns:
            result_lines.append(pattern)

    return "\n".join(result_lines) + "\n"
