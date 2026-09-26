from __future__ import annotations

"""Weather observation service with real-time API integrations and graceful fallbacks."""

import logging
import os
import requests
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeatherData:
    """Structured weather metrics."""

    city: str
    temperature_celsius: float
    description: str
    humidity_percent: int


class WeatherService:
    """Queries meteorological satellites and weather APIs."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initializes weather service.

        Args:
            api_key: Optional OpenWeather API key. Defaults to WEATHER_API_KEY from env.
        """
        self.api_key = api_key or os.getenv("WEATHER_API_KEY", "").strip()

    def get_weather(self, city: str) -> WeatherData | str:
        """Retrieves real-time weather information for a specific city.

        Args:
            city: Name of the municipality or location.

        Returns:
            WeatherData | str: Parsed weather object or formatted descriptive string.
        """
        if not self.api_key:
            logger.warning("WEATHER_API_KEY not configured.")
            return "Sensor de clima desativado. Chave API não encontrada no ambiente."

        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={self.api_key}&units=metric&lang=pt_br"
        )

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if data.get("cod") == 200:
                main_info = data.get("main", {})
                weather_info = data.get("weather", [{}])[0]

                return WeatherData(
                    city=city,
                    temperature_celsius=float(main_info.get("temp", 0.0)),
                    description=str(weather_info.get("description", "sem dados")),
                    humidity_percent=int(main_info.get("humidity", 0)),
                )
            else:
                logger.warning("Weather API returned non-200 for %s: %s", city, data)
                return f"Não foi possível localizar os dados meteorológicos para '{city}'."

        except Exception as exc:
            logger.error("Meteorological request failed for '%s': %s", city, exc)
            return f"Falha temporária nos sensores meteorológicos: {exc}"
