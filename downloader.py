import os
import sys
import time
import signal
import subprocess

import requests

from config import WX_DL_EXE, WX_DL_API


class Downloader:
    """管理 Go 视频号下载器子进程"""

    def __init__(self, download_dir=None, api_base=None):
        self.api_base = api_base or WX_DL_API
        self.download_dir = download_dir
        self.process = None
        self._seen_ids = set()

    def start(self):
        """启动 Go 代理服务"""
        if not os.path.exists(WX_DL_EXE):
            print(f"[ERROR] 找不到下载器: {WX_DL_EXE}")
            print("[INFO] 请先编译 Go 下载器:")
            print("  cd backend/core && go build -o ../../scribe-transcribe/bin/wx-dl.exe .")
            return False

        cmd = [WX_DL_EXE]
        if self.download_dir:
            cmd.extend(["--config", self._write_config()])

        print(f"[INFO] 启动视频号代理服务...")
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            universal_newlines=True,
        )

        # 实时输出 Go 进程日志
        self._log_thread = _stream_output(self.process)

        if not self.wait_ready(timeout=15):
            print("[ERROR] 代理服务启动超时")
            self.stop()
            return False

        print(f"[INFO] 代理服务已就绪: {self.api_base}")
        return True

    def stop(self):
        """停止代理服务"""
        if self.process and self.process.poll() is None:
            print("[INFO] 停止代理服务...")
            self.process.send_signal(signal.CTRL_C_EVENT)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("[INFO] 代理服务已停止")

    def wait_ready(self, timeout=15):
        """等待 API 服务就绪"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                resp = requests.get(f"{self.api_base}/api/status", timeout=2)
                if resp.status_code == 200:
                    return True
            except requests.ConnectionError:
                pass
            time.sleep(0.5)
        return False

    def list_tasks(self, status="done"):
        """获取已完成下载的任务列表

        Args:
            status: 过滤状态 (done/downloading/all)

        Returns:
            list[dict]: 任务列表
        """
        try:
            resp = requests.get(
                f"{self.api_base}/api/task/list",
                params={"status": status, "page": 1, "pageSize": 100},
                timeout=5,
            )
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", {}).get("tasks", [])
            return []
        except requests.RequestException:
            return []

    def poll_new_downloads(self):
        """轮询新完成的下载任务

        Returns:
            list[dict]: 新完成的任务（之前未见过的）
        """
        tasks = self.list_tasks(status="done")
        new_tasks = []
        for t in tasks:
            tid = t.get("id", "")
            if tid and tid not in self._seen_ids:
                self._seen_ids.add(tid)
                new_tasks.append(t)
        return new_tasks

    def _write_config(self):
        """生成临时配置文件"""
        import tempfile
        cfg_path = os.path.join(self.download_dir, "wx-dl-config.yaml")
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(f"download:\n  dir: \"{self.download_dir.replace(os.sep, '/')}\"\n")
        return cfg_path


def _stream_output(process):
    """在后台线程中实时输出子进程日志"""
    import threading

    def _reader():
        for line in process.stdout:
            line = line.rstrip()
            if line:
                print(f"  [wx-dl] {line}")
                sys.stdout.flush()

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    return t
