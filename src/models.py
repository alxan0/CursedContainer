from dataclasses import dataclass
from enum import Enum, auto

class ModType(Enum):
    MOD = 9137
    PREFAB = auto()
    WORLD = auto()
    BOOTSTRAP = auto()
    TRANSLATION = auto()
    UNKNOWN = -1

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN

@dataclass
class HytaleMod:
    id: int
    name: str
    slug: str
    mod_type: ModType
    filename: str
    current_file_id: int
    sha1_hash: str