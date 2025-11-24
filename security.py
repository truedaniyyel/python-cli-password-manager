import os
import sys
import base64

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError:
    print("[!] Error: 'cryptography' is missing. Run 'uv add cryptography'")
    sys.exit(1)

# Constants
KDF_ITERATIONS = 600000
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_LENGTH = 32

class SecurityManager:
    @staticmethod
    def generate_salt():
        """Generates a random salt for KDF."""
        return os.urandom(SALT_SIZE)

    @staticmethod
    def derive_key(master_password: str, secret_key: str, salt: bytes) -> bytes:
        """
        Derives a 32-byte AES key using PBKDF2-HMAC-SHA256.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=KEY_LENGTH,
            salt=salt,
            iterations=KDF_ITERATIONS,
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