from __future__ import annotations

"""System telemetry and hardware resource monitoring service."""

import logging
import platform
import psutil
from typing import TypedDict

logger = logging.getLogger(__name__)


class TelemetryData(TypedDict):
    """Schema for system resource telemetry."""

    cpu_usage_percent: float
    ram_usage_percent: float
    ram_available_mb: float
    disk_usage_percent: float
    platform: str
    python_version: str


class SystemService:
    """Provides safe telemetry and OS-level hardware inspection."""

    @staticmethod
    def get_telemetry() -> TelemetryData:
        """Collects current CPU, RAM, and Disk utilization safely.

        Returns:
            TelemetryData: Hardware metric snapshots.
        """
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_usage_percent": float(cpu),
                "ram_usage_percent": float(mem.percent),
                "ram_available_mb": round(mem.available / (1024 * 1024), 2),
                "disk_usage_percent": float(disk.percent),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
            }
        except Exception as exc:
            logger.error("Failed to gather system telemetry: %s", exc)
            return {
                "cpu_usage_percent": 0.0,
                "ram_usage_percent": 0.0,
                "ram_available_mb": 0.0,
                "disk_usage_percent": 0.0,
                "platform": platform.platform(),
                "python_version": platform.python_version(),
            }
