import os
import sys
import asyncio
from dotenv import load_dotenv
import logging

import models
from api_client import CurseClient
from parser import ModListParser
from sync_engine import SyncEngine
from downloader import Downloader

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s') # TODO create a logger for every module

load_dotenv()

async def check_api_healty(cclient):
    try:
        r = await cclient.test_api()
        if r is None or r != 200:
            print(f"Error: API health check failed with status {r if r else 'unknown'}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: Could not reach API - {e}")
        sys.exit(1)


async def main():
    
    api_key = os.getenv("CURSE_FORGE_API", "")
    base_path = os.getenv("APP_BASE_PATH", "")
    sync_interval = int(os.getenv("SYNC_INTERVAL", "0"))

    modlist_path = os.path.join(base_path, "data/modlist.txt") 
    manifest_path = os.path.join(base_path, "data/manifest.json")
    #print(f"Key loaded: {api_key}")


    if not api_key:
        print("Error: CURSE_FORGE_API environment variable not set.")
        return

    cclient = CurseClient(api_key)
    #await check_api_healty(cclient)
    sengine = SyncEngine(manifest_path, base_path)
    downloader = Downloader()

    while True:
        try:
            sluglist = ModListParser(modlist_path)
        except FileNotFoundError as e:
            print(f"FATAL ERROR: {e}")
            return  

        for slug in sluglist:
            try:
                print(f"Processing: {slug}")
                #print(await cclient.get_game_id("hytale"))
                mod_data = await cclient.get_mod_data(slug)
                folder_path = sengine.prepare_for_download(mod_data)
                if folder_path:
                    download_url = await cclient.get_mod_download_url(mod_data)
                    await downloader.download_mod(mod_data,download_url, folder_path)
                    sengine.update_record(mod_data, mod_data.filename)
            except Exception as e:
                print(f"Skipping {slug} due to error: {e}")
                continue
        
        if sync_interval == 0:
            break

        logging.info(f"Sleeping for {sync_interval} hours...")
        await asyncio.sleep(sync_interval*3600)
        

if __name__ == "__main__":
    asyncio.run(main())