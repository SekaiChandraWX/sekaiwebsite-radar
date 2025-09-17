import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
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

# Set page config
st.set_page_config(
    page_title="NEXRAD Radar Viewer", 
    page_icon="📡",
    layout="wide"
)

# Suppress matplotlib font debugging messages
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)

# Full radar list with ID, latitude, longitude
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
    ("KCYS", 41.152, -104.806), ("KRIW", 43.066, -108.477), ("KHDC", 30.519, -90.407), 
    ("KJAN", 32.319, -90.077)
]

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
            filename = url.split('/')[-1]
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

def create_simple_radar_plot(radar_id, radar_lat, radar_lon, filename):
    """Create a simple radar plot showing station location and basic info."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Parse time from filename
    try:
        date_str = filename[4:12]
        time_str = filename[13:19]
        dt = datetime.strptime(date_str + time_str, "%Y%m%d%H%M%S")
        time_formatted = dt.strftime("%B %d, %Y at %H:%M UTC")
    except:
        time_formatted = "Unknown Time"
    
    # Create simple map-like visualization
    # Set up coordinate system around radar location
    extent = 2.0  # degrees
    
    ax.set_xlim(radar_lon - extent, radar_lon + extent)
    ax.set_ylim(radar_lat - extent, radar_lat + extent)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Plot radar location
    ax.plot(radar_lon, radar_lat, 'ro', markersize=15, label=f'{radar_id} Radar')
    
    # Add range rings (in degrees, approximate)
    for radius_miles in [50, 100, 150, 200]:
        # Convert miles to degrees (rough approximation)
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

Note: This is a simplified view showing radar location.
Full radar data processing requires additional dependencies
not available in this cloud deployment.
    """
    
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Attribution
    fig.text(0.5, 0.02, "NEXRAD Data Viewer | Data from NOAA/National Weather Service",
             ha='center', fontsize=10, style='italic')
    
    plt.tight_layout()
    return fig

# Streamlit UI
st.title("NEXRAD Radar Data Viewer")
st.markdown("### Weather Radar Station Locator and File Browser")

st.markdown("""
**Note**: This is a simplified version for cloud deployment. It shows radar station locations 
and available data files. Full radar data visualization requires additional dependencies 
that are not available in this environment.
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Select Date & Location")
    
    # Date selection
    today = datetime.now().date()
    min_date = datetime(1991, 6, 1).date()
    
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
            
            st.info(f"Selected: {radar_id} at {radar_lat:.3f}°N, {radar_lon:.3f}°W")
            
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
                        
                        generate_button = st.button("Show Radar Info", type="primary")
                        
                        if generate_button:
                            with col2:
                                st.subheader("Radar Station Information")
                                fig = create_simple_radar_plot(radar_id, radar_lat, radar_lon, filename)
                                st.pyplot(fig, use_container_width=True)
                                plt.close(fig)
                                
                                st.success("Radar station information displayed!")
                                
                                # Show file info
                                st.subheader("Available Data File")
                                st.write(f"**Filename:** {filename}")
                                st.write(f"**Download URL:** {file_url}")
                                st.write(f"**File Size:** Available for download from NOAA")
                                
                else:
                    st.warning(f"No radar data available for {radar_id} on {date_input}")

with col2:
    if not st.session_state.get('radar_select') or not st.session_state.get('time_select'):
        st.subheader("Radar Information Display")
        st.info("Select a radar station and time to view information.")
        
        # Information about radar data
        st.markdown("""
        **About NEXRAD Radar Data:**
        
        - **Network**: 160+ weather radar stations across the United States
        - **Coverage**: 230-mile radius per station
        - **Products**: Reflectivity, velocity, spectrum width
        - **Resolution**: 250m range resolution, 0.5° beam width
        - **Updates**: New scans every 4-10 minutes during active weather
        
        **This Simplified Version Provides:**
        - Radar station locations and basic information
        - Available data file listings by date
        - Direct download links to NOAA data archive
        - Station coverage area visualization
        """)

# Information section
with st.expander("NEXRAD Network Information"):
    st.markdown("""
    The **Next Generation Weather Radar (NEXRAD)** network provides comprehensive weather monitoring 
    across the United States and territories.
    
    **Network Statistics:**
    - **Total Stations**: 160+ operational radars
    - **Coverage**: Continental US, Alaska, Hawaii, Puerto Rico
    - **Operational Since**: 1991 (first installations)
    - **Upgrade Completed**: 2013 (dual-polarization)
    
    **Technical Specifications:**
    - **Frequency**: S-band (2.7-3.0 GHz)
    - **Antenna**: 8.5-meter parabolic dish
    - **Power**: 750 kilowatts peak
    - **Range**: 460 km (248 nautical miles)
    
    **Data Archive:**
    - Historical data available from 1991
    - Real-time data updated every 4-10 minutes
    - Multiple data products and resolution levels
    - Free access via NOAA data services
    """)

with st.expander("Cloud Deployment Limitations"):
    st.markdown("""
    **Why This Version is Simplified:**
    
    This cloud deployment uses a simplified interface due to dependency limitations:
    
    **Missing Dependencies:**
    - **PyART**: Advanced radar data processing toolkit
    - **CartoPy**: Geographic projections and mapping
    - **Complex NetCDF**: Full radar file processing
    
    **What This Version Provides:**
    - Radar station location finder
    - Available data file browser
    - Basic station information display
    - Direct links to download radar files
    
    **For Full Functionality:**
    Run the complete application locally with all dependencies installed, 
    or use a more capable cloud platform that supports scientific Python packages.
    
    **Local Installation:**
    ```
    pip install arm-pyart cartopy matplotlib numpy requests beautifulsoup4 geopy
    ```
    """)

st.markdown("---")
st.markdown("*NEXRAD Data Viewer | Data from NOAA/National Weather Service*")