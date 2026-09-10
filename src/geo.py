"""Geographic coordinates lookup for Indian States and major agricultural districts."""

from typing import Tuple, Dict

# Centroids of Indian States & Union Territories (Lat, Lon)
STATE_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Maharashtra": (19.7515, 75.7139),
    "Karnataka": (15.3173, 75.7139),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Punjab": (31.1471, 75.3412),
    "Haryana": (29.0588, 76.0856),
    "Tamil Nadu": (11.1271, 78.6569),
    "Andhra Pradesh": (15.9129, 79.7400),
    "Telangana": (18.1124, 79.0193),
    "West Bengal": (22.9868, 87.8550),
    "Gujarat": (22.2587, 71.1924),
    "Rajasthan": (27.0238, 74.2179),
    "Kerala": (10.8505, 76.2711),
    "Keralam": (10.8505, 76.2711),
    "Bihar": (25.0961, 85.3131),
    "Odisha": (20.9517, 85.0985),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Uttarakhand": (30.0668, 79.0193),
    "NCT of Delhi": (28.7041, 77.1025),
    "Delhi": (28.7041, 77.1025),
    "Jammu and Kashmir": (33.7782, 76.5762),
    "Assam": (26.2006, 92.9376),
    "Chhattisgarh": (21.2787, 81.8661),
    "Jharkhand": (23.6102, 85.2799),
}

# Major Agricultural District Centroids
DISTRICT_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Nashik": (20.0059, 73.7904),
    "Pune": (18.5204, 73.8567),
    "Solapur": (17.6599, 75.9064),
    "Ahmednagar": (19.0952, 74.7496),
    "Thane": (19.2183, 72.9781),
    "Kolar": (13.1367, 78.1292),
    "Bangalore Urban": (12.9716, 77.5946),
    "Belgaum": (15.8497, 74.4977),
    "Agra": (27.1767, 78.0081),
    "Farrukhabad": (27.3826, 79.5828),
    "Aligarh": (27.8974, 78.0880),
    "Kanpur": (26.4499, 80.3319),
    "Indore": (22.7196, 75.8577),
    "Ujjain": (23.1765, 75.7885),
    "Patiala": (30.3398, 76.3869),
    "Fazilka": (30.4036, 74.0277),
    "Amritsar": (31.6340, 74.8723),
    "Karnal": (29.6857, 76.9905),
    "North Delhi": (28.7163, 77.1772),
    "Kolkata": (22.5726, 88.3639),
    "Hooghly": (22.9048, 88.3968),
    "Ernakulam": (9.9816, 76.2999),
    "Kancheepuram": (12.8342, 79.7036),
}


def get_coordinates(district: str, state: str) -> Tuple[float, float]:
    """Retrieve best available coordinates for a district or state."""
    d_clean = district.strip().title()
    s_clean = state.strip().title()

    if d_clean in DISTRICT_COORDINATES:
        return DISTRICT_COORDINATES[d_clean]
    
    if s_clean in STATE_COORDINATES:
        lat, lon = STATE_COORDINATES[s_clean]
        # Slight deterministic jitter based on district name hash so all mandis don't stack on 1 pixel
        jitter_lat = ((hash(d_clean) % 100) / 500.0) - 0.1
        jitter_lon = ((hash(d_clean[::-1]) % 100) / 500.0) - 0.1
        return round(lat + jitter_lat, 4), round(lon + jitter_lon, 4)

    return (20.5937, 78.9629)
