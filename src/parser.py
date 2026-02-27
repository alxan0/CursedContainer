import os

class ModListParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._lines = []
        self._index = 0
        self._load_file()

    def _load_file(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Missing mod list at {self.file_path}")

        with open(self.file_path, "r") as fin:
            for line in fin:
                line = line.strip()
                if line and not line.startswith("#"):
                    self._lines.append(line)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self._index >= len(self._lines):
            raise StopIteration
        
        raw_target = self._lines[self._index]
        self._index += 1

        return self._clean_entry(raw_target)
    
    def _clean_entry(self, entry: str):
        if "curseforge.com" in entry:
            return entry.rstrip('/').split('/')[-1]
        return entry


