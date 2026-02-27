import httpx

class CurseClient:
    BASE_URL = "https://api.curseforge.com"

    def __init__(self, api_key: str):
        self.headers={"Accept": "application/json", "x-api-key": api_key}
    
    async def test_api(self):
        url = f"{self.BASE_URL}/v1/games"
        async with httpx.AsyncClient() as client:
            r = await client.get(url, headers=self.headers)
            return r.status_code            
