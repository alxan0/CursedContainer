import httpx
import asyncio
import logging

from models import HytaleMod, ModType

class ApiServerError(Exception):
    pass

class ApiResponseError(Exception):
    pass

class ModNotFoundError(Exception):
    pass

GAME_ID = 70216 # Hytale game id

class CurseClient:
    base_url = "https://api.curseforge.com"

    def __init__(
            self, 
            api_key: str,
            download_timeout_seconds: float, 
            connect_timeout_seconds: float,
            max_retries: int = 3,
            retry_backoff_seconds: float = 1.5,
            ):
        self.headers={
            "Accept": "application/json", 
            "x-api-key": api_key
            }
        self.timeout = httpx.Timeout(
            connect=connect_timeout_seconds,
            read=download_timeout_seconds,
            write=download_timeout_seconds,
            pool=10.0,
            )
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
    
    def _api_status(self, r: httpx.Response, slug: str = "") -> None:
        match r.status_code:
            case 200:
                return
            case 400:
                raise ValueError(f"Bad Request (400): The slug '{slug}' is invalid or malformed.")
            case 404:
                raise ModNotFoundError(f"Not Found (404): slug '{slug}' does not exist.")
            case 500:
                raise ApiServerError("Server Error (500): CurseForge API is having internal issues. Try again later.") 
            case _:
                r.raise_for_status()

    async def _get_json(self, url: str, params: dict | None = None, slug: str = "") -> dict:
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    r = await client.get(url=url, headers=self.headers, params=params)

                self._api_status(r, slug)

                payload = r.json()
                if not isinstance(payload, dict):
                    raise ApiResponseError("Invalid API response: expected JSON object.")
                return payload

            except (httpx.TimeoutException, httpx.NetworkError, ApiServerError) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
                wait_seconds = self.retry_backoff_seconds * (2 ** (attempt - 1))
                logging.warning(f"Retry {attempt}/{self.max_retries} after {wait_seconds:.1f}s: {exc}")
                await asyncio.sleep(wait_seconds)

        raise RuntimeError(f"API request failed after {self.max_retries} attempts: {last_error}")

    async def test_api(self) -> None:
        url = f"{self.base_url}/v1/games"
        payload = await self._get_json(url=url)
        data = payload.get("data")
        if not isinstance(data, list):
            raise ApiResponseError("Health check failed: unexpected /v1/games payload shape.")
    
    async def get_game_id(self, game_name: str): # TODO optimise it to use _get_json
        url = f"{self.base_url}/v1/games"
        async with httpx.AsyncClient() as client:
            r = await client.get(url=url, headers=self.headers)
        if r.status_code == 200:
            games = r.json().get('data', [])
            for game in games:
                if game["name"].lower() == game_name:
                    return game["id"]
            return "Hytale not found in the game list."
        else:
            return r.status_code

    async def get_mod_data(self, slug: str) -> HytaleMod:
        url = f"{self.base_url}/v1/mods/search"
        params = {
            "gameId": GAME_ID,
            "slug": slug,
        }

        payload = await self._get_json(url=url, params=params, slug=slug)
        data = payload.get("data")

        if not isinstance(data, list) or not data:
            raise ModNotFoundError(f"No mod found for slug '{slug}'.")

        raw_mod_data = data[0]

        latest_files = raw_mod_data.get("latestFiles", [])
        target_id = raw_mod_data.get("mainFileId")
        if target_id is None:
            raise ApiResponseError(f"Mod '{slug}' missing mainFileId.")

        main_file = next((f for f in latest_files if f.get("id") == target_id), None)
        if not main_file:
            raise ApiResponseError(f"Mod '{slug}' main file id {target_id} not found in latestFiles.")

        filename = main_file.get("fileName")
        if not filename:
            raise ApiResponseError(f"Mod '{slug}' main file missing fileName.")

        hashes = main_file.get("hashes", [])
        file_hash = next((h.get("value") for h in hashes if h.get("algo") == 1 and h.get("value")), None)
        if not file_hash:
            raise ApiResponseError(f"Mod '{slug}' file {target_id} has no SHA-1 hash.")

        return HytaleMod(
            id=raw_mod_data["id"],
            name=raw_mod_data["name"],
            slug=raw_mod_data["slug"],
            mod_type=ModType(raw_mod_data["classId"]),
            filename=filename,
            current_file_id=target_id,
            sha1_hash=file_hash,
        )

    async def get_mod_download_url(self, mod_data: HytaleMod) -> str:
        url = f"{self.base_url}/v1/mods/{mod_data.id}/files/{mod_data.current_file_id}/download-url"
        payload = await self._get_json(url=url)

        download_url = payload.get("data")
        if not isinstance(download_url, str) or not download_url:
            raise ApiResponseError(f"Download URL missing/invalid for mod {mod_data.id}, file {mod_data.current_file_id}.")
        return download_url
