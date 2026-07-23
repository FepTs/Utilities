"""Shared validation and safe file-writing helpers."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterable

IMAGE_SUFFIXES = frozenset({".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"})


class UtilityError(ValueError):
    """A user-facing error caused by invalid input or unsafe state."""


def require_directory(path: os.PathLike[str] | str, label: str) -> Path:
    result = Path(path).expanduser().resolve()
    if not result.is_dir():
        raise UtilityError(f"{label}不是有效文件夹：{result}")
    return result


def ensure_distinct_paths(source: Path, destination: Path) -> None:
    source = source.resolve()
    destination = destination.resolve()
    if source == destination:
        raise UtilityError("输入目录和输出目录不能相同。")
    if source in destination.parents:
        raise UtilityError("输出目录不能位于输入目录内部。")
    if destination in source.parents:
        raise UtilityError("输入目录不能位于输出目录内部。")


def visible_files(folder: Path, suffixes: Iterable[str] | None = None) -> list[Path]:
    allowed = {suffix.lower() for suffix in suffixes} if suffixes else None
    return sorted(
        (
            item
            for item in folder.iterdir()
            if item.is_file()
            and not item.name.startswith(".")
            and (allowed is None or item.suffix.lower() in allowed)
        ),
        key=lambda item: (item.name.casefold(), item.name),
    )


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Replace a text file atomically without leaving a truncated file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding=encoding, newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def index_unique_stems(files: Iterable[Path], label: str) -> dict[str, Path]:
    """Index files by case-insensitive stem and reject ambiguous duplicates."""
    result: dict[str, Path] = {}
    for path in files:
        key = path.stem.casefold()
        if key in result:
            raise UtilityError(
                f"{label}中存在同名但不同后缀的文件：{result[key].name}、{path.name}"
            )
        result[key] = path
    return result
