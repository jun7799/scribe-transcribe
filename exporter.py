import os


def format_srt_time(seconds):
    """秒数 → SRT 时间格式 HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def export_srt(segments, output_path):
    """导出 SRT 字幕文件"""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = format_srt_time(seg["start"])
        end = format_srt_time(seg["end"])
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(seg["text"])
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path


def export_txt(full_text, output_path):
    """导出纯文本文件"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    return output_path


def export_all(result, output_dir, base_name):
    """导出所有格式

    Args:
        result: transcriber.transcribe() 返回的结果
        output_dir: 输出目录
        base_name: 文件名（不含扩展名）

    Returns:
        dict: {srt: path, txt: path}
    """
    os.makedirs(output_dir, exist_ok=True)

    srt_path = os.path.join(output_dir, f"{base_name}.srt")
    txt_path = os.path.join(output_dir, f"{base_name}.txt")

    export_srt(result["segments"], srt_path)
    export_txt(result["full_text"], txt_path)

    return {"srt": srt_path, "txt": txt_path}
