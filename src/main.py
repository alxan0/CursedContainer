import os
import sys
import asyncio
from dotenv import load_dotenv

import models
from api_client import CurseClient
from parser import ModListParser

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
    modlist_path = "data/modlist.txt" # TODO add it to the env file
    #print(f"Key loaded: {api_key}")


    if not api_key:
        print("Error: CURSE_FORGE_API environment variable not set.")
        return

    cclient = CurseClient(api_key)
    #await check_api_healty(cclient)

    try:
        sluglist = ModListParser(modlist_path)
    except FileNotFoundError as e:
        print(f"FATAL ERROR: {e}")
        return

    for slug in sluglist:
        try:
            print(f"Processing: {slug}")
            pass
        except Exception as e:
            print(f"Skipping {slug} due to error: {e}")
            continue
        
    

if __name__ == "__main__":
    # Use asyncio.run to start the event loop
    asyncio.run(main())