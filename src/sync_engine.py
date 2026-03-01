import os
import json
import logging
from datetime import datetime
from models import HytaleMod, ModType

class SyncEngine:

    def __init__(self, manifest_path: str):
        self.manifest_path = manifest_path
        self.data = self._load_file()

    def _load_file(self) -> dict:
        if os.path.exists(self.manifest_path):
            try:
                with open(self.manifest_path, "r") as fin:
                    return json.load(fin)
            except (json.JSONDecodeError, ValueError):
                logging.warning(f"Manifest at '{self.manifest_path}' is empty or invalid. Resetting.")
        
        logging.info(f"Missing manifest.json or manifest.json is empty at {self.manifest_path}")
        return {"last_sync": None, "mods": {}}
    
    def _save(self):
        with open(self.manifest_path, "w") as fout:
            json.dump(self.data, fout, indent=4)


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
                return "mods"
            case ModType.PREFAB:
                return "mods"
            case ModType.WORLD:
                return "mods"
            case ModType.BOOTSTRAP:
                return "mods"
            case ModType.TRANSLATION:
                return "mods"
            case _:
                raise NotImplementedError(f"ModType {mod_type} is not yet supported")
            
    def _delete_file(self, old_mod_path: str):
        if os.path.exists(old_mod_path):
            os.remove(old_mod_path)
            logging.info(f"Deleted old version: {old_mod_path}")

    def prune_orphaned_mods(self, active_mod_ids: list[int]):
        pass

    def prepare_for_download(self, remote_mod: HytaleMod):
        if not self._should_update(remote_mod):
            logging.info(f"Mod already up-to-date: {remote_mod.name}")
            return None
        
        folder_path = self._get_target_path(remote_mod.mod_type)
        old_filename = self.data["mods"].get(str(remote_mod.id), {}).get("file_name", None)
        
        if old_filename:
            old_mod_path = os.path.join(folder_path, old_filename)
            self._delete_file(old_mod_path)
        
        return folder_path

    def update_record(self, remote_mod: HytaleMod, filename: str):
        self.data["last_sync"] = datetime.now().isoformat()
        self.data["mods"][str(remote_mod.id)] = {
            "name": remote_mod.name,
            "slug": remote_mod.slug,
            "file_name": filename,
            "current_file_id": remote_mod.current_file_id,
            "mod_type": remote_mod.mod_type.value,
            "sha1": remote_mod.sha1_hash
        }
        self._save()