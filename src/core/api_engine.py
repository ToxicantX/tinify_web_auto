import os
import time
import tinify
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from .base_engine import BaseEngine, CompressResult


class ApiEngine(BaseEngine):

    def __init__(self, api_key: str = "", concurrency: int = 5):
        self.api_key = api_key
        self.concurrency = concurrency
        if api_key:
            tinify.key = api_key

    def set_key(self, api_key: str):
        self.api_key = api_key
        tinify.key = api_key

    def validate(self) -> tuple[bool, str]:
        if not self.api_key:
            return False, "API Key 未设置"
        try:
            tinify.validate()
            count = tinify.compression_count
            return True, f"API Key 有效 (本月已使用 {count} 次压缩)"
        except tinify.Error as e:
            return False, f"API Key 验证失败: {e}"

    def compress(self, input_path: str, output_path: str) -> CompressResult:
        original_name = os.path.basename(input_path)
        original_size = os.path.getsize(input_path)
        start = time.time()
        try:
            source = tinify.from_file(input_path)
            source.to_file(output_path)
            compressed_size = os.path.getsize(output_path)
            duration_ms = int((time.time() - start) * 1000)
            return CompressResult(
                original_path=input_path,
                original_name=original_name,
                original_size=original_size,
                compressed_size=compressed_size,
                output_path=output_path,
                duration_ms=duration_ms,
                success=True,
            )
        except tinify.Error as e:
            duration_ms = int((time.time() - start) * 1000)
            return CompressResult(
                original_path=input_path,
                original_name=original_name,
                original_size=original_size,
                compressed_size=0,
                output_path=output_path,
                duration_ms=duration_ms,
                success=False,
                error=str(e),
            )

    def compress_batch(self, files: list[str], output_dir: str,
                       progress_callback: Optional[Callable] = None) -> list[CompressResult]:
        results = []
        total = len(files)
        completed = 0

        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = {}
            for f in files:
                name = os.path.basename(f)
                out_path = os.path.join(output_dir, name)
                future = executor.submit(self.compress, f, out_path)
                futures[future] = f

            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, os.path.basename(futures[future]))

        return results
