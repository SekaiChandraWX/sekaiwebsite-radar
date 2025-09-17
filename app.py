import streamlit as st
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import matplotlib.ticker as mticker
from geopy.geocoders import Nominatim
import requests
from bs4 import BeautifulSoup
import re
from math import radians, sin, cos, sqrt, atan2
import urllib.request
import tempfile
import time
import gc
import logging

# Try to import radar-specific packages with fallback
try:
    import pyart
    PYART_AVAILABLE = True
except ImportError:
    try:
        import arm_pyart as pyart
        PYART_AVAILABLE = True
    except ImportError:
        PYART_AVAILABLE = False

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
    CARTOPY_AVAILABLE = True
except ImportError:
    CARTOPY_AVAILABLE = False

try:
    from matplotlib.colors import ListedColormap
    MATPLOTLIB_COLORS_AVAILABLE = True
except ImportError:
    MATPLOTLIB_COLORS_AVAILABLE = False

# Set page config
st.set_page_config(
    page_title="NEXRAD Radar Viewer", 
    page_icon="📡",
    layout="wide"
)

# Suppress matplotlib font debugging messages
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

# PLACEHOLDER: Insert your RADAR_LIST here
RADAR_LIST = [
    ("KBMX", 33.172, -86.770), ("KEOX", 31.460, -85.459), ("KHTX", 34.931, -86.084),
    ("KMXX", 32.537, -85.790), ("KMOB", 30.679, -88.240), ("KSRX", 35.290, -94.362),
    ("KLZK", 34.836, -92.262), ("KFSX", 34.574, -111.198), ("KIWA", 33.289, -111.670),
    ("KEMX", 31.894, -110.630), ("KYUX", 32.495, -114.656), ("KBBX", 39.496, -121.632),
    ("KEYX", 35.098, -117.561), ("KBHX", 40.499, -124.292), ("KVTX", 34.412, -119.179),
    ("KDAX", 38.501, -121.678), ("KNKX", 32.919, -117.041), ("KMUX", 37.155, -121.898),
    ("KHNX", 36.314, -119.632), ("KSOX", 33.818, -117.636), ("KVBX", 34.839, -120.398),
    ("KFTG", 39.786, -104.546), ("KGJX", 39.062, -108.214), ("KPUX", 38.460, -104.181),
    ("KDOX", 38.826, -75.440), ("KEVX", 30.565, -85.922), ("KJAX", 30.485, -81.702),
    ("KBYX", 24.597, -81.703), ("KMLB", 28.113, -80.654), ("KAMX", 25.611, -80.413),
    ("KTLH", 30.398, -84.329), ("KTBW", 27.705, -82.402), ("KFFC", 33.363, -84.566),
    ("KVAX", 30.890, -83.002), ("KJGX", 32.675, -83.351), ("PGUA", 13.456, 144.811),
    ("PHKI", 21.894, -159.552), ("PHKM", 20.125, -155.778), ("PHMO", 21.133, -157.180),
    ("PHWA", 19.095, -155.569), ("KDMX", 41.731, -93.723), ("KDVN", 41.612, -90.581),
    ("KCBX", 43.490, -116.236), ("KSFX", 43.106, -112.686), ("KLOT", 41.604, -88.085),
    ("KILX", 40.150, -89.337), ("KVWX", 38.260, -87.724), ("KIWX", 41.359, -85.700),
    ("KIND", 39.708, -86.280), ("KDDC", 37.761, -99.969), ("KGLD", 39.367, -101.700),
    ("KTWX", 38.997, -96.232), ("KICT", 37.654, -97.443), ("KHPX", 36.737, -87.285),
    ("KJKL", 37.591, -83.313), ("KLVX", 37.975, -85.944), ("KPAH", 37.068, -88.772),
    ("KPOE", 31.155, -92.976), ("KLCH", 30.125, -93.216), ("KLIX", 30.337, -89.825),
    ("KSHV", 32.451, -93.841), ("KBOX", 41.956, -71.137), ("KCBW", 46.039, -67.806),
    ("KGYX", 43.891, -70.256), ("KDTX", 42.700, -83.472), ("KAPX", 44.906, -84.720),
    ("KGRR", 42.894, -85.545), ("KMQT", 46.531, -87.548), ("KDLH", 46.837, -92.210),
    ("KMPX", 44.849, -93.565), ("KEAX", 38.810, -94.264), ("KSGF", 37.235, -93.400),
    ("KLSX", 38.699, -90.683), ("KGWX", 33.897, -88.329), ("KDGX", 32.280, -89.984),
    ("KBLX", 45.854, -108.607), ("KGGW", 48.206, -106.625), ("KTFX", 47.460, -111.385),
    ("KMSX", 47.041, -113.986), ("KMHX", 34.776, -76.876), ("KRAX", 35.665, -78.490),
    ("KLTX", 33.989, -78.429), ("KBIS", 46.771, -100.760), ("KMVX", 47.528, -97.325),
    ("KMBX", 48.393, -100.864), ("KUEX", 40.321, -98.442), ("KLNX", 41.958, -100.576),
    ("KOAX", 41.320, -96.367), ("KABX", 35.150, -106.824), ("KFDX", 34.634, -103.619),
    ("KHDX", 33.077, -106.120), ("KLRX", 40.740, -116.803), ("KESX", 35.701, -114.891),
    ("KRGX", 39.754, -119.462), ("KENX", 42.586, -74.064), ("KBGM", 42.200, -75.985),
    ("KBUF", 42.949, -78.737), ("KTYX", 43.756, -75.680), ("KOKX", 40.865, -72.864),
    ("KCLE", 41.413, -81.860), ("KILN", 39.420, -83.822), ("KFDR", 34.362, -98.977),
    ("KTLX", 35.333, -97.278), ("KINX", 36.175, -95.564), ("KVNX", 36.741, -98.128),
    ("KMAX", 42.081, -122.717), ("KPDT", 45.691, -118.853), ("KRTX", 45.715, -122.965),
    ("KDIX", 39.947, -74.411), ("KPBZ", 40.532, -80.218), ("KCCX", 40.923, -78.004),
    ("TJUA", 18.116, -66.078), ("KCLX", 32.655, -81.042), ("KCAE", 33.949, -81.119),
    ("KGSP", 34.883, -82.220), ("KABR", 45.456, -98.413), ("KUDX", 44.125, -102.830),
    ("KFSD", 43.588, -96.729), ("KMRX", 36.168, -83.402), ("KNQA", 35.345, -89.873),
    ("KOHX", 36.247, -86.563), ("KAMA", 35.233, -101.709), ("KBRO", 25.916, -97.419),
    ("KGRK", 30.722, -97.383), ("KCRP", 27.784, -97.511), ("KFWS", 32.573, -97.303),
    ("KDYX", 32.538, -99.254), ("KEPZ", 31.873, -106.698), ("KHGX", 29.472, -95.079),
    ("KDFX", 29.273, -100.280), ("KLBB", 33.654, -101.814), ("KMAF", 31.943, -102.189),
    ("KSJT", 31.371, -100.492), ("KEWX", 29.704, -98.029), ("KICX", 37.591, -112.862),
    ("KMTX", 41.263, -112.448), ("KFCX", 37.024, -80.274), ("KLWX", 38.976, -77.487),
    ("KAKQ", 36.984, -77.008), ("KCXX", 44.511, -73.166), ("KLGX", 47.116, -124.107),
    ("KATX", 48.195, -122.496), ("KOTX", 47.681, -117.626), ("KGRB", 44.499, -88.111),
    ("KARX", 43.823, -91.191), ("KMKX", 42.968, -88.551), ("KRLX", 38.311, -81.723),
    ("KCYS", 41.152, -104.806), ("KRIW", 43.066, -108.477), ("KHDC", 30.519, -90.407), ("KJAN", 32.319, -90.077)
]

# Check dependencies and show status
dependency_status = {
    "PyART": PYART_AVAILABLE,
    "CartoPy": CARTOPY_AVAILABLE, 
    "Matplotlib Colors": MATPLOTLIB_COLORS_AVAILABLE
}

# Show dependency status in sidebar
with st.sidebar:
    st.subheader("System Status")
    for dep, available in dependency_status.items():
        if available:
            st.success(f"✅ {dep}")
        else:
            st.error(f"❌ {dep}")
    
    if all(dependency_status.values()):
        st.success("🎉 Full radar processing available!")
    else:
        st.warning("⚠️ Limited functionality - some dependencies missing")

@st.cache_data
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points in miles."""
    R = 3958.8  # Earth's radius in miles
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

@st.cache_data
def get_closest_radars(lat, lon, max_distance=230):
    """Return a list of radars sorted by distance, within max_distance miles."""
    distances = []
    for radar_id, radar_lat, radar_lon in RADAR_LIST:
        distance = haversine_distance(lat, lon, radar_lat, radar_lon)
        if distance <= max_distance:
            distances.append((radar_id, distance, radar_lat, radar_lon))
    return sorted(distances, key=lambda x: x[1])

@st.cache_data(ttl=3600)
def get_location_coordinates(location):
    """Use geopy to get latitude and longitude for a location with retries."""
    geolocator = Nominatim(user_agent="radar_plotter")
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            loc = geolocator.geocode(location, timeout=10)
            if loc:
                return loc.latitude, loc.longitude
            else:
                raise ValueError(f"Location '{location}' not found.")
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                raise ValueError(f"Geocoding error after {max_retries} attempts: {str(e)}")

@st.cache_data(ttl=1800)
def get_nexrad_files_for_date(radar_id, date_obj):
    """Get available NEXRAD files for a specific radar and date."""
    base_url = f"https://www.ncdc.noaa.gov/nexradinv/bdp-download.jsp?id={radar_id}&yyyy={date_obj.year}&mm={date_obj.strftime('%m')}&dd={date_obj.strftime('%d')}&product=AAL2"
    
    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.find_all("a", href=True)
        
        gz_cutoff = datetime(2016, 6, 1, 13, 0)
        include_non_gz = date_obj >= gz_cutoff.date()
        
        file_urls = []
        for link in links:
            href = link["href"]
            if href.endswith(".gz") or (include_non_gz and href.endswith("_V06")):
                file_urls.append(href)
        
        # Parse file times
        file_times = []
        for url in file_urls:
            filename = os.path.basename(url)
            try:
                file_time_str = filename[4:19]
                file_time = datetime.strptime(file_time_str, "%Y%m%d_%H%M%S")
                file_times.append((file_time, url, filename))
            except ValueError:
                continue
        
        return sorted(file_times, key=lambda x: x[0])
    
    except Exception as e:
        st.error(f"Error accessing NOAA data for {radar_id}: {str(e)}")
        return []

def download_radar_file(file_url):
    """Download radar file to temporary location."""
    filename = os.path.basename(file_url)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gz' if filename.endswith('.gz') else '') as tmp_file:
        temp_path = tmp_file.name
    
    try:
        urllib.request.urlretrieve(file_url, temp_path)
        return temp_path
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise Exception(f"Download error: {str(e)}")

def miles_to_degrees(miles, latitude):
    """Convert miles to degrees at a given latitude."""
    lat_degrees = miles / 69.0
    lon_degrees = miles / (69.0 * np.cos(np.radians(latitude)))
    return lat_degrees, lon_degrees

def create_reflectivity_colormap():
    """Create custom reflectivity colormap"""
    # PLACEHOLDER: Insert your reflectivity color_data here
    color_data = [
        (-32.0, 115, 77, 172), (-31.5, 115, 78, 168), (-31.0, 115, 79, 165), (-30.5, 115, 81, 162),
        (-30.0, 116, 82, 158), (-29.5, 116, 84, 155), (-29.0, 116, 85, 152), (-28.5, 117, 86, 148),
        (-28.0, 117, 88, 145), (-27.5, 117, 89, 142), (-27.0, 118, 91, 138), (-26.5, 118, 92, 135),
        (-26.0, 118, 94, 132), (-25.5, 119, 95, 128), (-25.0, 119, 96, 125), (-24.5, 119, 98, 122),
        (-24.0, 120, 99, 118), (-23.5, 120, 101, 115), (-23.0, 120, 102, 112), (-22.5, 121, 103, 108),
        (-22.0, 121, 105, 105), (-21.5, 121, 106, 102), (-21.0, 122, 108, 98), (-20.5, 122, 109, 95),
        (-20.0, 122, 111, 92), (-19.5, 123, 112, 88), (-19.0, 123, 113, 85), (-18.5, 123, 115, 82),
        (-18.0, 124, 116, 78), (-17.5, 124, 118, 75), (-17.0, 124, 119, 72), (-16.5, 125, 121, 69),
        (-16.0, 127, 123, 72), (-15.5, 129, 125, 75), (-15.0, 131, 127, 79), (-14.5, 133, 130, 82),
        (-14.0, 135, 132, 85), (-13.5, 137, 134, 89), (-13.0, 139, 137, 92), (-12.5, 141, 139, 96),
        (-12.0, 144, 141, 99), (-11.5, 146, 144, 102), (-11.0, 148, 146, 106), (-10.5, 150, 148, 109),
        (-10.0, 152, 151, 113), (-9.5, 154, 153, 116), (-9.0, 156, 155, 119), (-8.5, 158, 158, 123),
        (-8.0, 161, 160, 126), (-7.5, 163, 162, 130), (-7.0, 165, 165, 133), (-6.5, 167, 167, 136),
        (-6.0, 169, 169, 140), (-5.5, 171, 172, 143), (-5.0, 173, 174, 147), (-4.5, 175, 176, 150),
        (-4.0, 178, 179, 154), (-3.5, 173, 175, 153), (-3.0, 168, 171, 152), (-2.5, 163, 167, 151),
        (-2.0, 158, 163, 150), (-1.5, 154, 159, 149), (-1.0, 149, 155, 148), (-0.5, 144, 151, 147),
        (0.0, 139, 147, 146), (0.5, 135, 144, 145), (1.0, 130, 140, 144), (1.5, 125, 136, 143),
        (2.0, 120, 132, 142), (2.5, 115, 128, 142), (3.0, 111, 124, 141), (3.5, 106, 120, 140),
        (4.0, 101, 116, 139), (4.5, 96, 112, 138), (5.0, 92, 109, 137), (5.5, 87, 105, 136),
        (6.0, 82, 101, 135), (6.5, 77, 97, 134), (7.0, 73, 93, 133), (7.5, 68, 89, 132),
        (8.0, 63, 85, 131), (8.5, 58, 81, 130), (9.0, 54, 78, 130), (9.5, 55, 81, 132),
        (10.0, 57, 85, 134), (10.5, 59, 89, 136), (11.0, 61, 93, 138), (11.5, 63, 97, 141),
        (12.0, 65, 101, 143), (12.5, 67, 105, 145), (13.0, 69, 109, 147), (13.5, 71, 113, 149),
        (14.0, 73, 117, 152), (14.5, 74, 121, 154), (15.0, 76, 125, 156), (15.5, 78, 129, 158),
        (16.0, 80, 133, 160), (16.5, 82, 137, 163), (17.0, 84, 141, 165), (17.5, 86, 145, 167),
        (18.0, 88, 149, 169), (18.5, 90, 153, 171), (19.0, 92, 157, 174), (19.5, 76, 165, 142),
        (20.0, 60, 173, 110), (20.5, 45, 182, 78), (21.0, 42, 175, 72), (21.5, 39, 169, 67),
        (22.0, 37, 163, 62), (22.5, 34, 156, 56), (23.0, 31, 150, 51), (23.5, 29, 144, 46),
        (24.0, 26, 137, 40), (24.5, 24, 131, 35), (25.0, 21, 125, 30), (25.5, 18, 118, 24),
        (26.0, 16, 112, 19), (26.5, 13, 106, 14), (27.0, 11, 100, 9), (27.5, 35, 115, 8),
        (28.0, 59, 130, 7), (28.5, 83, 145, 6), (29.0, 107, 161, 5), (29.5, 131, 176, 4),
        (30.0, 155, 191, 3), (30.5, 179, 207, 2), (31.0, 203, 222, 1), (31.5, 227, 237, 0),
        (32.0, 252, 253, 0), (32.5, 248, 248, 0), (33.0, 244, 243, 0), (33.5, 241, 238, 0),
        (34.0, 237, 233, 0), (34.5, 233, 228, 0), (35.0, 230, 223, 0), (35.5, 226, 218, 0),
        (36.0, 222, 213, 0), (36.5, 219, 208, 0), (37.0, 215, 203, 0), (37.5, 211, 198, 0),
        (38.0, 208, 193, 0), (38.5, 204, 188, 0), (39.0, 200, 183, 0), (39.5, 197, 179, 0),
        (40.0, 250, 148, 0), (40.5, 246, 144, 0), (41.0, 242, 141, 1), (41.5, 238, 138, 1),
        (42.0, 234, 135, 2), (42.5, 231, 132, 3), (43.0, 227, 129, 3), (43.5, 223, 126, 4),
        (44.0, 219, 123, 5), (44.5, 215, 120, 5), (45.0, 212, 116, 6), (45.5, 208, 113, 6),
        (46.0, 204, 110, 7), (46.5, 200, 107, 8), (47.0, 196, 104, 8), (47.5, 193, 101, 9),
        (48.0, 189, 98, 10), (48.5, 185, 95, 10), (49.0, 181, 92, 11), (49.5, 178, 89, 12),
        (50.0, 249, 35, 11), (50.5, 242, 35, 12), (51.0, 236, 35, 13), (51.5, 230, 35, 14),
        (52.0, 223, 36, 15), (52.5, 217, 36, 16), (53.0, 211, 36, 17), (53.5, 205, 36, 18),
        (54.0, 198, 37, 19), (54.5, 192, 37, 20), (55.0, 186, 37, 22), (55.5, 180, 37, 23),
        (56.0, 173, 38, 24), (56.5, 167, 38, 25), (57.0, 161, 38, 26), (57.5, 155, 38, 27),
        (58.0, 148, 39, 28), (58.5, 142, 39, 29), (59.0, 136, 39, 30), (59.5, 130, 40, 32),
        (60.0, 202, 153, 180), (60.5, 201, 146, 176), (61.0, 201, 139, 173), (61.5, 200, 133, 169),
        (62.0, 200, 126, 166), (62.5, 199, 120, 162), (63.0, 199, 113, 159), (63.5, 199, 106, 155),
        (64.0, 198, 100, 152), (64.5, 198, 93, 148), (65.0, 197, 87, 145), (65.5, 197, 80, 141),
        (66.0, 196, 74, 138), (66.5, 196, 67, 134), (67.0, 196, 60, 131), (67.5, 195, 54, 127),
        (68.0, 195, 47, 124), (68.5, 194, 41, 120), (69.0, 194, 34, 117), (69.5, 194, 28, 114),
        (70.0, 154, 36, 224), (70.5, 149, 34, 219), (71.0, 144, 33, 215), (71.5, 139, 32, 210),
        (72.0, 134, 31, 206), (72.5, 129, 30, 201), (73.0, 124, 29, 197), (73.5, 120, 28, 193),
        (74.0, 115, 27, 188), (74.5, 110, 26, 184), (75.0, 105, 24, 179), (75.5, 100, 23, 175),
        (76.0, 95, 22, 170), (76.5, 91, 21, 166), (77.0, 86, 20, 162), (77.5, 81, 19, 157),
        (78.0, 76, 18, 153), (78.5, 71, 17, 148), (79.0, 66, 16, 144), (79.5, 62, 15, 140),
        (80.0, 132, 253, 255), (80.5, 128, 245, 249), (81.0, 125, 238, 243), (81.5, 121, 231, 237),
        (82.0, 118, 224, 231), (82.5, 115, 217, 225), (83.0, 111, 210, 219), (83.5, 108, 203, 213),
        (84.0, 105, 196, 207), (84.5, 101, 189, 201), (85.0, 98, 181, 196), (85.5, 94, 174, 190),
        (86.0, 91, 167, 184), (86.5, 88, 160, 178), (87.0, 84, 153, 172), (87.5, 81, 146, 166),
        (88.0, 78, 139, 160), (88.5, 74, 132, 154), (89.0, 71, 125, 148), (89.5, 68, 118, 143),
        (90.0, 161, 101, 73), (90.5, 155, 90, 65), (91.0, 150, 80, 56), (91.5, 145, 70, 48),
        (92.0, 140, 60, 40), (92.5, 135, 50, 32), (93.0, 130, 40, 24), (93.5, 125, 30, 16),
        (94.0, 120, 20, 8), (94.5, 115, 10, 1)
    ]
    dbz_values = np.array([x[0] for x in color_data])
    colors = [(r / 255, g / 255, b / 255) for _, r, g, b in color_data]
    return ListedColormap(colors, name="custom_reflectivity"), dbz_values

def create_velocity_colormap():
    """Create custom velocity colormap"""
    # PLACEHOLDER: Insert your velocity color_data here
    color_data = [
        (-65.4, 127, 0, 207), (-64.9, 255, 0, 132), (-64.4, 249, 0, 132), (-63.9, 243, 0, 133),
        (-63.4, 237, 0, 134), (-62.8, 231, 0, 135), (-62.3, 225, 1, 136), (-61.8, 219, 1, 137),
        (-61.3, 212, 1, 137), (-60.8, 206, 1, 138), (-60.3, 200, 1, 139), (-59.8, 194, 2, 140),
        (-59.3, 188, 2, 141), (-58.7, 182, 2, 142), (-58.2, 175, 2, 142), (-57.7, 169, 2, 143),
        (-57.2, 163, 3, 144), (-56.7, 157, 3, 145), (-56.2, 151, 3, 146), (-55.7, 145, 3, 147),
        (-55.1, 138, 3, 147), (-54.6, 132, 4, 148), (-54.1, 126, 4, 149), (-53.6, 120, 4, 150),
        (-53.1, 114, 4, 151), (-52.6, 108, 4, 152), (-52.1, 93, 5, 153), (-51.5, 85, 5, 153),
        (-50.5, 77, 4, 153), (-50.0, 69, 4, 153), (-49.5, 61, 3, 153), (-49.0, 52, 3, 153),
        (-48.5, 44, 3, 153), (-48.0, 36, 2, 153), (-47.5, 28, 2, 153), (-47.0, 22, 2, 153),
        (-46.5, 22, 12, 156), (-46.0, 23, 23, 160), (-45.4, 24, 34, 163), (-44.9, 25, 44, 167),
        (-44.4, 26, 55, 170), (-43.9, 27, 66, 174), (-43.4, 28, 76, 177), (-42.9, 29, 87, 181),
        (-42.4, 30, 98, 184), (-41.9, 31, 108, 188), (-41.3, 32, 119, 192), (-40.8, 33, 130, 195),
        (-40.3, 34, 140, 199), (-39.8, 35, 151, 202), (-39.3, 36, 162, 206), (-38.8, 37, 172, 209),
        (-38.3, 38, 183, 213), (-37.8, 39, 194, 216), (-37.2, 40, 204, 220), (-37.0, 48, 224, 227),
        (-36.0, 52, 224, 227), (-35.5, 58, 224, 227), (-35.0, 65, 225, 228), (-34.5, 71, 226, 229),
        (-34.0, 78, 226, 229), (-33.5, 84, 227, 230), (-33.0, 91, 228, 231), (-32.5, 97, 229, 232),
        (-31.9, 104, 229, 232), (-31.4, 110, 230, 233), (-30.9, 123, 231, 234), (-30.4, 130, 232, 235),
        (-29.9, 136, 233, 236), (-29.4, 143, 234, 237), (-28.9, 149, 234, 237), (-28.4, 156, 235, 238),
        (-27.8, 162, 236, 239), (-27.3, 169, 236, 239), (-26.8, 175, 237, 240), (-26.3, 182, 238, 241),
        (-25.8, 167, 241, 218), (-25.3, 154, 242, 200), (-24.8, 140, 243, 181), (-24.3, 127, 245, 163),
        (-23.7, 113, 246, 144), (-23.2, 100, 247, 126), (-22.7, 87, 248, 108), (-22.2, 73, 250, 89),
        (-21.7, 60, 251, 71), (-21.2, 46, 252, 52), (-20.7, 33, 253, 34), (-20.2, 3, 250, 3),
        (-19.6, 3, 245, 3), (-19.1, 3, 240, 3), (-18.6, 3, 234, 3), (-18.1, 3, 229, 3),
        (-17.6, 3, 224, 3), (-17.1, 3, 219, 3), (-16.6, 3, 213, 3), (-15.9, 3, 208, 3),
        (-15.4, 3, 203, 3), (-14.9, 3, 198, 3), (-14.4, 3, 192, 3), (-13.9, 3, 187, 3),
        (-13.4, 3, 182, 3), (-12.9, 3, 177, 3), (-12.4, 2, 171, 2), (-11.8, 2, 166, 2),
        (-11.3, 2, 161, 2), (-10.8, 2, 156, 2), (-10.3, 2, 150, 2), (-9.8, 2, 145, 2),
        (-9.3, 2, 140, 2), (-8.8, 2, 135, 2), (-8.2, 2, 129, 2), (-7.7, 2, 124, 2),
        (-7.2, 2, 119, 2), (-6.7, 2, 114, 2), (-6.2, 2, 108, 2), (-5.7, 2, 103, 2),
        (-5.1, 5, 102, 3), (-4.6, 78, 121, 76), (-4.1, 82, 122, 80), (-3.6, 86, 124, 84),
        (-3.1, 90, 125, 88), (-2.6, 94, 126, 92), (-2.1, 98, 128, 96), (-1.5, 102, 129, 100),
        (-1.0, 106, 130, 104), (-0.5, 110, 132, 108), (-0.3, 114, 133, 112), (0, 0, 0, 0),
        (0.3, 138, 118, 118), (0.5, 138, 114, 129), (1.0, 138, 108, 122), (1.5, 137, 102, 115),
        (2.1, 136, 95, 108), (2.6, 136, 89, 101), (3.1, 135, 82, 94), (3.6, 134, 76, 86),
        (4.1, 133, 69, 79), (4.6, 133, 63, 72), (5.1, 132, 56, 65), (5.7, 110, 0, 0),
        (6.2, 115, 0, 0), (6.7, 121, 0, 0), (7.2, 126, 0, 0), (7.7, 132, 0, 1),
        (8.2, 137, 0, 1), (8.8, 143, 0, 1), (9.3, 149, 0, 2), (9.8, 154, 0, 2),
        (10.3, 160, 0, 2), (10.8, 165, 0, 3), (11.3, 171, 0, 3), (11.8, 176, 0, 3),
        (12.4, 182, 0, 4), (12.9, 188, 0, 4), (13.4, 193, 0, 4), (13.9, 199, 0, 4),
        (14.4, 204, 0, 5), (14.9, 210, 0, 5), (15.4, 215, 0, 5), (15.9, 221, 0, 6),
        (16.5, 227, 0, 6), (16.9, 232, 0, 6), (17.4, 238, 0, 7), (18.0, 243, 0, 7),
        (18.5, 250, 55, 81), (19.0, 250, 60, 89), (19.5, 250, 65, 97), (20.0, 250, 71, 105),
        (20.6, 251, 76, 113), (21.1, 251, 82, 122), (21.6, 251, 87, 130), (22.1, 252, 93, 138),
        (22.6, 252, 98, 146), (23.1, 252, 104, 155), (23.6, 252, 109, 163), (24.2, 253, 115, 171),
        (24.7, 253, 120, 179), (25.2, 253, 126, 188), (25.7, 254, 131, 196), (26.2, 254, 137, 204),
        (26.7, 255, 140, 213), (27.2, 255, 149, 208), (27.8, 255, 159, 203), (28.3, 255, 168, 198),
        (28.8, 255, 178, 193), (29.3, 255, 187, 188), (29.8, 255, 197, 183), (30.3, 255, 206, 178),
        (30.8, 255, 216, 173), (31.4, 255, 225, 168), (31.9, 255, 232, 163), (32.4, 255, 228, 159),
        (32.9, 255, 224, 155), (33.4, 255, 219, 151), (33.9, 255, 215, 147), (34.4, 255, 211, 142),
        (34.9, 255, 206, 138), (35.5, 255, 202, 134), (36.0, 255, 197, 130), (36.5, 255, 193, 125),
        (37.0, 255, 189, 121), (37.5, 255, 184, 117), (38.0, 255, 180, 113), (38.5, 255, 176, 108),
        (39.1, 255, 171, 104), (39.6, 255, 167, 100), (40.1, 255, 162, 96), (40.6, 255, 158, 91),
        (41.1, 255, 154, 87), (41.6, 255, 149, 83), (42.1, 255, 138, 79), (42.6, 252, 135, 78),
        (43.2, 248, 132, 76), (43.7, 245, 129, 74), (44.2, 241, 126, 72), (44.7, 238, 123, 71),
        (45.2, 234, 120, 69), (45.7, 231, 117, 67), (46.2, 227, 114, 65), (46.7, 224, 111, 63),
        (47.3, 220, 108, 62), (47.8, 216, 104, 60), (48.3, 213, 101, 58), (48.8, 209, 98, 56),
        (49.3, 206, 95, 54), (49.8, 202, 92, 53), (50.3, 199, 89, 51), (50.8, 195, 86, 49),
        (51.4, 192, 83, 47), (51.9, 188, 80, 45), (52.4, 185, 77, 44), (52.9, 181, 74, 42),
        (53.4, 177, 70, 40), (53.9, 174, 67, 38), (54.4, 170, 64, 36), (55.0, 167, 61, 35),
        (55.5, 163, 58, 33), (56.0, 160, 55, 31), (56.5, 156, 52, 29), (57.0, 153, 49, 27),
        (57.5, 149, 46, 26), (58.0, 146, 43, 24), (58.6, 142, 40, 22), (59.1, 138, 36, 20),
        (59.6, 135, 33, 18), (60.1, 131, 30, 17), (60.6, 128, 27, 15), (61.1, 121, 21, 11),
        (61.6, 117, 18, 9), (62.2, 114, 15, 8), (62.7, 110, 12, 6), (63.2, 107, 9, 4),
        (64.2, 103, 6, 2), (64.9, 255, 255, 255)
    ]
    mps_values = np.array([x[0] for x in color_data])
    colors = [(r / 255, g / 255, b / 255) for _, r, g, b in color_data]
    return ListedColormap(colors, name="custom_velocity"), mps_values

def get_sweep_info(radar, target_elevation=0.5, tolerance=0.3):
    """Get information about sweeps with valid data near target elevation."""
    try:
        sweep_starts = radar.sweep_start_ray_index["data"]
        sweep_ends = radar.sweep_end_ray_index["data"]
        time_data = radar.time["data"]
        base_time = datetime.strptime(radar.time["units"].split("since ")[1], "%Y-%m-%dT%H:%M:%SZ")
        elevations = np.array(
            [radar.elevation["data"][start:end + 1].mean() for start, end in zip(sweep_starts, sweep_ends)])
        mean_times = np.array([time_data[start:end + 1].mean() for start, end in zip(sweep_starts, sweep_ends)])
        valid_sweeps = np.abs(elevations - target_elevation) <= tolerance

        sweep_info = []
        for i in np.where(valid_sweeps)[0]:
            sweep_type = []
            elevation = elevations[i]
            
            # Check reflectivity
            refl_valid = False
            if "reflectivity" in radar.fields:
                refl_data = radar.fields["reflectivity"]["data"][radar.get_slice(i)]
                refl_valid = np.any(~np.ma.getmaskarray(refl_data) & ~np.isnan(refl_data))
                if refl_valid:
                    sweep_type.append("reflectivity")

            # Check velocity
            vel_valid = False
            if "velocity" in radar.fields:
                vel_data = radar.fields["velocity"]["data"][radar.get_slice(i)]
                vel_valid = np.any(~np.ma.getmaskarray(vel_data) & ~np.isnan(vel_data))
                if vel_valid:
                    sweep_type.append("velocity")

            if sweep_type:
                sweep_time = base_time + timedelta(seconds=int(mean_times[i]))
                sweep_info.append({
                    "sweep_index": i,
                    "time": sweep_time,
                    "type": sweep_type,
                    "elevation": elevations[i]
                })
        return sweep_info
    except Exception as e:
        return []

def pair_sweeps(sweep_info, max_time_diff=30, is_high_res=True):
    """Pair reflectivity and velocity sweeps within max_time_diff seconds."""
    refl_sweeps = [s for s in sweep_info if "reflectivity" in s["type"]]
    vel_sweeps = [s for s in sweep_info if "velocity" in s["type"]]

    effective_time_diff = max_time_diff if is_high_res else 60

    pairs = []
    used_vel = set()
    for refl in refl_sweeps:
        min_diff = float("inf")
        closest_vel = None
        refl_time = refl["time"]
        
        # Prefer velocity sweep with index 1 if available and within time diff
        for vel in vel_sweeps:
            if vel["sweep_index"] == 1 and vel["sweep_index"] not in used_vel:
                time_diff = abs((vel["time"] - refl_time).total_seconds())
                if time_diff <= effective_time_diff and time_diff < min_diff:
                    min_diff = time_diff
                    closest_vel = vel
        
        # If no sweep 1, try any velocity sweep
        if not closest_vel:
            for vel in vel_sweeps:
                if vel["sweep_index"] in used_vel:
                    continue
                time_diff = abs((vel["time"] - refl_time).total_seconds())
                if time_diff <= effective_time_diff and time_diff < min_diff:
                    min_diff = time_diff
                    closest_vel = vel
                    
        if closest_vel:
            pairs.append((refl, closest_vel))
            used_vel.add(closest_vel["sweep_index"])

    # Fallback: If no pairs found and both sweep types exist, pair closest sweeps
    if not pairs and refl_sweeps and vel_sweeps:
        refl = min(refl_sweeps, key=lambda s: abs((s["time"] - refl_sweeps[0]["time"]).total_seconds()))
        vel = min(vel_sweeps, key=lambda s: abs((s["time"] - refl["time"]).total_seconds()))
        pairs.append((refl, vel))

    return pairs

def simple_improved_dealias_velocity(radar, vel_sweep_index):
    """Simple but effective velocity dealiasing."""
    try:
        nyquist_vel = 28.0
        if "nyquist_velocity" in radar.instrument_parameters:
            nyq_data = radar.instrument_parameters["nyquist_velocity"]["data"]
            if len(nyq_data) > 0:
                nyquist_vel = nyq_data[0]

        dealiased_vel = pyart.correct.dealias_region_based(
            radar,
            vel_field="velocity",
            nyquist_vel=nyquist_vel,
            centered=True,
            keep_original=True,
            gatefilter=False
        )

        radar.add_field("dealiased_velocity", dealiased_vel, replace_existing=True)
        radar.fields["dealiased_velocity"]["units"] = "m/s"

    except Exception as e:
        radar.add_field("dealiased_velocity", radar.fields["velocity"], replace_existing=True)

def parse_filename_for_title(file_path):
    """Parse filename to create plot title."""
    filename = os.path.basename(file_path)
    radar_id = filename[:4]
    date_str = filename[4:12]
    time_str = filename[13:19]
    date_time = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
    date_formatted = date_time.strftime("%B %d, %Y")
    time_formatted = date_time.strftime("%H:%M")
    return f"{radar_id} data for {date_formatted} at {time_formatted} UTC"

def check_resolution(radar):
    """Determine if radar file is low-res or high-res based on year and gate count."""
    try:
        sweep_index = 0
        sweep_slice = radar.get_slice(sweep_index)
        data_shape = radar.fields["velocity"]["data"][sweep_slice].shape
        total_gates = data_shape[0] * data_shape[1]
        try:
            base_time_str = radar.time["units"].split("since ")[1]
            base_year = datetime.strptime(base_time_str, "%Y-%m-%dT%H:%M:%SZ").year
        except Exception:
            base_year = None
        is_super_res = radar.instrument_parameters.get("super_resolution", {}).get("data", [0])[0] == 1
        if base_year is not None and base_year < 2008:
            return False
        gate_threshold = 1000000
        return total_gates >= gate_threshold or is_super_res
    except Exception:
        return True

def plot_radar_data(radar, refl_sweep_index, vel_sweep_index, file_path, center_lat, center_lon):
    """Create radar plot with reflectivity and velocity data - FIXED VERSION."""
    try:
        # STEP 1: Set the radar's location correctly before doing anything else.
        # This whole block of code MUST run before creating the display object.
        radar_id = os.path.basename(file_path)[:4]
        radar_lat, radar_lon = center_lat, center_lon
        
        try:
            parsed_lat = radar.latitude["data"][0]
            parsed_lon = radar.longitude["data"][0]
            if parsed_lat != 0.0 or parsed_lon != 0.0:
                radar_lat, radar_lon = parsed_lat, parsed_lon
        except:
            for rid, rlat, rlon in RADAR_LIST:
                if rid == radar_id:
                    radar_lat, radar_lon = rlat, rlon
                    break
        
        radar.latitude["data"] = np.array([radar_lat])
        radar.longitude["data"] = np.array([radar_lon])

        # Validate that the data fields are not empty
        refl_data = radar.fields["reflectivity"]["data"][radar.get_slice(refl_sweep_index)]
        vel_data = radar.fields["dealiased_velocity"]["data"][radar.get_slice(vel_sweep_index)]

        refl_valid = np.any(~np.ma.getmaskarray(refl_data))
        vel_valid = np.any(~np.ma.getmaskarray(vel_data))

        if not refl_valid or not vel_valid:
            return None

        # Set up the figure
        fig = plt.figure(figsize=(20, 9))
        projection = ccrs.PlateCarree()

        ax1 = fig.add_subplot(121, projection=projection)
        ax2 = fig.add_subplot(122, projection=projection, sharex=ax1, sharey=ax1)

        # STEP 2: NOW create the RadarMapDisplay object.
        # It will be initialized with the corrected coordinates.
        display = pyart.graph.RadarMapDisplay(radar)

        # STEP 3: Proceed with plotting as before.
        # Titles
        refl_elevation = radar.elevation["data"][radar.get_slice(refl_sweep_index)].mean()
        vel_elevation = radar.elevation["data"][radar.get_slice(vel_sweep_index)].mean()

        titles = [
            f"Reflectivity - {refl_elevation:.2f}° Tilt",
            f"Dealiased Velocity - {vel_elevation:.2f}° Tilt"
        ]

        # Set plot extent
        half_width = 35
        lat_deg, lon_deg = miles_to_degrees(half_width, center_lat)
        extent = [center_lon - lon_deg, center_lon + lon_deg,
                  center_lat - lat_deg, center_lat + lat_deg]

        # Use custom colormaps with proper fallback
        try:
            refl_cmap, _ = create_reflectivity_colormap()
            vel_cmap, _ = create_velocity_colormap()
        except:
            try:
                refl_cmap = "pyart_NWSRef"
                vel_cmap = "pyart_balance"
            except:
                refl_cmap = "jet"
                vel_cmap = "RdBu_r"

        # Plot reflectivity with CORRECT range
        display.plot_ppi_map(
            "reflectivity",
            sweep=refl_sweep_index,
            vmin=-32.0,  # FIXED: Match working script
            vmax=94.5,   # FIXED: Match working script
            ax=ax1,
            projection=projection,
            title=titles[0],
            colorbar_label="Reflectivity (dBZ)",
            cmap=refl_cmap,
            resolution='50m'
        )

        # Plot velocity with proper scaling
        nyquist_vel = 28.0
        if "nyquist_velocity" in radar.instrument_parameters:
            nyq_data = radar.instrument_parameters["nyquist_velocity"]["data"]
            if len(nyq_data) > 0:
                nyquist_vel = nyq_data[0] if len(nyq_data) == 1 else nyq_data[vel_sweep_index]

        # Use smaller velocity range for better visualization
        vel_range = min(30, nyquist_vel)  # FIXED: Use 30 instead of 65

        display.plot_ppi_map(
            "dealiased_velocity",
            sweep=vel_sweep_index,
            vmin=-vel_range,
            vmax=vel_range,
            ax=ax2,
            projection=projection,
            title=titles[1],
            colorbar_label="Velocity (m/s)",
            cmap=vel_cmap,
            resolution='50m'
        )

        # Main title
        try:
            base_time_str = radar.time["units"].split("since ")[1]
            scan_time = datetime.strptime(base_time_str, "%Y-%m-%dT%H:%M:%SZ")
            radar_id = os.path.basename(file_path)[:4]
            main_title = f"{radar_id} - {scan_time.strftime('%B %d, %Y at %H:%M UTC')}"
        except:
            main_title = parse_filename_for_title(file_path)

        plt.suptitle(main_title, fontsize=24, fontweight='bold', y=0.95)

        # Attribution
        fig.text(0.5, 0.02, "Plotted by Sekai Chandra (@Sekai_WX)",
                 ha='center', fontsize=12, style='italic')

        # Add geographic features
        for ax in [ax1, ax2]:
            ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3, zorder=0)
            ax.add_feature(cfeature.COASTLINE, linewidth=0.8, color='black', zorder=2)
            ax.add_feature(cfeature.STATES, linestyle="-", linewidth=0.5, color='darkgray', zorder=2)
            ax.add_feature(cfeature.BORDERS, linewidth=0.8, color='black', zorder=2)

            ax.set_extent(extent, crs=projection)

            gl = ax.gridlines(crs=projection, draw_labels=True, linestyle=":",
                              color="gray", alpha=0.7, linewidth=0.5)
            gl.top_labels = gl.right_labels = False
            gl.xformatter = LONGITUDE_FORMATTER
            gl.yformatter = LATITUDE_FORMATTER

            gl.xlocator = mticker.FixedLocator(
                np.arange(np.floor(extent[0]), np.ceil(extent[1]) + 0.5, 0.5)
            )
            gl.ylocator = mticker.FixedLocator(
                np.arange(np.floor(extent[2]), np.ceil(extent[3]) + 0.5, 0.5)
            )

            gl.xlabel_style = gl.ylabel_style = {'size': 11, 'color': 'black'}

        plt.tight_layout(pad=2.0, h_pad=2.0, w_pad=2.0, rect=[0, 0.05, 1, 0.92])

        return fig

    except Exception as e:
        st.error(f"Error plotting radar data: {str(e)}")
        return None

def plot_radar_data_basic(radar, refl_sweep_index, vel_sweep_index, file_path, center_lat, center_lon):
    """Basic radar plotting without CartoPy dependencies."""
    try:
        # Set radar location properly
        radar_id = os.path.basename(file_path)[:4]
        radar_lat, radar_lon = center_lat, center_lon
        
        try:
            parsed_lat = radar.latitude["data"][0]
            parsed_lon = radar.longitude["data"][0]
            if parsed_lat != 0.0 or parsed_lon != 0.0:
                radar_lat, radar_lon = parsed_lat, parsed_lon
        except:
            for rid, rlat, rlon in RADAR_LIST:
                if rid == radar_id:
                    radar_lat, radar_lon = rlat, rlon
                    break
        
        radar.latitude["data"] = np.array([radar_lat])
        radar.longitude["data"] = np.array([radar_lon])
        
        # Get radar data
        refl_data = radar.fields["reflectivity"]["data"][radar.get_slice(refl_sweep_index)]
        vel_data = radar.fields["dealiased_velocity"]["data"][radar.get_slice(vel_sweep_index)]
        
        # Get coordinate data
        azimuth = radar.azimuth["data"][radar.get_slice(refl_sweep_index)]
        ranges = radar.range["data"]
        
        # Convert to Cartesian coordinates
        range_grid, azimuth_grid = np.meshgrid(ranges, azimuth)
        x = range_grid * np.sin(np.deg2rad(azimuth_grid))
        y = range_grid * np.cos(np.deg2rad(azimuth_grid))
        
        # Create plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 9))
        
        # Use custom colormaps or fallback
        try:
            refl_cmap, _ = create_reflectivity_colormap()
            vel_cmap, _ = create_velocity_colormap()
        except:
            refl_cmap = "jet"
            vel_cmap = "RdBu_r"
        
        # Plot reflectivity with FIXED range
        im1 = ax1.pcolormesh(x/1000, y/1000, refl_data, 
                            vmin=-32.0, vmax=94.5, cmap=refl_cmap, shading='auto')
        ax1.set_title(f"Reflectivity - {radar.elevation['data'][radar.get_slice(refl_sweep_index)].mean():.2f}° Tilt")
        ax1.set_xlabel('Distance East (km)')
        ax1.set_ylabel('Distance North (km)')
        ax1.set_aspect('equal')
        plt.colorbar(im1, ax=ax1, label='Reflectivity (dBZ)')
        
        # Plot velocity
        nyquist_vel = 28.0
        if "nyquist_velocity" in radar.instrument_parameters:
            nyq_data = radar.instrument_parameters["nyquist_velocity"]["data"]
            if len(nyq_data) > 0:
                nyquist_vel = nyq_data[0] if len(nyq_data) == 1 else nyq_data[vel_sweep_index]
        
        vel_range = min(30, nyquist_vel)  # FIXED: Use 30 instead of 65
        
        im2 = ax2.pcolormesh(x/1000, y/1000, vel_data, 
                            vmin=-vel_range, vmax=vel_range, cmap=vel_cmap, shading='auto')
        ax2.set_title(f"Velocity - {radar.elevation['data'][radar.get_slice(vel_sweep_index)].mean():.2f}° Tilt")
        ax2.set_xlabel('Distance East (km)')
        ax2.set_ylabel('Distance North (km)')
        ax2.set_aspect('equal')
        plt.colorbar(im2, ax=ax2, label='Velocity (m/s)')
        
        # Main title
        try:
            base_time_str = radar.time["units"].split("since ")[1]
            scan_time = datetime.strptime(base_time_str, "%Y-%m-%dT%H:%M:%SZ")
            radar_id = os.path.basename(file_path)[:4]
            main_title = f"{radar_id} - {scan_time.strftime('%B %d, %Y at %H:%M UTC')}"
        except:
            main_title = parse_filename_for_title(file_path)

        plt.suptitle(main_title, fontsize=24, fontweight='bold', y=0.95)
        
        # Attribution
        fig.text(0.5, 0.02, "Plotted by Sekai Chandra (@Sekai_WX) | Basic matplotlib rendering",
                 ha='center', fontsize=12, style='italic')
        
        plt.tight_layout()
        
        return fig
        
    except Exception as e:
        st.error(f"Error in basic radar plotting: {str(e)}")
        return None

def create_fallback_visualization(radar_id, radar_lat, radar_lon, filename):
    """Create a fallback visualization when PyART/CartoPy aren't available."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Parse time from filename
    try:
        date_str = filename[4:12]
        time_str = filename[13:19]
        dt = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        time_formatted = dt.strftime("%B %d, %Y at %H:%M UTC")
    except:
        time_formatted = "Unknown Time"
    
    # Create coordinate system around radar location
    extent = 2.0  # degrees
    
    ax.set_xlim(radar_lon - extent, radar_lon + extent)
    ax.set_ylim(radar_lat - extent, radar_lat + extent)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Plot radar location
    ax.plot(radar_lon, radar_lat, 'ro', markersize=15, label=f'{radar_id} Radar')
    
    # Add range rings
    for radius_miles in [50, 100, 150, 200]:
        radius_deg = radius_miles / 69.0
        circle = plt.Circle((radar_lon, radar_lat), radius_deg, 
                          fill=False, color='gray', alpha=0.5, linestyle='--')
        ax.add_patch(circle)
        ax.text(radar_lon + radius_deg, radar_lat, f'{radius_miles} mi', 
               fontsize=8, alpha=0.7)
    
    # Labels and title
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(f'{radar_id} NEXRAD Station\n{time_formatted}', fontsize=14, fontweight='bold')
    ax.legend()
    
    # Add info text
    info_text = f"""
Station: {radar_id}
Location: {radar_lat:.3f}°N, {radar_lon:.3f}°W
File: {filename}

Radar data file is available for download.
Full radar processing requires PyART and CartoPy.
    """
    
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    fig.text(0.5, 0.02, "NEXRAD Data Viewer | Data from NOAA/National Weather Service",
             ha='center', fontsize=10, style='italic')
    
    plt.tight_layout()
    return fig

def process_radar_file_robust(file_url, filename, radar_lat, radar_lon):
    """Process radar file with robust error handling and fallbacks."""
    if not PYART_AVAILABLE:
        st.warning("PyART not available - showing basic radar information instead.")
        return create_fallback_visualization(
            filename[:4], radar_lat, radar_lon, filename
        )
    
    temp_path = None
    try:
        # Download file
        temp_path = download_radar_file(file_url)
        
        # Read radar data
        radar = pyart.io.read(temp_path)

        if "reflectivity" not in radar.fields or "velocity" not in radar.fields:
            raise Exception("Required fields missing in radar file.")

        is_high_res = check_resolution(radar)
        
        sweep_info = get_sweep_info(radar)
        if not sweep_info:
            raise Exception("No valid sweeps found in radar file.")

        pairs = pair_sweeps(sweep_info, is_high_res=is_high_res)
        if not pairs:
            raise Exception("No paired sweeps found in radar file.")

        # Use the first pair
        refl_sweep, vel_sweep = pairs[0]

        # Perform velocity dealiasing
        simple_improved_dealias_velocity(radar, vel_sweep["sweep_index"])

        # Create plot based on available dependencies
        if CARTOPY_AVAILABLE:
            fig = plot_radar_data(
                radar, refl_sweep["sweep_index"], vel_sweep["sweep_index"],
                filename, radar_lat, radar_lon
            )
        else:
            # Use matplotlib-only plotting
            fig = plot_radar_data_basic(
                radar, refl_sweep["sweep_index"], vel_sweep["sweep_index"],
                filename, radar_lat, radar_lon
            )

        return fig

    except Exception as e:
        st.error(f"Error processing radar file: {str(e)}")
        return create_fallback_visualization(
            filename[:4], radar_lat, radar_lon, filename
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if 'radar' in locals():
            del radar
        gc.collect()

# Streamlit UI
st.title("NEXRAD Radar Data Viewer")
st.markdown("### High-Resolution Weather Radar Imagery")

st.markdown("""
Access NEXRAD radar data from the National Weather Service. Select a date and radar station 
to view reflectivity and velocity data with professional-quality visualization.
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Select Date & Location")
    
    # Date selection
    today = datetime.now().date()
    min_date = datetime(1991, 6, 1).date()  # NEXRAD started operation
    
    date_input = st.date_input(
        "Date", value=today, min_value=min_date, max_value=today)
    
    # Location selection
    location_method = st.radio(
        "Location Selection",
        ["Search by City/Place", "Select Radar Station"])
    
    if location_method == "Search by City/Place":
        location_input = st.text_input(
            "Enter city or place name",
            placeholder="e.g., Miami, Los Angeles, Chicago")
        
        radar_options = []
        selected_radar = None
        
        if location_input:
            with st.spinner("Finding nearby radars..."):
                try:
                    lat, lon = get_location_coordinates(location_input)
                    if lat and lon:
                        st.success(f"Found: {lat:.4f}°, {lon:.4f}°")
                        nearby_radars = get_closest_radars(lat, lon)
                        if nearby_radars:
                            radar_options = [(f"{r[0]} ({r[1]:.0f} miles)", r[0], r[2], r[3]) for r in nearby_radars[:10]]
                        else:
                            st.warning("No radars found within 230 miles of this location.")
                    else:
                        st.error("Location not found. Please try a different name.")
                except Exception as e:
                    st.error(f"Error geocoding location: {str(e)}")
    else:
        # Direct radar selection
        radar_dict = {f"{r[0]} - {r[1]:.2f}°N, {r[2]:.2f}°W": (r[0], r[1], r[2]) for r in RADAR_LIST}
        radar_options = [(k, v[0], v[1], v[2]) for k, v in radar_dict.items()]
    
    # Radar selection dropdown
    if radar_options:
        selected_option = st.selectbox(
            "Select Radar Station",
            options=[opt[0] for opt in radar_options],
            key="radar_select")
        
        if selected_option:
            selected_radar = next(opt for opt in radar_options if opt[0] == selected_option)
            radar_id, radar_lat, radar_lon = selected_radar[1], selected_radar[2], selected_radar[3]
            
            # Get available files for selected date and radar
            if date_input:
                with st.spinner("Loading available radar times..."):
                    file_times = get_nexrad_files_for_date(radar_id, date_input)
                
                if file_times:
                    st.success(f"Found {len(file_times)} radar scans")
                    
                    # Time selection
                    time_options = []
                    for file_time, url, filename in file_times:
                        time_str = file_time.strftime("%H:%M:%S UTC")
                        time_options.append((time_str, url, filename))
                    
                    selected_time = st.selectbox(
                        "Select Radar Scan Time",
                        options=[opt[0] for opt in time_options],
                        key="time_select")
                    
                    if selected_time:
                        selected_file = next(opt for opt in time_options if opt[0] == selected_time)
                        file_url = selected_file[1]
                        filename = selected_file[2]
                        
                        generate_button = st.button("Generate Radar Plot", type="primary")
                        
                        if generate_button:
                            with col2:
                                st.subheader("Radar Visualization")
                                with st.spinner("Processing radar data... This may take 2-3 minutes."):
                                    try:
                                        fig = process_radar_file_robust(file_url, filename, radar_lat, radar_lon)
                                        
                                        if fig:
                                            st.pyplot(fig, use_container_width=True)
                                            plt.close(fig)
                                            gc.collect()
                                            
                                            if all(dependency_status.values()):
                                                st.success("Full radar plot generated successfully!")
                                            else:
                                                st.info("Basic radar information displayed. Install PyART and CartoPy for full functionality.")
                                            
                                            st.info("Right-click on the image to save it to your device.")
                                        else:
                                            st.error("Failed to generate radar plot.")
                                            
                                    except Exception as e:
                                        st.error(f"Error generating radar plot: {str(e)}")
                                        
                                        # Show fallback
                                        st.info("Showing basic radar station information instead:")
                                        fallback_fig = create_fallback_visualization(radar_id, radar_lat, radar_lon, filename)
                                        st.pyplot(fallback_fig, use_container_width=True)
                                        plt.close(fallback_fig)
                else:
                    st.warning(f"No radar data available for {radar_id} on {date_input}")

with col2:
    st.subheader("Radar Visualization")
    if not st.session_state.get('radar_select') or not st.session_state.get('time_select'):
        st.info("Select a radar station and time to generate the plot.")
        
        # Information about radar data
        st.markdown("""
        **About NEXRAD Radar Data:**
        
        - **Reflectivity**: Shows precipitation intensity (dBZ scale)
        - **Velocity**: Shows wind movement toward/away from radar (m/s)
        - **Range**: Covers approximately 230-mile radius from each radar
        - **Resolution**: High-resolution data available from 2008+
        - **Updates**: New scans every 4-10 minutes during active weather
        
        The system automatically pairs reflectivity and velocity data from the 
        closest available scan times and applies velocity dealiasing for accurate 
        wind measurements.
        """)

# Information section
with st.expander("NEXRAD Radar Network Information"):
    st.markdown("""
    The **Next Generation Weather Radar (NEXRAD)** network consists of 160+ weather radar stations 
    across the United States, providing comprehensive weather monitoring capability.
    
    **Technical Specifications:**
    - **Frequency**: S-band (2.7-3.0 GHz)
    - **Range**: 230 nautical miles (460 km) maximum
    - **Resolution**: 250m range resolution, 0.5° beam width
    - **Products**: Reflectivity, velocity, spectrum width, and derived products
    
    **Data Quality Features:**
    - Dual-polarization capability (2013+ upgrades)
    - Velocity dealiasing for accurate wind measurements  
    - Automated quality control and clutter filtering
    - Super-resolution mode for enhanced detail
    
    **Coverage Areas:**
    - Continental United States
    - Alaska, Hawaii, and Puerto Rico
    - Selected overseas military installations
    
    Data is provided by the National Weather Service and archived by NOAA.
    """)

with st.expander("How to Read Radar Data"):
    st.markdown("""
    **Reflectivity (Left Panel):**
    - **Green/Blue**: Light precipitation (drizzle, light rain)
    - **Yellow**: Moderate precipitation  
    - **Orange/Red**: Heavy precipitation
    - **Purple/Magenta**: Very heavy precipitation or hail
    
    **Velocity (Right Panel):**
    - **Green colors**: Motion toward the radar
    - **Red colors**: Motion away from the radar
    - **Adjacent red/green**: Indicates rotation (possible tornado)
    - **Speed**: Measured in meters per second (m/s)
    
    **Understanding the Display:**
    - Radar beam travels in straight lines but Earth curves
    - Higher altitudes sampled at greater distances
    - Beam blockage may occur near mountains or tall structures
    - Range rings help estimate distance from radar site
    """)

st.markdown("---")
st.markdown("*Created by Sekai Chandra (@Sekai_WX) | Data from NOAA/National Weather Service*")