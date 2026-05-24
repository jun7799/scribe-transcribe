#!/usr/bin/env python3
"""视频号转录工具 — 下载 + 转写一体化 CLI

用法:
  python main.py transcribe <video_path>  对本地视频转写
  python main.py serve                    启动代理，自动下载+转写
  python main.py tasks                    列出已下载的任务
"""

import argparse
import os
import sys
import time

from config import DOWNLOAD_DIR, ensure_dirs, load_cache, save_cache
from audio import extract_audio
from transcriber import transcribe
from exporter import export_all
from downloader import Downloader


def cmd_transcribe(args):
    """对本地视频文件进行转写"""
    video_path = args.video
    if not os.path.exists(video_path):
        print(f"[ERROR] 文件不存在: {video_path}")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(DOWNLOAD_DIR, base_name)
    os.makedirs(output_dir, exist_ok=True)

    # 检查缓存
    cached = load_cache(video_path)
    if cached and not args.force:
        print(f"[INFO] 已有缓存，跳过转写。使用 --force 强制重新转写。")
        print(f"[INFO] 缓存位置: {output_dir}")
        return

    # 步骤1: 提取音频
    print(f"\n[步骤1/2] 提取音频...")
    wav_path = extract_audio(video_path, output_dir)
    print(f"[OK] 音频已提取: {wav_path}")

    # 步骤2: 转写
    print(f"\n[步骤2/2] 转写中...")
    result = transcribe(wav_path, language=args.language)

    # 保存缓存
    save_cache(video_path, result)

    # 导出
    paths = export_all(result, output_dir, base_name)
    print(f"\n[OK] 转写完成!")
    print(f"  SRT: {paths['srt']}")
    print(f"  TXT: {paths['txt']}")

    # 清理临时 WAV
    if not args.keep_wav:
        os.remove(wav_path)
        print(f"  已清理临时音频文件")


def _clean_temp_files(download_dir):
    """清理下载目录中残留的 .temp 文件（下载中断产生的半成品）"""
    if not os.path.exists(download_dir):
        return
    cleaned = 0
    for root, _, files in os.walk(download_dir):
        for f in files:
            if f.endswith(".temp"):
                temp_path = os.path.join(root, f)
                try:
                    size_mb = os.path.getsize(temp_path) / 1024 / 1024
                    os.remove(temp_path)
                    cleaned += 1
                    print(f"[INFO] 清理残留临时文件: {f} ({size_mb:.1f}MB)")
                except OSError as e:
                    print(f"[WARN] 无法删除 {f}: {e}")
    if cleaned:
        print(f"[OK] 共清理 {cleaned} 个残留临时文件\n")


def cmd_serve(args):
    """启动代理服务，自动监控下载并转写"""
    download_dir = args.download_dir or DOWNLOAD_DIR
    ensure_dirs()

    # 启动前清理上次中断残留的 .temp 文件
    _clean_temp_files(download_dir)

    dl = Downloader(download_dir=download_dir)

    if not dl.start():
        sys.exit(1)

    print(f"\n[INFO] 下载目录: {download_dir}")
    print("[INFO] 请在手机微信中打开视频号，代理会自动拦截下载")
    print("[INFO] 下载完成后自动转写。按 Ctrl+C 退出\n")

    poll_interval = args.poll_interval or 5

    try:
        while True:
            new_tasks = dl.poll_new_downloads()
            for task in new_tasks:
                _process_task(task, download_dir)
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("\n[INFO] 收到退出信号")
    finally:
        dl.stop()


def cmd_tasks(args):
    """列出已下载的任务"""
    dl = Downloader()

    # 尝试连接已运行的服务
    if not dl.wait_ready(timeout=2):
        print("[WARN] 代理服务未运行，仅显示本地已转写的文件")
        _list_local_transcripts()
        return

    tasks = dl.list_tasks(status="done")
    if not tasks:
        print("[INFO] 暂无已完成的下载任务")
        return

    print(f"\n已完成的下载任务 ({len(tasks)} 条):\n")
    for t in tasks:
        title = t.get("title") or t.get("filename", "未知")
        size_mb = t.get("size", 0) / 1024 / 1024
        print(f"  - {title} ({size_mb:.1f}MB)")
        print(f"    路径: {t.get('path', '')}")
        print()


def _process_task(task, download_dir):
    """处理单个下载任务：提取音频 → 转写 → 导出"""
    video_path = task.get("path", "")
    title = task.get("title") or task.get("filename", "未知")

    if not video_path or not os.path.exists(video_path):
        print(f"[WARN] 视频文件不存在，跳过: {title}")
        return

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(download_dir, base_name)

    # 检查缓存
    cached = load_cache(video_path)
    if cached:
        print(f"[INFO] 已有缓存，跳过: {title}")
        return

    print(f"\n{'='*50}")
    print(f"[INFO] 处理新视频: {title}")
    print(f"{'='*50}")

    try:
        # 提取音频
        wav_path = extract_audio(video_path, output_dir)

        # 转写
        result = transcribe(wav_path)
        save_cache(video_path, result)

        # 导出
        paths = export_all(result, output_dir, base_name)
        print(f"[OK] 转写完成: {title}")
        print(f"  TXT: {paths['txt']}")

        # 清理临时 WAV
        os.remove(wav_path)

    except Exception as e:
        print(f"[ERROR] 处理失败 {title}: {e}")


def _list_local_transcripts():
    """列出本地已转写的文件"""
    if not os.path.exists(DOWNLOAD_DIR):
        print("[INFO] 下载目录为空")
        return

    found = False
    for name in os.listdir(DOWNLOAD_DIR):
        subdir = os.path.join(DOWNLOAD_DIR, name)
        if not os.path.isdir(subdir):
            continue
        txt_file = os.path.join(subdir, f"{name}.txt")
        if os.path.exists(txt_file):
            found = True
            print(f"  - {name}")

    if not found:
        print("[INFO] 暂无已转写的文件")


def main():
    parser = argparse.ArgumentParser(
        description="视频号转录工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py transcribe video.mp4          转写本地视频
  python main.py transcribe video.mp4 --force  强制重新转写
  python main.py serve                         启动代理+自动转写
  python main.py tasks                         查看已下载任务
        """,
    )
    sub = parser.add_subparsers(dest="command")

    # transcribe
    p_transcribe = sub.add_parser("transcribe", help="转写本地视频文件")
    p_transcribe.add_argument("video", help="视频文件路径")
    p_transcribe.add_argument("--language", default="zh", help="语言 (默认: zh)")
    p_transcribe.add_argument("--force", action="store_true", help="强制重新转写")
    p_transcribe.add_argument("--keep-wav", action="store_true", help="保留中间 WAV 文件")

    # serve
    p_serve = sub.add_parser("serve", help="启动代理，自动下载+转写")
    p_serve.add_argument("--download-dir", help="下载目录")
    p_serve.add_argument("--poll-interval", type=int, default=5, help="轮询间隔秒数 (默认: 5)")

    # tasks
    sub.add_parser("tasks", help="列出已下载的任务")

    args = parser.parse_args()

    if args.command == "transcribe":
        cmd_transcribe(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "tasks":
        cmd_tasks(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
