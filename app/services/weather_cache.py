import hashlib
from datetime import datetime, timedelta
from typing import Any

from app.core.logging import logger


class WeatherCache:
    """In-memory weather data cache with TTL"""

    def __init__(self, ttl_hours: int = 1):
        self._cache: dict[str, dict[str, Any]] = {}
        self.ttl_hours = ttl_hours
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "expired": 0
        }

    def _generate_key(self, location: str, lat: float, lon: float) -> str:
        """Generate cache key for location"""
        # Create a consistent key regardless of location format
        location_str = f"{location.lower().strip()}_{lat:.4f}_{lon:.4f}"
        return hashlib.md5(location_str.encode()).hexdigest()[:16]  # Shorter key

    def get(self, location: str, lat: float, lon: float) -> dict[str, Any] | None:
        """Get cached weather data if not expired"""
        try:
            key = self._generate_key(location, lat, lon)

            if key not in self._cache:
                self._stats["misses"] += 1
                logger.debug(f"Weather cache miss for {location}")
                return None

            cached_data = self._cache[key]
            cached_time = datetime.fromisoformat(cached_data["cached_at"])

            # Check if expired
            if datetime.now() - cached_time > timedelta(hours=self.ttl_hours):
                del self._cache[key]
                self._stats["expired"] += 1
                logger.info(f"Weather cache expired for {location}")
                return None

            self._stats["hits"] += 1
            logger.info(f"Weather cache hit for {location} (age: {datetime.now() - cached_time})")
            return cached_data["data"]

        except Exception as e:
            logger.error(f"Error retrieving from weather cache: {e}")
            return None

    def set(self, location: str, lat: float, lon: float, data: dict[str, Any]) -> None:
        """Cache weather data"""
        try:
            key = self._generate_key(location, lat, lon)

            self._cache[key] = {
                "data": data,
                "cached_at": datetime.now().isoformat(),
                "location": location,
                "coordinates": {"lat": lat, "lon": lon}
            }

            self._stats["sets"] += 1
            logger.info(f"Weather data cached for {location} (cache size: {len(self._cache)})")

            # Cleanup old entries if cache gets too large
            if len(self._cache) > 100:  # Limit cache size
                self._cleanup_old_entries()

        except Exception as e:
            logger.error(f"Error setting weather cache: {e}")

    def clear_expired(self) -> int:
        """Clear expired cache entries and return count of cleared entries"""
        try:
            current_time = datetime.now()
            expired_keys = []

            for key, cached_data in self._cache.items():
                try:
                    cached_time = datetime.fromisoformat(cached_data["cached_at"])
                    if current_time - cached_time > timedelta(hours=self.ttl_hours):
                        expired_keys.append(key)
                except Exception as e:
                    logger.warning(f"Invalid cache entry format for key {key}: {e}")
                    expired_keys.append(key)  # Remove invalid entries

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                self._stats["expired"] += len(expired_keys)
                logger.info(f"Cleared {len(expired_keys)} expired weather cache entries")

            return len(expired_keys)

        except Exception as e:
            logger.error(f"Error clearing expired cache entries: {e}")
            return 0

    def _cleanup_old_entries(self) -> None:
        """Remove oldest entries when cache is full"""
        try:
            if len(self._cache) <= 50:  # Keep some entries
                return

            # Sort by cache time and remove oldest entries
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1]["cached_at"]
            )

            # Remove oldest 25% of entries
            entries_to_remove = len(sorted_entries) // 4
            for i in range(entries_to_remove):
                key = sorted_entries[i][0]
                del self._cache[key]

            logger.info(f"Cleaned up {entries_to_remove} old cache entries")

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_size": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "expired": self._stats["expired"],
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_hours": self.ttl_hours
        }

    def clear_all(self) -> None:
        """Clear all cache entries"""
        cleared_count = len(self._cache)
        self._cache.clear()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "expired": 0
        }
        logger.info(f"Cleared all {cleared_count} weather cache entries")

    def get_cached_locations(self) -> list[dict[str, Any]]:
        """Get list of currently cached locations"""
        try:
            locations = []
            current_time = datetime.now()

            for _key, cached_data in self._cache.items():
                try:
                    cached_time = datetime.fromisoformat(cached_data["cached_at"])
                    age_minutes = (current_time - cached_time).total_seconds() / 60

                    locations.append({
                        "location": cached_data.get("location", "Unknown"),
                        "coordinates": cached_data.get("coordinates", {}),
                        "cached_at": cached_data["cached_at"],
                        "age_minutes": round(age_minutes, 1),
                        "expires_in_minutes": round((self.ttl_hours * 60) - age_minutes, 1)
                    })
                except Exception as e:
                    logger.warning(f"Invalid cache entry: {e}")
                    continue

            return sorted(locations, key=lambda x: x["age_minutes"])

        except Exception as e:
            logger.error(f"Error getting cached locations: {e}")
            return []
