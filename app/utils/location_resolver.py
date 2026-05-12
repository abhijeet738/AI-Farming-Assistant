import re

from app.core.logging import logger


class LocationResolver:
    """Resolve various location formats to coordinates and normalized names"""

    # Indian state/city mappings for better resolution
    INDIAN_LOCATIONS = {
        # States to major cities
        "maharashtra": "Mumbai, Maharashtra, India",
        "punjab": "Chandigarh, Punjab, India",
        "uttar pradesh": "Lucknow, Uttar Pradesh, India",
        "bihar": "Patna, Bihar, India",
        "west bengal": "Kolkata, West Bengal, India",
        "tamil nadu": "Chennai, Tamil Nadu, India",
        "karnataka": "Bangalore, Karnataka, India",
        "gujarat": "Ahmedabad, Gujarat, India",
        "rajasthan": "Jaipur, Rajasthan, India",
        "madhya pradesh": "Bhopal, Madhya Pradesh, India",
        "andhra pradesh": "Hyderabad, Andhra Pradesh, India",
        "telangana": "Hyderabad, Telangana, India",
        "kerala": "Kochi, Kerala, India",
        "odisha": "Bhubaneswar, Odisha, India",
        "haryana": "Gurgaon, Haryana, India",
        "jharkhand": "Ranchi, Jharkhand, India",
        "assam": "Guwahati, Assam, India",
        "chhattisgarh": "Raipur, Chhattisgarh, India",
        "uttarakhand": "Dehradun, Uttarakhand, India",
        "himachal pradesh": "Shimla, Himachal Pradesh, India",

        # Major cities (already specific)
        "mumbai": "Mumbai, Maharashtra, India",
        "delhi": "New Delhi, Delhi, India",
        "bangalore": "Bangalore, Karnataka, India",
        "hyderabad": "Hyderabad, Telangana, India",
        "chennai": "Chennai, Tamil Nadu, India",
        "kolkata": "Kolkata, West Bengal, India",
        "pune": "Pune, Maharashtra, India",
        "ahmedabad": "Ahmedabad, Gujarat, India",
        "jaipur": "Jaipur, Rajasthan, India",
        "lucknow": "Lucknow, Uttar Pradesh, India",
        "kanpur": "Kanpur, Uttar Pradesh, India",
        "nagpur": "Nagpur, Maharashtra, India",
        "indore": "Indore, Madhya Pradesh, India",
        "thane": "Thane, Maharashtra, India",
        "bhopal": "Bhopal, Madhya Pradesh, India",
        "visakhapatnam": "Visakhapatnam, Andhra Pradesh, India",
        "pimpri": "Pimpri-Chinchwad, Maharashtra, India",
        "patna": "Patna, Bihar, India",
        "vadodara": "Vadodara, Gujarat, India",
        "ludhiana": "Ludhiana, Punjab, India",
        "agra": "Agra, Uttar Pradesh, India",
        "nashik": "Nashik, Maharashtra, India",
        "faridabad": "Faridabad, Haryana, India",
        "meerut": "Meerut, Uttar Pradesh, India",
        "rajkot": "Rajkot, Gujarat, India",
        "kalyan": "Kalyan, Maharashtra, India",
        "vasai": "Vasai-Virar, Maharashtra, India",
        "varanasi": "Varanasi, Uttar Pradesh, India",
        "srinagar": "Srinagar, Jammu and Kashmir, India",
        "aurangabad": "Aurangabad, Maharashtra, India",
        "dhanbad": "Dhanbad, Jharkhand, India",
        "amritsar": "Amritsar, Punjab, India",
        "navi mumbai": "Navi Mumbai, Maharashtra, India",
        "allahabad": "Prayagraj, Uttar Pradesh, India",
        "prayagraj": "Prayagraj, Uttar Pradesh, India",
        "howrah": "Howrah, West Bengal, India",
        "ranchi": "Ranchi, Jharkhand, India",
        "gwalior": "Gwalior, Madhya Pradesh, India",
        "jabalpur": "Jabalpur, Madhya Pradesh, India",
        "coimbatore": "Coimbatore, Tamil Nadu, India"
    }

    @classmethod
    def normalize_location(cls, location: str) -> str:
        """Normalize location string for better API results"""
        if not location:
            raise ValueError("Location cannot be empty")

        location = location.lower().strip()

        # Check if it's coordinates first
        if cls.extract_coordinates(location):
            return location  # Return as-is for coordinates

        # Check if it's a known Indian location
        if location in cls.INDIAN_LOCATIONS:
            normalized = cls.INDIAN_LOCATIONS[location]
            logger.info(f"Normalized '{location}' to '{normalized}'")
            return normalized

        # Check for partial matches (e.g., "mumbai maharashtra" -> "mumbai")
        for key, value in cls.INDIAN_LOCATIONS.items():
            if key in location or location in key:
                logger.info(f"Partial match: normalized '{location}' to '{value}'")
                return value

        # Add country suffix if not present and doesn't look like international
        if "india" not in location and not re.search(r'\b(usa|uk|canada|australia|china|japan)\b', location):
            location += ", India"

        normalized = location.title()
        logger.info(f"Generic normalization: '{location}' to '{normalized}'")
        return normalized

    @classmethod
    def extract_coordinates(cls, location: str) -> tuple[float, float] | None:
        """Extract coordinates if location is in lat,lon format"""
        # Support various coordinate formats
        patterns = [
            r'^(-?\d+\.?\d*),\s*(-?\d+\.?\d*)$',  # 19.0760,72.8777
            r'^(-?\d+\.?\d*)\s+(-?\d+\.?\d*)$',   # 19.0760 72.8777
            r'^lat:\s*(-?\d+\.?\d*),?\s*lon:\s*(-?\d+\.?\d*)$',  # lat:19.0760,lon:72.8777
            r'^(-?\d+\.?\d*)°?\s*[NS],?\s*(-?\d+\.?\d*)°?\s*[EW]$'  # 19.0760°N,72.8777°E
        ]

        location = location.strip()

        for pattern in patterns:
            match = re.match(pattern, location, re.IGNORECASE)
            if match:
                try:
                    lat, lon = float(match.group(1)), float(match.group(2))

                    # Validate coordinate ranges
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        logger.info(f"Extracted coordinates from '{location}': {lat}, {lon}")
                        return lat, lon
                    else:
                        logger.warning(f"Invalid coordinate ranges in '{location}': lat={lat}, lon={lon}")
                except ValueError:
                    continue

        return None

    @classmethod
    def is_indian_location(cls, location: str) -> bool:
        """Check if location appears to be in India"""
        location_lower = location.lower()

        # Check for explicit India mention
        if "india" in location_lower:
            return True

        # Check against known Indian locations
        if location_lower in cls.INDIAN_LOCATIONS:
            return True

        # Check for Indian state/city names
        indian_keywords = [
            "maharashtra", "punjab", "gujarat", "rajasthan", "karnataka",
            "tamil nadu", "kerala", "west bengal", "uttar pradesh", "bihar",
            "mumbai", "delhi", "bangalore", "hyderabad", "chennai", "kolkata"
        ]

        return any(keyword in location_lower for keyword in indian_keywords)

    @classmethod
    def get_location_info(cls, location: str) -> dict:
        """Get detailed information about a location"""
        normalized = cls.normalize_location(location)
        coordinates = cls.extract_coordinates(location)
        is_indian = cls.is_indian_location(location)

        return {
            "original": location,
            "normalized": normalized,
            "coordinates": coordinates,
            "is_indian": is_indian,
            "is_coordinates": coordinates is not None
        }
