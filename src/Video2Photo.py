"""Compatibility wrapper for lightweight FFmpeg frame extraction."""

from yolo_utils.video import extract_frames


def main(input_video, start=0, timeF=10):
    report = extract_frames(input_video, start, timeF)
    print(f"已提取 {report.extracted_count} 张图片到 {report.output_folder}。")
    return report
