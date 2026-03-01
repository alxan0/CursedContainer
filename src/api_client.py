import httpx

from models import HytaleMod, ModType

GAME_ID = 70216 # Hytale game id

class CurseClient:
    base_url = "https://api.curseforge.com"

    def __init__(self, api_key: str):
        self.headers={
            "Accept": "application/json", 
            "x-api-key": api_key
            }
    
    def _api_status(self, r: httpx.Response, slug: str = ""):
        match r.status_code:
            case 200:
                pass
            case 400:
                raise ValueError(f"Bad Request (400): The slug '{slug}' is invalid or malformed.")
            case 500:
                raise RuntimeError("Server Error (500): CurseForge API is having internal issues. Try again later.") 
            case _:
                r.raise_for_status()

    async def test_api(self):
        url = f"{self.base_url}/v1/games"
        async with httpx.AsyncClient() as client:
            r = await client.get(url=url, headers=self.headers)
        return r.status_code            
    
    async def get_game_id(self, game_name: str):
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

    async def get_mod_data(self, slug: str):
        url = f"{self.base_url}/v1/mods/search"
        params = {
            "gameId": GAME_ID,
            "slug": slug
            }
        async with httpx.AsyncClient() as client:
            r = await client.get(url=url, headers=self.headers, params=params)
        
        self._api_status(r, slug)           

        raw_mod_data = r.json().get("data", [])[0]

        target_id = raw_mod_data["mainFileId"]
        main_file = next((f for f in raw_mod_data["latestFiles"] if f["id"] == target_id), None)
        if not main_file:
            raise ValueError(f"Critical Error: Mod '{raw_mod_data['name']}' (ID: {raw_mod_data['id']}) "
                             f"is missing the file for mainFileId: {target_id}")
        filename = main_file["fileName"]
        file_hash = next((h["value"] for h in main_file["hashes"] if h["algo"] == 1), None)
        if not file_hash:
            raise ValueError(f"Critical Error: File {target_id} has no SHA-1 hash (algo 1)")

        mod_data = HytaleMod(
            id = raw_mod_data["id"],
            name = raw_mod_data["name"],
            slug = raw_mod_data["slug"],
            mod_type = ModType(raw_mod_data["classId"]),
            filename= filename,
            current_file_id = target_id,
            sha1_hash = file_hash
        )
        
        return mod_data

    async def get_mod_download_url(self, mod_data: HytaleMod):
        url = f"{self.base_url}/v1/mods/{mod_data.id}/files/{mod_data.current_file_id}/download-url"

        async with httpx.AsyncClient() as client:
            r = await client.get(url=url, headers=self.headers)
        
        self._api_status(r)
        return r.json()["data"]
