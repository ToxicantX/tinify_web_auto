import os
import time
from typing import Callable, Optional

import requests
from DrissionPage import ChromiumPage, ChromiumOptions

from .base_engine import BaseEngine, CompressResult


class WebEngine(BaseEngine):

    UPLOAD_URL = "https://tinypng.com/"
    MAX_FILE_SIZE = 5 * 1024 * 1024
    BATCH_SIZE = 20

    def __init__(self, browser_path: str = ""):
        self.browser_path = browser_path
        self._page: Optional[ChromiumPage] = None

    def _get_page(self) -> ChromiumPage:
        if self._page is not None:
            try:
                self._page.url
                return self._page
            except Exception:
                self._page = None

        co = ChromiumOptions()
        co.set_argument("--window-size=900,700")
        co.set_argument("--disable-extensions")
        if self.browser_path:
            co.set_browser_path(self.browser_path)

        self._page = ChromiumPage(co)
        self._page.get(self.UPLOAD_URL)
        return self._page

    def validate(self) -> tuple[bool, str]:
        try:
            page = self._get_page()
            zone = page.ele("#upload-dropbox-zone", timeout=8)
            if zone:
                return True, "网页模式就绪"
            return False, "无法访问 TinyPNG 网页"
        except Exception as e:
            return False, f"网页模式初始化失败: {e}"

    def compress(self, input_path: str, output_path: str) -> CompressResult:
        results = self.compress_batch([input_path], os.path.dirname(output_path))
        result = results[0]
        default_out = os.path.join(os.path.dirname(output_path), os.path.basename(input_path))
        if result.success and output_path != default_out and os.path.exists(default_out):
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(default_out, output_path)
            result.output_path = output_path
        return result

    def compress_batch(self, files: list[str], output_dir: str,
                       progress_callback: Optional[Callable] = None) -> list[CompressResult]:
        """Batch compress with real-time progress at each stage."""
        results = []
        total = len(files)
        completed = 0
        os.makedirs(output_dir, exist_ok=True)

        for batch_start in range(0, total, self.BATCH_SIZE):
            batch = files[batch_start:batch_start + self.BATCH_SIZE]

            # Wrap callback to map batch-local indices to overall progress
            def batch_cb(local_completed, local_total, name):
                overall = batch_start + local_completed
                if progress_callback:
                    progress_callback(overall, total, name)

            batch_results = self._process_batch(batch, output_dir, batch_cb)
            results.extend(batch_results)
            completed = batch_start + len(batch_results)

        return results

    # ── Batch processing ──────────────────────────────────────────────

    def _process_batch(self, files: list[str], output_dir: str,
                       progress_callback: Optional[Callable] = None) -> list[CompressResult]:
        """Upload batch, wait with progress, download with progress."""
        start = time.time()
        batch_total = len(files)
        results = []

        try:
            page = self._get_page()
            page.get(self.UPLOAD_URL)
            page.wait(3)

            file_input = self._find_file_input(page)
            if not file_input:
                return [self._fail_result(f, "找不到上传控件") for f in files]

            # Notify: uploading
            if progress_callback:
                progress_callback(0, batch_total, "[上传中...]")

            file_input.input(files)

            # Wait for compression with live progress
            download_map = self._wait_for_batch_results(
                page, files, progress_callback, batch_total
            )

            # Download each file with live progress
            downloaded = 0
            for input_path in files:
                name = os.path.basename(input_path)
                out_path = os.path.join(output_dir, name)
                original_size = os.path.getsize(input_path)

                if progress_callback:
                    progress_callback(downloaded, batch_total, f"[下载中] {name}")

                if name in download_map:
                    try:
                        self._http_download(page, download_map[name], out_path)
                        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                            compressed_size = os.path.getsize(out_path)
                            duration_ms = int((time.time() - start) * 1000)
                            results.append(CompressResult(
                                original_path=input_path, original_name=name,
                                original_size=original_size, compressed_size=compressed_size,
                                output_path=out_path, duration_ms=duration_ms, success=True,
                            ))
                            downloaded += 1
                            if progress_callback:
                                progress_callback(downloaded, batch_total, name)
                            continue
                    except Exception:
                        pass

                results.append(CompressResult(
                    original_path=input_path, original_name=name,
                    original_size=original_size, compressed_size=0,
                    output_path=out_path, duration_ms=int((time.time() - start) * 1000),
                    success=False, error="下载失败",
                ))
                downloaded += 1
                if progress_callback:
                    progress_callback(downloaded, batch_total, f"[失败] {name}")

            return results

        except Exception as e:
            return [self._fail_result(f, str(e)) for f in files]

    def _fail_result(self, path: str, error: str) -> CompressResult:
        name = os.path.basename(path)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        return CompressResult(
            original_path=path, original_name=name,
            original_size=size, compressed_size=0,
            output_path="", duration_ms=0, success=False, error=error,
        )

    # ── Page interaction helpers ──────────────────────────────────────

    def _find_file_input(self, page: ChromiumPage):
        for inp in page.eles("tag:input"):
            if inp.attr("type") == "file":
                return inp
        return None

    def _wait_for_batch_results(self, page: ChromiumPage, files: list[str],
                                 progress_callback: Optional[Callable],
                                 batch_total: int, timeout: int = 180) -> dict[str, str]:
        """Wait until all files have download links. Reports status text updates."""
        file_names = {os.path.basename(f) for f in files}
        last_matched = 0

        waited = 0
        while waited < timeout:
            url_map = self._collect_download_urls(page)
            matched = {}
            for name in file_names:
                for url in url_map:
                    if url.endswith("/" + name) or ("/" + name) in url:
                        matched[name] = url
                        break

            current = len(matched)
            if current > last_matched and progress_callback:
                # Keep bar at 0, only update status text during compression
                progress_callback(0, batch_total, f"[压缩中 {current}/{batch_total}]")
                last_matched = current

            if current >= len(files):
                return matched

            time.sleep(2)
            waited += 2

        return self._collect_download_urls_by_name(page, file_names)

    def _collect_download_urls(self, page: ChromiumPage) -> list[str]:
        urls = []
        for link in page.eles("tag:a"):
            try:
                href = link.attr("href") or ""
                if "backend/opt/download" in href:
                    if not href.startswith("http"):
                        href = "https://tinypng.com" + href
                    urls.append(href)
            except Exception:
                continue
        return urls

    def _collect_download_urls_by_name(self, page: ChromiumPage,
                                        names: set[str]) -> dict[str, str]:
        result = {}
        for link in page.eles("tag:a"):
            try:
                href = link.attr("href") or ""
                if "backend/opt/download" in href:
                    if not href.startswith("http"):
                        href = "https://tinypng.com" + href
                    for name in names:
                        if href.endswith("/" + name) or ("/" + name) in href:
                            result[name] = href
                            break
            except Exception:
                continue
        return result

    def _http_download(self, page: ChromiumPage, url: str, output_path: str):
        cookies_dict = {}
        try:
            for cookie in page.get_cookies():
                cookies_dict[cookie["name"]] = cookie["value"]
        except Exception:
            pass

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://tinypng.com/",
        }

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        resp = requests.get(url, headers=headers, cookies=cookies_dict, timeout=30)
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(resp.content)

    def __del__(self):
        if self._page is not None:
            try:
                self._page.quit()
            except Exception:
                pass
