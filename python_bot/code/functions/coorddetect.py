import re

def find_coordinates(text: str) -> list[str]:
    """Finds coordinates in text and returns them as a list of strings in DD format with map links."""
    found_coords = []

    # 1. Decimal Degrees (DD)
    # Examples: 59.6091, -108.7217 | 32.30642° N 122.61458° W | N 52.456095 W 001.567915
    dd_regex = re.compile(r"(?i)([NS])?\s*(-?\d{1,3}\.\d{2,})[°\s]*([NS])?\s*[\s\t,;]+\s*([EW])?\s*(-?\d{1,3}\.\d{2,})[°\s]*([EW])?")
    for match in dd_regex.finditer(text):
        h1_pre, lat_val, h1_post, h2_pre, lon_val, h2_post = match.groups()
        
        try:
            lat = float(lat_val)
            lon = float(lon_val)
            
            h1 = (h1_pre or h1_post)
            h2 = (h2_pre or h2_post)
            
            if h1 and h1.upper() == 'S' and lat > 0: lat = -lat
            if h1 and h1.upper() == 'N' and lat < 0: lat = abs(lat)
            if h2 and h2.upper() == 'W' and lon > 0: lon = -lon
            if h2 and h2.upper() == 'E' and lon < 0: lon = abs(lon)
            
            found_coords.append(f"{lat}, {lon}")
        except ValueError:
            continue

    # 2. Degrees Decimal Minutes (DMM)
    # Examples: N 59° 36.551 W 108° 43.304 | 59 36.551 -108 43.304
    dmm_regex = re.compile(r"(?i)([NS])?\s*(-?\d{1,3})[°\s]+(\d{1,3}(?:\.\d+)?)['′]?\s*([NS])?\s*[\s\t,;]+\s*([EW])?\s*(-?\d{1,3})[°\s]+(\d{1,3}(?:\.\d+)?)['′]?\s*([EW])?")
    for match in dmm_regex.finditer(text):
        h1_pre, d1, m1, h1_post, h2_pre, d2, m2, h2_post = match.groups()
        
        try:
            m1_f = float(m1)
            m2_f = float(m2)
            if m1_f >= 60 or m2_f >= 60: continue
            
            lat_deg = float(d1)
            lon_deg = float(d2)
            
            lat_sign = -1 if lat_deg < 0 else 1
            lon_sign = -1 if lon_deg < 0 else 1
            
            lat = abs(lat_deg) + m1_f / 60
            lon = abs(lon_deg) + m2_f / 60
            
            lat *= lat_sign
            lon *= lon_sign
            
            h1 = (h1_pre or h1_post)
            h2 = (h2_pre or h2_post)
            
            if h1 and h1.upper() == 'S' and lat > 0: lat = -lat
            if h1 and h1.upper() == 'N' and lat < 0: lat = abs(lat)
            if h2 and h2.upper() == 'W' and lon > 0: lon = -lon
            if h2 and h2.upper() == 'E' and lon < 0: lon = abs(lon)
            
            found_coords.append(f"{lat}, {lon}")
        except ValueError:
            continue

    # 3. Degrees Minutes Seconds (DMS)
    # Examples: 59° 36' 33.1" N 108° 43' 18.2" W | N 59° 36' 33.088'' W 108° 43' 18.239''
    dms_regex = re.compile(r"(?i)([NS])?\s*(-?\d{1,3})[°\s]+(\d{1,2})['′\s]+(\d{1,2}(?:\.\d+)?)[\"″'']*\s*([NS])?\s*[\s\t,;]+\s*([EW])?\s*(-?\d{1,3})[°\s]+(\d{1,2})['′\s]+(\d{1,2}(?:\.\d+)?)[\"″'']*\s*([EW])?")
    for match in dms_regex.finditer(text):
        h1_pre, d1, m1, s1, h1_post, h2_pre, d2, m2, s2, h2_post = match.groups()
        
        try:
            m1_f, s1_f = float(m1), float(s1)
            m2_f, s2_f = float(m2), float(s2)
            if m1_f >= 60 or s1_f >= 60 or m2_f >= 60 or s2_f >= 60: continue
            
            lat_deg = float(d1)
            lon_deg = float(d2)
            
            lat_sign = -1 if lat_deg < 0 else 1
            lon_sign = -1 if lon_deg < 0 else 1
            
            lat = abs(lat_deg) + m1_f / 60 + s1_f / 3600
            lon = abs(lon_deg) + m2_f / 60 + s2_f / 3600
            
            lat *= lat_sign
            lon *= lon_sign
            
            h1 = (h1_pre or h1_post)
            h2 = (h2_pre or h2_post)
            
            if h1 and h1.upper() == 'S' and lat > 0: lat = -lat
            if h1 and h1.upper() == 'N' and lat < 0: lat = abs(lat)
            if h2 and h2.upper() == 'W' and lon > 0: lon = -lon
            if h2 and h2.upper() == 'E' and lon < 0: lon = abs(lon)
            
            found_coords.append(f"{lat}, {lon}")
        except ValueError:
            continue

    unique_coords = []
    seen = set()
    for c in found_coords:
        if c not in seen:
            lat_str, lon_str = c.split(',')
            lat_str = lat_str.strip()
            lon_str = lon_str.strip()
            formatted = f"<:map_dot:1457804317963718840> Geocaching Map: [click](<https://www.geocaching.com/play/map?lat={lat_str}&lng={lon_str}&r=10>), Google Maps: [click](<https://www.google.com/maps/search/?api=1&query={lat_str}%2C{lon_str}>), OSM Map: [click](<https://www.openstreetmap.org/#map=18/{lat_str}/{lon_str}>)"
            unique_coords.append(formatted)
            seen.add(c)
    
    return unique_coords