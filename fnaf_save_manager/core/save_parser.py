import os

class SaveParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.header = ""
        self.data = {}

    def load(self):
        self.data.clear()
        if not os.path.exists(self.file_path):
            return False
            
        with open(self.file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line: continue
            
            if line.startswith('[') and line.endswith(']'):
                self.header = line
            elif '=' in line:
                key, value = line.split('=', 1)
                self.data[key.strip()] = value.strip()
        return True

    def save(self):
        with open(self.file_path, 'w', encoding='utf-8') as f:
            if self.header:
                f.write(f"{self.header}\n")
            for key, value in self.data.items():
                f.write(f"{key}={value}\n")

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self.data.get(key, default))
        except ValueError:
            return default

    def set_int(self, key: str, value: int):
        self.data[key] = str(value)