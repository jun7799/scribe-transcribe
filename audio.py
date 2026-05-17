import os
import subprocess
import shutil


def extract_audio(input_path, output_dir=None):
    """从视频中提取 16kHz 单声道 WAV 音频

    Args:
        input_path: 输入视频/音频文件路径
        output_dir: 输出目录，默认与输入同目录

    Returns:
        wav 文件路径
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("找不到 ffmpeg，请先安装并加入 PATH")

    base = os.path.splitext(os.path.basename(input_path))[0]
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(input_path))

    wav_path = os.path.join(output_dir, f"{base}.wav")

    cmd = [
        ffmpeg,
        "-y", "-hide_banner", "-loglevel", "error",
        "-i", input_path,
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        wav_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 失败: {result.stderr}")

    if not os.path.exists(wav_path):
        raise RuntimeError(f"ffmpeg 未生成输出文件: {wav_path}")

    return wav_path
