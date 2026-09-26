from __future__ import annotations

"""Unit and validation tests for J.A.R.V.I.S. Mark V core architecture."""

import concurrent.futures
import unittest
from app.core.config import Settings
from app.core.exceptions import SecurityHardeningError
from app.services.memory_service import MemoryService
from app.services.system_service import SystemService


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


if __name__ == "__main__":
    unittest.main()

