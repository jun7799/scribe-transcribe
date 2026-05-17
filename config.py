import os
import sys
import json

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(BASE_DIR, "bin")
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")

# Go 下载器
WX_DL_EXE = os.path.join(BIN_DIR, "wx-dl.exe")
WX_DL_API = "http://127.0.0.1:2022"

# Whisper 模型（复用已有的 faster-whisper-small）
WHISPER_MODEL = "small"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

# ffmpeg 输出参数
FFMPEG_AUDIO_PARAMS = {
    "ac": "1",          # 单声道
    "ar": "16000",      # 16kHz
    "c:a": "pcm_s16le", # PCM 16bit
}


def ensure_dirs():
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(BIN_DIR, exist_ok=True)


def load_cache(video_path):
    """加载转写缓存"""
    cache_path = _cache_path(video_path)
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cache(video_path, data):
    """保存转写缓存"""
    cache_path = _cache_path(video_path)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _cache_path(video_path):
    base = os.path.splitext(os.path.basename(video_path))[0]
    return os.path.join(DOWNLOAD_DIR, base, f"{base}.transcript.json")
