import logging
import os
import hashlib
import tempfile
from urllib.parse import urlparse

import httpx

from models import HytaleMod

class HashMismatchError(Exception):
    pass

class UnsafeDownloadUrlError(Exception):
    pass

class UnsafePathError(Exception):
    pass

class DownloadTooLargeError(Exception):
    pass

class Downloader:

    ALLOWED_HOST_SUFFIXES = (
        "forgecdn.net",
        "curseforge.com",
    )

    def __init__(
            self, 
            max_mod_file_size_bytes: int, 
            download_timeout_seconds: float, 
            connect_timeout_seconds: float
            ):
        self.max_file_size_bytes = max_mod_file_size_bytes

        self.request_timeout = httpx.Timeout(
            connect=connect_timeout_seconds,
            read=download_timeout_seconds,
            write=download_timeout_seconds,
            pool=10,
        )
    
    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        if not filename:
            raise ValueError("Empty filename.")

        cleaned = filename.replace("\x00", "").replace("\\", "/")
        safe_name = os.path.basename(cleaned)

        if safe_name in ("", ".", ".."):
            raise ValueError(f"Unsafe filename: {filename}")

        if len(safe_name) > 255:
            raise ValueError(f"Filename too long: {safe_name}")

        return safe_name

    @classmethod
    def _validate_download_url(cls, download_url: str) -> None:
        parsed = urlparse(download_url)

        if parsed.scheme.lower() != "https":
            raise UnsafeDownloadUrlError("Download URL must use HTTPS.")

        host = (parsed.hostname or "").lower()
        if not host:
            raise UnsafeDownloadUrlError("Download URL is missing a hostname.")

        trusted = any(
            host == suffix or host.endswith(f".{suffix}")
            for suffix in cls.ALLOWED_HOST_SUFFIXES
        )
        if not trusted:
            raise UnsafeDownloadUrlError(f"Untrusted download host: {host}")

    @staticmethod
    def _resolve_safe_path(base_dir: str, file_name: str) -> str:
        base_real = os.path.realpath(base_dir)
        target_real = os.path.realpath(os.path.join(base_real, file_name))

        if os.path.commonpath([base_real, target_real]) != base_real:
            raise UnsafePathError(f"Path escapes base directory: {target_real}")

        return target_real


    async def download_mod(self, mod_data: HytaleMod, download_url: str, folder_path: str):
        if not folder_path:
            return
        
        self._validate_download_url(download_url)
        safe_filename = self._sanitize_filename(mod_data.filename)

        os.makedirs(folder_path, mode=0o755, exist_ok=True)
        final_path = self._resolve_safe_path(folder_path, safe_filename)
        
        fd, temp_path = tempfile.mkstemp(prefix=".part-", dir=os.path.realpath(folder_path))
        os.close(fd)

        sha1_hash = hashlib.sha1() 
        bytes_downloaded = 0

        try:
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                async with client.stream("GET", url=download_url, follow_redirects=True) as response:
                    response.raise_for_status()

                    content_length = response.headers.get("content-length")
                    if content_length:
                        try:
                            expected_size = int(content_length)
                        except ValueError as exc:
                            raise DownloadTooLargeError("Invalid Content-Length header.") from exc

                        if expected_size > self.max_file_size_bytes:
                            raise DownloadTooLargeError(
                                f"File too large: {expected_size} > {self.max_file_size_bytes} bytes."
                            )

                    with open(temp_path, "wb") as fout:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            bytes_downloaded += len(chunk)
                            if bytes_downloaded > self.max_file_size_bytes:
                                raise DownloadTooLargeError(
                                    f"Download exceeded {self.max_file_size_bytes} bytes."
                                )

                            fout.write(chunk)
                            sha1_hash.update(chunk)

            if sha1_hash.hexdigest().lower() != mod_data.sha1_hash.lower():
                raise HashMismatchError(
                    f"Verification failed for {mod_data.name}. "
                    f"Expected: {mod_data.sha1_hash.lower()}, Got: {sha1_hash.hexdigest().lower()}"
                )

            os.replace(temp_path, final_path)
            logging.info(f"Downloaded and verified: {mod_data.name} -> {final_path}")

        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise


