from dataclasses import dataclass
from typing import Optional, List

@dataclass
class HytaleMod:
    id: int
    name: str
    slug: str
    mod_type: str
    current_file_id: Optional[int] = None
    hash: Optional[str] = None

@dataclass
class CurseFile:
    file_id: int
    display_name: str
    download_url: str
    sha1_hash: str