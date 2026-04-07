import os
import json
import logging
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo
from models import HytaleMod, ModType

class SyncEngine:

    def __init__(self, manifest_path: str, base_path: str, timezone: str):
        self.manifest_path = manifest_path
        self.base_path = base_path
        self.data = self._load_file()
        self.tz = ZoneInfo(timezone)

    def _validate_manifest(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise ValueError("Manifest root must be a JSON object.")

        if "mods" not in data:
            data["mods"] = {}

        if not isinstance(data["mods"], dict):
            raise ValueError("Manifest 'mods' must be a JSON object.")

        if "last_sync" not in data:
            data["last_sync"] = None

        return data

    def _load_file(self) -> dict:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as fin:
                    raw = json.load(fin)
                return self._validate_manifest(raw)
            except (json.JSONDecodeError, ValueError) as exc:
                logging.warning(f"Manifest at '{self.manifest_path}' is invalid ({exc}). Resetting.")

        logging.info(f"Missing manifest.json or invalid manifest at {self.manifest_path}")
        return {"last_sync": None, "mods": {}}
    
    def _save(self):
        manifest_dir = os.path.dirname(self.manifest_path) or "."
        os.makedirs(manifest_dir, exist_ok=True)

        fd, tmp_path = tempfile.mkstemp(prefix=".manifest-", suffix=".tmp", dir=manifest_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fout:
                json.dump(self.data, fout, indent=4)
                fout.flush()
                os.fsync(fout.fileno())

            os.replace(tmp_path, self.manifest_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise


    def _get_local_file_id(self, mod_id: int):
        mod_entry = self.data["mods"].get(str(mod_id), {})
        return mod_entry.get("current_file_id", None)
    
    def _should_update(self, remote_mod: HytaleMod):
        local_file_id = self._get_local_file_id(remote_mod.id)
        
        if not local_file_id:
            return True
        if local_file_id != remote_mod.current_file_id:
            return True
        return False
    
    def _get_target_path(self, mod_type: ModType): # TODO add proper ModType handling other then normal mods
        match mod_type:
            case ModType.MOD:
                return os.path.join(self.base_path, "mods")
            case ModType.PREFAB:
                return os.path.join(self.base_path, "mods")
            case ModType.WORLD:
                return os.path.join(self.base_path, "mods")
            case ModType.BOOTSTRAP:
                return os.path.join(self.base_path, "mods")
            case ModType.TRANSLATION:
                return os.path.join(self.base_path, "mods")
            case _:
                raise NotImplementedError(f"ModType {mod_type} is not yet supported")
            
    def prune_orphaned_mods(self, active_mod_ids: list[int]):
        pass

    def prepare_for_download(self, remote_mod: HytaleMod):
        if not self._should_update(remote_mod):
            logging.info(f"Mod already up-to-date: {remote_mod.name}")
            return None
        
        folder_path = self._get_target_path(remote_mod.mod_type)
        old_filename = self.data["mods"].get(str(remote_mod.id), {}).get("file_name", None)
        old_mod_path = os.path.join(folder_path, old_filename) if old_filename else None
        
        return folder_path, old_mod_path

    def finalize_successful_update(self, old_mod_path: str | None, new_filename: str):
        if not old_mod_path:
            return

        if os.path.basename(old_mod_path) == new_filename:
            return

        if os.path.exists(old_mod_path):
            os.remove(old_mod_path)
            logging.info(f"Deleted old version: {old_mod_path}")

    def update_record(self, remote_mod: HytaleMod, filename: str):
        self.data["last_sync"] = datetime.now(self.tz).isoformat()
        self.data["mods"][str(remote_mod.id)] = {
            "name": remote_mod.name,
            "slug": remote_mod.slug,
            "file_name": filename,
            "current_file_id": remote_mod.current_file_id,
            "mod_type": remote_mod.mod_type.value,
            "sha1": remote_mod.sha1_hash
        }
        self._save()