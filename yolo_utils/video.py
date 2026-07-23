"""Optional video frame extraction without a heavyweight bundled dependency."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .common import UtilityError


@dataclass(frozen=True)
class VideoReport:
    output_folder: Path
    extracted_count: int
    backend: str


def extract_frames(
    input_video: str | Path,
    start_number: int = 0,
    frame_interval: int = 10,
    output_folder: str | Path | None = None,
) -> VideoReport:
    source = Path(input_video).expanduser().resolve()
    if not source.is_file():
        raise UtilityError(f"视频文件不存在：{source}")
    try:
        start = int(start_number)
        interval = int(frame_interval)
    except (TypeError, ValueError) as error:
        raise UtilityError("起始编号和帧间隔必须是整数。") from error
    if start < 0 or interval <= 0:
        raise UtilityError("起始编号不能为负数，帧间隔必须大于 0。")
    destination = (
        Path(output_folder).expanduser().resolve() if output_folder else source.parent / "images"
    )
    destination.mkdir(parents=True, exist_ok=True)

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise UtilityError(
            "未找到 FFmpeg。请安装 FFmpeg 并加入 PATH；基础程序不再捆绑 OpenCV，"
            "因此启动更快、打包更小。"
        )
    existing = {path.resolve() for path in destination.glob("*.jpg")}
    output_pattern = str(destination / "%05d.jpg")
    command = [
        ffmpeg,
        "-n",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(source),
        "-vf",
        f"select=not(mod(n+1\\,{interval}))",
        "-fps_mode",
        "vfr",
        "-start_number",
        str(start + 1),
        "-q:v",
        "2",
        output_pattern,
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode:
        detail = result.stderr.strip() or "FFmpeg 返回未知错误。"
        raise UtilityError(f"视频抽帧失败：{detail}")
    created = [
        path
        for path in destination.glob("*.jpg")
        if path.resolve() not in existing and path.is_file()
    ]
    return VideoReport(destination, len(created), "ffmpeg")
