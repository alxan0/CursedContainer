import logging
import os
import httpx
import hashlib
from models import HytaleMod

class HashMismatchError(Exception):
    pass

class Downloader:

    def __init__(self):
        pass
    
    async def download_mod(self, mod_data: HytaleMod, download_url: str, folder_path: str):
        if not folder_path:
            return
        
        os.makedirs(folder_path, exist_ok=True)
        download_path = os.path.join(folder_path, mod_data.filename)
        
        sha1_hash = hashlib.sha1() 

        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url=download_url, follow_redirects=True) as r:
                r.raise_for_status()

                with open(download_path, "wb") as fout:
                    async for chunk in r.aiter_bytes(chunk_size=8192):
                        fout.write(chunk)
                        sha1_hash.update(chunk)


        
        if sha1_hash.hexdigest().lower() != mod_data.sha1_hash.lower():
            os.remove(download_path)
            logging.error("HASH MISMATCH! Deleting corrupted file.")
            raise HashMismatchError(
                    f"Verification failed for {mod_data.name}. "
                    f"Expected: {mod_data.sha1_hash.lower()}, Got: {sha1_hash.hexdigest().lower()}"
                    )


