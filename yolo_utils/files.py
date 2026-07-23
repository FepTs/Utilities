"""Safe file comparison, deletion, and collision-free renaming."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from pathlib import Path

from .common import UtilityError, index_unique_stems, require_directory, visible_files


@dataclass(frozen=True)
class FolderComparison:
    common: tuple[str, ...]
    only_first: tuple[Path, ...]
    only_second: tuple[Path, ...]


def compare_folders(folder1: str | Path, folder2: str | Path) -> FolderComparison:
    first = require_directory(folder1, "文件夹 1")
    second = require_directory(folder2, "文件夹 2")
    first_files = index_unique_stems(visible_files(first), "文件夹 1")
    second_files = index_unique_stems(visible_files(second), "文件夹 2")
    return FolderComparison(
        common=tuple(sorted(first_files.keys() & second_files.keys())),
        only_first=tuple(
            first_files[key] for key in sorted(first_files.keys() - second_files.keys())
        ),
        only_second=tuple(
            second_files[key] for key in sorted(second_files.keys() - first_files.keys())
        ),
    )


def delete_paths(paths: list[Path] | tuple[Path, ...]) -> int:
    """Delete an explicit list of files without following symlinks."""
    targets = [Path(path).expanduser().absolute() for path in paths]
    for path in targets:
        if not path.is_file() and not path.is_symlink():
            raise UtilityError(f"只能删除普通文件：{path}")
    for path in targets:
        path.unlink()
    return len(targets)


def matching_files(input_folder: str | Path, feature: str, extension: str = "") -> tuple[Path, ...]:
    folder = require_directory(input_folder, "输入目录")
    if not feature:
        raise UtilityError("文件名特征不能为空，避免意外匹配目录中的全部文件。")
    normalized_extension = extension.strip()
    if normalized_extension and not normalized_extension.startswith("."):
        normalized_extension = f".{normalized_extension}"
    return tuple(
        path
        for path in visible_files(folder)
        if feature in path.name
        and (not normalized_extension or path.suffix.casefold() == normalized_extension.casefold())
    )


def rename_files(
    input_dir: str | Path, extension: str = "all", start_number: int = 1
) -> list[tuple[str, str]]:
    """Rename deterministically in two phases so existing names cannot collide."""
    folder = require_directory(input_dir, "输入目录")
    try:
        start = int(start_number)
    except (TypeError, ValueError) as error:
        raise UtilityError("起始编号必须是非负整数。") from error
    if start < 0:
        raise UtilityError("起始编号必须是非负整数。")

    normalized = extension.strip().lstrip(".").casefold()
    files = visible_files(folder)
    if normalized not in {"", "all"}:
        files = [path for path in files if path.suffix.lstrip(".").casefold() == normalized]
    if not files:
        raise UtilityError("没有找到符合条件的文件。")

    width = max(5, len(str(start + len(files) - 1)))
    plan: list[tuple[Path, Path]] = []
    selected = {path.resolve() for path in files}
    for index, old_path in enumerate(files, start=start):
        suffix = f".{normalized}" if normalized not in {"", "all"} else old_path.suffix
        new_path = folder / f"{index:0{width}d}{suffix}"
        if new_path.exists() and new_path.resolve() not in selected:
            raise UtilityError(f"目标文件已存在且不在重命名范围内：{new_path.name}")
        plan.append((old_path, new_path))

    token = uuid.uuid4().hex
    temporary: list[tuple[Path, Path, Path]] = []
    try:
        for index, (old_path, new_path) in enumerate(plan):
            temp_path = folder / f".yolo-utils-{token}-{index}.tmp"
            os.replace(old_path, temp_path)
            temporary.append((temp_path, old_path, new_path))
        for temp_path, _, new_path in temporary:
            os.replace(temp_path, new_path)
    except BaseException:
        for temp_path, old_path, new_path in reversed(temporary):
            current = temp_path if temp_path.exists() else new_path
            if current.exists() and not old_path.exists():
                os.replace(current, old_path)
        raise
    return [(old.name, new.name) for old, new in plan if old != new]
