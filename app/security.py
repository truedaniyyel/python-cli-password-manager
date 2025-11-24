import os
import sys
import base64

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
except ImportError:
    print("[!] Error: 'cryptography' is missing. Run 'uv add cryptography'")
    sys.exit(1)

# --- ARGON2 CONFIGURATION ---
MEMORY_COST = 65536
TIME_COST = 4
PARALLELISM = 2

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_LENGTH = 32

class SecurityManager:
    @staticmethod
    def generate_salt():
        """Generates a random salt."""
        return os.urandom(SALT_SIZE)

    @staticmethod
    def derive_key(master_password: str, secret_key: str, salt: bytes) -> bytes:
        """
        Derives a 32-byte AES key using Argon2id.
        """
        kdf = Argon2id(
            salt=salt,
            length=KEY_LENGTH,
            iterations=TIME_COST,
            lanes=PARALLELISM,
            memory_cost=MEMORY_COST,
            ad=None,
            secret=None
        )

        combined = (master_password + secret_key).encode('utf-8')
        return kdf.derive(combined)

    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        """
        Encrypts data using AES-256-GCM.
        Returns: NONCE + CIPHERTEXT
        """
        aesgcm = AESGCM(key)
        nonce = os.urandom(NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext

    @staticmethod
    def decrypt(blob: bytes, key: bytes) -> bytes:
        """
        Decrypts a blob (NONCE + CIPHERTEXT).
        Raises InvalidTag if decryption fails.
        """
        if len(blob) < NONCE_SIZE:
            raise ValueError("Data too short")

        nonce = blob[:NONCE_SIZE]
        ciphertext = blob[NONCE_SIZE:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    @staticmethod
    def encode_b64(data: bytes) -> str:
        return base64.b64encode(data).decode('utf-8')

    @staticmethod
    def decode_b64(data: str) -> bytes:
        return base64.b64decode(data)