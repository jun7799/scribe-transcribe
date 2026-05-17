import os
import re
import sys
import json

from faster_whisper import WhisperModel

from config import WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE


# ── 幻觉清理（移植自原项目 postprocess.go） ──────────────────────

HALLUCINATION_PATTERNS = [
    # (字幕:xxx) / (字幕：xxx) / 全角括号
    re.compile(r"^[\s]*[（(][\s]*字幕[\s]*[:：][^)）]*[）)][\s]*$"),
    re.compile(r"^[\s]*[（(][\s]*翻译[\s]*[:：][^)）]*[）)][\s]*$"),
    # 字幕组：xxx / 字幕:xxx
    re.compile(r"^[\s]*字幕(组)?[\s]*[:：]"),
    # English subtitle credits
    re.compile(r"(?i)^[\s]*(subtitles?\s+(by|provided\s+by|from)|transcribed\s+by|translated\s+by|subs?\s+by|captions?\s+by|closed\s+captions?)"),
    re.compile(r"(?i)^[\s]*transcribed\s+by\s+whisper\.?[\s]*$"),
    # [music] [applause] 等环境标记
    re.compile(r"^[\s]*\[[\s]*(music|applause|silence|background\s+music|no\s+audio|inaudible)[\s]*\][\s]*$"),
    re.compile(r"^[\s]*[【［\[][\s]*(音乐|掌声|寂静|静音|无音频|背景音乐)[\s]*[】］\]][\s]*$"),
    # 通用结束语
    re.compile(r"^[\s]*(谢谢观看|感谢观看|谢谢大家的?观看|感谢大家的?观看|多谢观看|请订阅|记得订阅|thanks\s+for\s+watching)[\s!！。.]*$"),
]

TAIL_WINDOW = 4


def _is_hallucination(text):
    text = text.strip()
    if not text:
        return True
    for pat in HALLUCINATION_PATTERNS:
        if pat.search(text):
            return True
    return False


def strip_hallucinations(segments):
    """清理尾部幻觉段落"""
    if not segments:
        return segments

    cutoff = len(segments)
    lowest = max(0, cutoff - TAIL_WINDOW)

    for i in range(cutoff - 1, lowest - 1, -1):
        if not _is_hallucination(segments[i]["text"]):
            break
        cutoff = i

    return segments[:cutoff]


# ── 转写核心 ──────────────────────────────────────────────────

_model = None


def _get_model():
    global _model
    if _model is None:
        print(f"[INFO] 加载 Whisper 模型: {WHISPER_MODEL} ...")
        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )
        print(f"[INFO] 模型加载完成")
    return _model


def transcribe(audio_path, language="zh"):
    """转写音频文件

    Args:
        audio_path: WAV 文件路径
        language: 语言代码，默认 "zh"

    Returns:
        dict: {segments: [{start, end, text}], full_text, duration, language}
    """
    model = _get_model()

    print(f"[INFO] 开始转写: {os.path.basename(audio_path)}")
    segments_iter, info = model.transcribe(
        audio_path,
        language=language,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    segments = []
    for seg in segments_iter:
        segments.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
        })
        # 实时进度
        sys.stdout.write(f"\r[INFO] 转写进度: {seg.end:.1f}s")
        sys.stdout.flush()

    print()  # 换行

    # 清理幻觉
    segments = strip_hallucinations(segments)

    full_text = "\n".join(s["text"] for s in segments)
    duration = segments[-1]["end"] if segments else 0

    return {
        "segments": segments,
        "full_text": full_text,
        "duration": round(duration, 3),
        "language": info.language,
    }
