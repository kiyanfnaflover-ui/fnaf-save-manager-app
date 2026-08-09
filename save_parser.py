import os
import sys

# Game IDs whose save files are RC4-encrypted (Clickteam "INI++" format).
# The value is the plaintext password the game uses to encode its data.
ENCRYPTED_KEYS = {
    "jrs": "RamenovJR2",
}


def rc4_decrypt(data: bytes, key: bytes) -> bytes:
    """RC4 / ARCFOUR stream cipher used by Clickteam INI++ save encryption.

    RC4 is symmetric, so the same routine decrypts and encrypts.
    """
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]
    out = bytearray()
    i = j = 0
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)


class SaveParser:
    # هدرهای اختصاصی بازی‌های کلیک‌تیم
    HEADERS = {
        "fnaf1": "freddy",
        "fnaf2": "freddy2",
        "fnaf3": "freddy3",
        "fnaf4": "fn4",
        "fnaf5": "sl",
        "fnaf6": "fnaf6",
        "ucn": "CN"
    }

    def __init__(self, file_path, game_id):
        self.file_path = str(file_path)
        self.game_id = game_id
        self.header = None
        self.data = {}
        self.encrypted = game_id in ENCRYPTED_KEYS
        self.enc_key = ENCRYPTED_KEYS.get(game_id, "").encode("latin-1")

    def _read_raw(self):
        """Read the on-disk bytes (already decrypted for encrypted saves)."""
        if not os.path.exists(self.file_path):
            return None
        try:
            with open(self.file_path, 'rb') as f:
                raw = f.read()
        except IOError:
            return None
        if self.encrypted:
            return rc4_decrypt(raw, self.enc_key)
        return raw

    def load(self):
        self.data = {}
        raw = self._read_raw()
        if raw is None:
            return

        try:
            content = raw.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = raw.decode('latin-1')
            except UnicodeDecodeError:
                return

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                if self.header is None:
                    self.header = line[1:-1]
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                self.data[key.strip()] = val.strip()

    def get_int(self, key, default=0):
        try:
            return int(self.data.get(key, default))
        except ValueError:
            return default

    def set_int(self, key, value):
        self.data[key] = str(value)

    def save(self):
        # Ensure the parent folder exists before writing
        parent = os.path.dirname(self.file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        header = self.header if self.header is not None else self._fallback_header()
        lines = [f"[{header}]"]
        for key, val in self.data.items():
            lines.append(f"{key}={val}")
        # Clickteam saves use CRLF line endings, matching what the games write.
        text = "\r\n".join(lines) + "\r\n"

        if self.encrypted:
            payload = rc4_decrypt(text.encode('utf-8'), self.enc_key)
            with open(self.file_path, 'wb') as f:
                f.write(payload)
        else:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(text)

    def _fallback_header(self):
        if "CERT" in os.path.basename(self.file_path).upper():
            return "CERT"
        # JR's and other encrypted saves use an empty section header ([]).
        if self.encrypted:
            return ""
        return self.HEADERS.get(self.game_id, self.game_id)