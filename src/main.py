import asyncio
import logging
import os
import sys
import signal
from dataclasses import dataclass

from api_client import CurseClient
from config import Settings, get_settings
from downloader import Downloader
from parser import ModListParser
from sync_engine import SyncEngine

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@dataclass
class AppContext:
    settings: Settings
    cclient: CurseClient
    sengine: SyncEngine
    downloader: Downloader
    modlist_path: str
    manifest_path: str


async def check_api_healthy(cclient: CurseClient) -> None:
    try:
        await cclient.test_api()
        logging.info("API health check passed.")
    except Exception as exc:
        logging.error(f"Could not reach API: {exc}")
        sys.exit(1)

def bootstrap() -> AppContext:
    settings = get_settings()

    base_path = str(settings.app_base_path)
    modlist_path = os.path.join(base_path, "data/modlist.txt")
    manifest_path = os.path.join(base_path, "data/manifest.json")

    cclient = CurseClient(settings.curse_forge_api, settings.download_timeout_seconds, settings.connect_timeout_seconds)
    sengine = SyncEngine(manifest_path, base_path, settings.timezone)
    downloader = Downloader(settings.max_mod_file_size_bytes, settings.download_timeout_seconds, settings.connect_timeout_seconds)

    return AppContext(
        settings=settings,
        cclient=cclient,
        sengine=sengine,
        downloader=downloader,
        modlist_path=modlist_path,
        manifest_path=manifest_path,
    )


async def run_sync_loop(ctx: AppContext, shutdown_event: asyncio.Event) -> None:
    try:
        while not shutdown_event.is_set():
            try:
                sluglist = ModListParser(ctx.modlist_path)
            except FileNotFoundError as exc:
                logging.error(f"Fatal error: {exc}")
                return

            for slug in sluglist:
                try:
                    logging.info(f"Processing: {slug}")
                    mod_data = await ctx.cclient.get_mod_data(slug)
                    download_plan = ctx.sengine.prepare_for_download(mod_data)
                    if download_plan:
                        folder_path, old_mod_path = download_plan
                        download_url = await ctx.cclient.get_mod_download_url(mod_data)
                        await ctx.downloader.download_mod(mod_data, download_url, folder_path)
                        ctx.sengine.update_record(mod_data, mod_data.filename)
                        ctx.sengine.finalize_successful_update(old_mod_path, mod_data.filename)
                except Exception as exc:
                    logging.error(f"Skipping {slug} due to error: {exc}")
                    continue

            if ctx.settings.sync_interval == 0:
                break

            sleep_seconds = ctx.settings.sync_interval * 3600
            logging.info(f"Sleeping for {ctx.settings.sync_interval} hours...")
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=sleep_seconds)
            except asyncio.TimeoutError:
                pass
    except asyncio.CancelledError:
        logging.info("Shutdown requested.")
        return

async def main() -> None:
    try:
        ctx = bootstrap()
    except Exception as exc:
        logging.error(f"Invalid startup configuration: {exc}")
        return

    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_event.set)

    await check_api_healthy(ctx.cclient)
    await run_sync_loop(ctx, shutdown_event)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutdown requested.")