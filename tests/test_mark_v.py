from __future__ import annotations

"""Unit and validation tests for J.A.R.V.I.S. Mark V core architecture."""

import concurrent.futures
import shutil
import unittest
from pathlib import Path
from cryptography.fernet import Fernet

from app.core.config import Settings
from app.core.exceptions import SecurityHardeningError
from app.services.memory_service import MemoryService
from app.services.personality_service import PersonalityService
from app.services.system_service import SystemService
from app.services.vault_service import VaultService


class TestJarvisMarkV(unittest.TestCase):
    """Test suite verifying fail-fast hardening, telemetry, and concurrency isolation."""

    def test_fail_fast_validation_missing_key(self) -> None:
        """Verifies that validate_fail_fast raises SecurityHardeningError when GEMINI_API_KEY is missing."""
        insecure_settings = Settings(
            gemini_api_key="",
            vault_key=None,
            jarvis_token=None,
            environment="development",
            host="0.0.0.0",
            port=8000,
        )
        with self.assertRaises(SecurityHardeningError):
            insecure_settings.validate_fail_fast()

    def test_system_telemetry(self) -> None:
        """Verifies that SystemService collects complete telemetry metrics."""
        telemetry = SystemService.get_telemetry()
        self.assertIn("cpu_usage_percent", telemetry)
        self.assertIn("ram_usage_percent", telemetry)
        self.assertIn("disk_usage_percent", telemetry)
        self.assertIsInstance(telemetry["platform"], str)

    def test_memory_service_concurrency(self) -> None:
        """Verifies thread-safety of MemoryService under concurrent access."""
        service = MemoryService()
        items_to_write = 100

        def worker(idx: int) -> None:
            service.set_item(f"key_{idx}", f"val_{idx}")
            self.assertEqual(service.get_item(f"key_{idx}"), f"val_{idx}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(items_to_write)]
            for f in concurrent.futures.as_completed(futures):
                f.result()

        self.assertEqual(service.get_item("key_42"), "val_42")

    def test_personality_service(self) -> None:
        """Verifies personality matrix boundaries and instruction generation."""
        service = PersonalityService()
        success, _ = service.adjust_trait("sarcasmo", 75)
        self.assertTrue(success)
        self.assertEqual(service.get_matrix()["sarcasmo"], 75)

        instructions = service.get_system_instructions()
        self.assertIn("J.A.R.V.I.S.", instructions)
        self.assertIn("Senhor", instructions)

    def test_vault_service_encryption(self) -> None:
        """Verifies AES-256 encryption and decryption of secrets."""
        test_vault_dir = Path("test_vault_tmp")
        key = Fernet.generate_key().decode()

        # Temporarily configure cipher with valid test key
        vault = VaultService(vault_dir=test_vault_dir)
        vault._cipher = Fernet(key.encode("utf-8"))

        try:
            saved_path = vault.store_encrypted("senha_mestra", "super_secret_payload_123")
            self.assertTrue(saved_path.exists())

            decrypted = vault.retrieve_decrypted("senha_mestra")
            self.assertEqual(decrypted, "super_secret_payload_123")
        finally:
            if test_vault_dir.exists():
                shutil.rmtree(test_vault_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
