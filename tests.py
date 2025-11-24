import unittest
import os
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

# Import your application modules
from security import SecurityManager
from storage import StorageManager
from cryptography.exceptions import InvalidTag


class TestSecurity(unittest.TestCase):
    """
    Tests for the cryptographic functions.
    Ensuring data isn't corrupted during encrypt/decrypt cycles.
    """

    def setUp(self):
        # Common test data
        self.mp = "MySuperSecretPassword"
        self.sk = "1234567890abcdef1234567890abcdef"  # 32 hex chars
        self.salt = SecurityManager.generate_salt()
        self.key = SecurityManager.derive_key(self.mp, self.sk, self.salt)

    def test_key_derivation_consistency(self):
        """Test that the same inputs always produce the same key."""
        key1 = SecurityManager.derive_key(self.mp, self.sk, self.salt)
        key2 = SecurityManager.derive_key(self.mp, self.sk, self.salt)
        self.assertEqual(key1, key2)

    def test_key_derivation_uniqueness(self):
        """Test that changing salt/MP/SK produces different keys."""
        new_salt = SecurityManager.generate_salt()
        key_new_salt = SecurityManager.derive_key(self.mp, self.sk, new_salt)
        self.assertNotEqual(self.key, key_new_salt)

        key_new_mp = SecurityManager.derive_key("DifferentPass", self.sk, self.salt)
        self.assertNotEqual(self.key, key_new_mp)

    def test_encrypt_decrypt_cycle(self):
        """Test that data can be encrypted and successfully decrypted."""
        data = b'{"site": "google.com", "password": "123"}'

        # Encrypt
        encrypted_blob = SecurityManager.encrypt(data, self.key)

        # Decrypt
        decrypted_data = SecurityManager.decrypt(encrypted_blob, self.key)

        self.assertEqual(data, decrypted_data)

    def test_tamper_detection(self):
        """Test that modifying the encrypted blob causes decryption to fail."""
        data = b'Secret Data'
        encrypted_blob = bytearray(SecurityManager.encrypt(data, self.key))

        # Tamper with the last byte of the ciphertext
        encrypted_blob[-1] = encrypted_blob[-1] ^ 0xFF

        with self.assertRaises(InvalidTag):
            SecurityManager.decrypt(bytes(encrypted_blob), self.key)

    def test_b64_helpers(self):
        """Test Base64 encoding/decoding helpers."""
        original = b"\x00\xFF\x10"
        encoded = SecurityManager.encode_b64(original)
        decoded = SecurityManager.decode_b64(encoded)
        self.assertEqual(original, decoded)
        self.assertIsInstance(encoded, str)


class TestStorage(unittest.TestCase):
    """
    Tests database operations.
    Uses a temporary directory to avoid overwriting the real vault.db.
    """

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "vault.db"

        # Patch the DB_FILE in storage.py to point to our temp file
        self.patcher = patch('storage.DB_FILE', self.db_path)
        self.patcher.start()

        # Initialize DB
        self.db = StorageManager()

    def tearDown(self):
        # Close connection and cleanup temp dir
        self.db.close()
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_config_crud(self):
        """Test creating and retrieving config values (salt, validation)."""
        self.db.save_config("test_key", "test_value")
        val = self.db.get_config("test_key")
        self.assertEqual(val, "test_value")

        # Test overwrite
        self.db.save_config("test_key", "new_value")
        val = self.db.get_config("test_key")
        self.assertEqual(val, "new_value")

    def test_secret_lifecycle(self):
        """Test adding, retrieving, updating, and deleting secrets."""
        # 1. Add
        blob = b"encrypted_stuff"
        self.db.add_secret(blob)

        # 2. Retrieve
        rows = self.db.get_all_blobs()
        self.assertEqual(len(rows), 1)
        row_id, data = rows[0]
        self.assertEqual(data, blob)

        # 3. Update
        new_blob = b"updated_encrypted_stuff"
        success = self.db.update_secret(row_id, new_blob)
        self.assertTrue(success)

        # Verify Update
        rows = self.db.get_all_blobs()
        self.assertEqual(rows[0][1], new_blob)

        # 4. Delete
        success = self.db.delete_secret(row_id)
        self.assertTrue(success)

        # Verify Delete
        rows = self.db.get_all_blobs()
        self.assertEqual(len(rows), 0)


if __name__ == '__main__':
    unittest.main()