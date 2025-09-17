import streamlit as st
import pyart
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import tempfile
import os
import re
from datetime import datetime
from matplotlib.colors import ListedColormap
import traceback

# Page config
st.set_page_config(
    page_title="NEXRAD Radar Viewer",
    page_icon="⛈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add some CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stFileUploader {
        margin-bottom: 1rem;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# NEXRAD radar stations database
RADAR_STATIONS = {
    "KBMX": {"name": "Birmingham, AL", "lat": 33.172, "lon": -86.770},
    "KEOX": {"name": "Fort Rucker, AL", "lat": 31.460, "lon": -85.459},
    "KHTX": {"name": "Huntsville, AL", "lat": 34.931, "lon": -86.084},
    "KMXX": {"name": "Montgomery, AL", "lat": 32.537, "lon": -85.790},
    "KMOB": {"name": "Mobile, AL", "lat": 30.679, "lon": -88.240},
    "KSRX": {"name": "Fort Smith, AR", "lat": 35.290, "lon": -94.362},
    "KLZK": {"name": "Little Rock, AR", "lat": 34.836, "lon": -92.262},
    "KFSX": {"name": "Flagstaff, AZ", "lat": 34.574, "lon": -111.198},
    "KIWA": {"name": "Phoenix, AZ", "lat": 33.289, "lon": -111.670},
    "KEMX": {"name": "Tucson, AZ", "lat": 31.894, "lon": -110.630},
    "KYUX": {"name": "Yuma, AZ", "lat": 32.495, "lon": -114.656},
    "KBBX": {"name": "Beale AFB, CA", "lat": 39.496, "lon": -121.632},
    "KEYX": {"name": "Edwards AFB, CA", "lat": 35.098, "lon": -117.561},
    "KBHX": {"name": "Eureka, CA", "lat": 40.499, "lon": -124.292},
    "KVTX": {"name": "Ventura, CA", "lat": 34.412, "lon": -119.179},
    "KDAX": {"name": "Sacramento, CA", "lat": 38.501, "lon": -121.678},
    "KNKX": {"name": "San Diego, CA", "lat": 32.919, "lon": -117.041},
    "KMUX": {"name": "San Francisco, CA", "lat": 37.155, "lon": -121.898},
    "KHNX": {"name": "San Joaquin Valley, CA", "lat": 36.314, "lon": -119.632},
    "KSOX": {"name": "Santa Ana Mountains, CA", "lat": 33.818, "lon": -117.636},
    "KVBX": {"name": "Vandenberg AFB, CA", "lat": 34.839, "lon": -120.398},
    "KFTG": {"name": "Denver, CO", "lat": 39.786, "lon": -104.546},
    "KGJX": {"name": "Grand Junction, CO", "lat": 39.062, "lon": -108.214},
    "KPUX": {"name": "Pueblo, CO", "lat": 38.460, "lon": -104.181},
    "KDOX": {"name": "Dover AFB, DE", "lat": 38.826, "lon": -75.440},
    "KEVX": {"name": "Eglin AFB, FL", "lat": 30.565, "lon": -85.922},
    "KJAX": {"name": "Jacksonville, FL", "lat": 30.485, "lon": -81.702},
    "KBYX": {"name": "Key West, FL", "lat": 24.597, "lon": -81.703},
    "KMLB": {"name": "Melbourne, FL", "lat": 28.113, "lon": -80.654},
    "KAMX": {"name": "Miami, FL", "lat": 25.611, "lon": -80.413},
    "KTLH": {"name": "Tallahassee, FL", "lat": 30.398, "lon": -84.329},
    "KTBW": {"name": "Tampa, FL", "lat": 27.705, "lon": -82.402},
    "KFFC": {"name": "Atlanta, GA", "lat": 33.363, "lon": -84.566},
    "KVAX": {"name": "Moody AFB, GA", "lat": 30.890, "lon": -83.002},
    "KJGX": {"name": "Robins AFB, GA", "lat": 32.675, "lon": -83.351},
    # Add more stations as needed...
}

def create_custom_reflectivity_colormap():
    """Create custom reflectivity colormap matching the original script"""
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
    colors_rgb = [(r, g, b) for _, r, g, b in color_data]
    return dbz_values, colors_rgb

def create_custom_velocity_colormap():
    """Create custom velocity colormap matching the original script"""
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
    
    vel_values = np.array([x[0] for x in color_data])
    colors_rgb = [(r, g, b) for _, r, g, b in color_data]
    return vel_values, colors_rgb

def parse_nexrad_filename(filename):
    """Parse NEXRAD filename to extract radar station, date, and time"""
    # Remove path and extension
    basename = os.path.basename(filename)
    if basename.endswith('.gz'):
        basename = basename[:-3]
    
    # Pattern: KXXXYYYYMMDDHHMMSS
    pattern = r'^(K[A-Z]{3})(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})'
    match = re.match(pattern, basename)
    
    if match:
        radar_id, year, month, day, hour, minute, second = match.groups()
        try:
            dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))
            return {
                'radar_id': radar_id,
                'datetime': dt,
                'station_info': RADAR_STATIONS.get(radar_id, {'name': 'Unknown', 'lat': 0, 'lon': 0})
            }
        except ValueError:
            pass
    
    return None

def detect_data_age(radar):
    """Detect if radar data is old (low-res) or new (high-res)"""
    try:
        sweep_index = 0
        sweep_slice = radar.get_slice(sweep_index)

        # Use velocity field to check data shape
        if 'velocity' in radar.fields:
            data_shape = radar.fields["velocity"]["data"][sweep_slice].shape
        elif 'reflectivity' in radar.fields:
            data_shape = radar.fields["reflectivity"]["data"][sweep_slice].shape
        else:
            return "new"

        total_gates = data_shape[0] * data_shape[1]

        # Check base year
        base_year = None
        try:
            base_time_str = radar.time["units"].split("since ")[1]
            base_year = datetime.strptime(base_time_str, "%Y-%m-%dT%H:%M:%SZ").year
        except Exception:
            base_year = None

        # Check super resolution flag
        is_super_res = radar.instrument_parameters.get("super_resolution", {}).get("data", [0])[0] == 1

        # Apply original logic
        if base_year is not None and base_year < 2008:
            return "old"

        gate_threshold = 1000000
        if total_gates >= gate_threshold or is_super_res:
            return "new"
        else:
            return "old"

    except Exception as e:
        st.warning(f"Error detecting data age: {e}, defaulting to new")
        return "new"

def advanced_velocity_dealiasing_new_data(radar, vel_sweep):
    """Advanced dealiasing for new data with tornadic signature handling"""
    try:
        # Get Nyquist velocity
        nyq = 28.0
        if 'nyquist_velocity' in radar.instrument_parameters:
            nyq_data = radar.instrument_parameters['nyquist_velocity']['data']
            sweep_slice = radar.get_slice(vel_sweep)
            if len(nyq_data) > 0:
                if len(nyq_data) > sweep_slice.start:
                    nyq_temp = nyq_data[sweep_slice.start]
                else:
                    nyq_temp = nyq_data[0]
                if nyq_temp > 0 and nyq_temp < 100:
                    nyq = float(nyq_temp)

        # Calculate velocity texture
        vel_texture = pyart.retrieve.calculate_velocity_texture(radar, vel_field='velocity')
        radar.add_field('vel_texture', vel_texture, replace_existing=True)

        # Create gate filter for non-tornadic areas
        gfilter_nontornadic = pyart.filters.GateFilter(radar)
        gfilter_nontornadic.exclude_above('vel_texture', 5)

        # Dealias non-tornadic velocity field
        corrected_vel_nontornadic = pyart.correct.dealias_region_based(
            radar,
            vel_field="velocity",
            nyquist_vel=nyq,
            gatefilter=gfilter_nontornadic
        )
        radar.add_field('dealiased_nontornadic', corrected_vel_nontornadic, replace_existing=True)

        # Create gate filter for tornadic signatures
        gfilter_tornadic = pyart.filters.GateFilter(radar)
        gfilter_tornadic.exclude_below('reflectivity', 30)
        gfilter_tornadic.exclude_below('vel_texture', 5)

        # Dealias tornadic signatures
        corrected_vel_temp = pyart.correct.dealias_region_based(
            radar,
            vel_field="velocity",
            nyquist_vel=nyq
        )
        radar.add_field('temp_dealiased_velocity', corrected_vel_temp, replace_existing=True)

        # Apply phase unwrapping to tornadic areas
        corrected_vel_tornadic = pyart.correct.dealias_unwrap_phase(
            radar,
            vel_field='temp_dealiased_velocity',
            gatefilter=gfilter_tornadic
        )
        radar.add_field('dealiased_tornadic', corrected_vel_tornadic, replace_existing=True)

        # Combine dealiased fields
        nontornadic = radar.fields['dealiased_nontornadic']['data']
        tornadic = radar.fields['dealiased_tornadic']['data']

        dealiased = np.ma.masked_invalid(nontornadic)
        dealiased = np.ma.where(dealiased.mask, tornadic, dealiased)
        radar.add_field_like('dealiased_nontornadic', 'corrected_velocity', dealiased)

        return True

    except Exception as e:
        st.warning(f"Advanced dealiasing failed: {e}")
        return False

def simple_velocity_dealiasing_old_data(radar, vel_sweep):
    """Simple dealiasing for old data"""
    try:
        # Get Nyquist velocity
        nyq = 28.0
        if 'nyquist_velocity' in radar.instrument_parameters:
            nyq_data = radar.instrument_parameters['nyquist_velocity']['data']
            sweep_slice = radar.get_slice(vel_sweep)
            if len(nyq_data) > 0:
                if len(nyq_data) > sweep_slice.start:
                    nyq_temp = nyq_data[sweep_slice.start]
                else:
                    nyq_temp = nyq_data[0]
                if nyq_temp > 0 and nyq_temp < 100:
                    nyq = float(nyq_temp)

        # Simple region-based dealiasing
        velocity_dealiased = pyart.correct.dealias_region_based(
            radar,
            vel_field="velocity",
            nyquist_vel=nyq,
            centered=True,
            keep_original=True,
            gatefilter=False
        )

        radar.add_field("corrected_velocity", velocity_dealiased, replace_existing=True)
        radar.fields["corrected_velocity"]["units"] = "m/s"

        return True

    except Exception as e:
        st.warning(f"Simple dealiasing failed: {e}")
        return False

def find_best_sweep(radar, field_name):
    """Find the best sweep with most valid data points"""
    for sweep_idx in range(radar.nsweeps):
        sweep_slice = radar.get_slice(sweep_idx)
        field_data = radar.fields[field_name]['data'][sweep_slice]
        valid_points = (~field_data.mask).sum() if hasattr(field_data, 'mask') else len(field_data.flatten())
        if valid_points > 1000:
            return sweep_idx
    return 0

def create_plotly_radar_plot(radar, field_name, sweep_idx, title, color_scale, vmin, vmax, max_range=250, show_range_rings=True):
    """Create interactive Plotly radar plot"""
    # Get data for the sweep
    sweep_slice = radar.get_slice(sweep_idx)
    field_data = radar.fields[field_name]['data'][sweep_slice]
    
    # Get radar coordinates
    x, y = pyart.core.antenna_to_cartesian(
        radar.range['data'],
        radar.azimuth['data'][sweep_slice],
        radar.elevation['data'][sweep_slice]
    )
    
    # Convert to km
    x = x / 1000.0
    y = y / 1000.0
    
    # Create the plot
    fig = go.Figure()
    
    # Add the radar data as a heatmap
    fig.add_trace(go.Heatmap(
        x=x[0, :],
        y=y[:, 0],
        z=field_data,
        colorscale=color_scale,
        zmin=vmin,
        zmax=vmax,
        showscale=True,
        hovertemplate='<b>%{fullData.name}</b><br>' +
                      'X: %{x:.1f} km<br>' +
                      'Y: %{y:.1f} km<br>' +
                      'Value: %{z:.1f}<br>' +
                      '<extra></extra>',
        name=title
    ))
    
    # Add range rings if requested
    if show_range_rings:
        theta = np.linspace(0, 2*np.pi, 100)
        ring_distances = np.arange(50, max_range + 1, 50)
        for r in ring_distances:
            x_ring = r * np.cos(theta)
            y_ring = r * np.sin(theta)
            fig.add_trace(go.Scatter(
                x=x_ring, y=y_ring,
                mode='lines',
                line=dict(color='rgba(255,255,255,0.3)', width=1, dash='dash'),
                showlegend=False,
                hoverinfo='skip',
                name=f'{r} km range'
            ))
    
    # Configure layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            font=dict(size=16)
        ),
        xaxis=dict(
            title='Distance East (km)',
            range=[-max_range, max_range],
            scaleanchor='y',
            scaleratio=1,
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)'
        ),
        yaxis=dict(
            title='Distance North (km)',
            range=[-max_range, max_range],
            showgrid=True,
            gridcolor='rgba(255,255,255,0.1)'
        ),
        width=800,
        height=800,
        template='plotly_dark',
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

# Streamlit App
def main():
    st.title("NEXRAD Radar Data Viewer")
    st.markdown("Upload a NEXRAD Level II file to visualize reflectivity and velocity data with interactive zooming.")
    
    # Add info about the app
    with st.expander("About this application"):
        st.markdown("""
        This application processes NEXRAD Level II radar data files and creates interactive visualizations of:
        - **Reflectivity data**: Shows precipitation intensity (dBZ scale)
        - **Velocity data**: Shows radial wind speeds with advanced dealiasing (MPH scale)
        
        **Supported file formats**: .gz, .ar2v, .Z
        
        **Features**:
        - Automatic radar station detection from filename
        - Advanced velocity dealiasing for high-resolution data
        - Interactive zoom and pan capabilities
        - Custom meteorological color scales
        
        **File naming convention**: KXXXYYYYMMDDHHMMSS (e.g., KHTX20240315123000.gz)
        """)

    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # File upload with better help text
        uploaded_file = st.file_uploader(
            "Choose NEXRAD file",
            type=['gz', 'ar2v', 'Z'],
            help="Upload NEXRAD Level II files. Maximum file size: 200MB"
        )
        
        # Display mode selection
        display_mode = st.radio(
            "Display Mode",
            ["Reflectivity", "Velocity", "Both"],
            index=0,
            help="Choose which radar products to display"
        )
        
        # Advanced options
        with st.expander("Advanced Options"):
            max_range = st.slider("Maximum Range (km)", 50, 300, 250, 25)
            show_range_rings = st.checkbox("Show Range Rings", True)

    if uploaded_file is not None:
        try:
            # Parse filename for radar info
            file_info = parse_nexrad_filename(uploaded_file.name)
            
            if file_info:
                st.sidebar.success("File Information Detected")
                st.sidebar.write(f"**Radar Station:** {file_info['radar_id']}")
                st.sidebar.write(f"**Location:** {file_info['station_info']['name']}")
                st.sidebar.write(f"**Date/Time:** {file_info['datetime'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                st.sidebar.write(f"**Coordinates:** {file_info['station_info']['lat']:.3f}°N, {file_info['station_info']['lon']:.3f}°W")
            else:
                st.sidebar.warning("Could not parse filename for radar information")
            
            # Save uploaded file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.gz') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Load radar data
            with st.spinner("Loading radar data..."):
                radar = pyart.io.read_nexrad_archive(tmp_file_path)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            # Display available fields
            st.sidebar.write("**Available Fields:**")
            for field in radar.fields.keys():
                st.sidebar.write(f"- {field}")
            
            # Check for required fields
            has_reflectivity = 'reflectivity' in radar.fields
            has_velocity = 'velocity' in radar.fields
            
            if not has_reflectivity:
                st.error("Reflectivity field not found in radar data.")
                return
            
            # Find best sweeps
            refl_sweep = find_best_sweep(radar, 'reflectivity')
            vel_sweep = find_best_sweep(radar, 'velocity') if has_velocity else 0
            
            # Detect data age and process velocity
            data_age = detect_data_age(radar)
            st.sidebar.write(f"**Data Type:** {data_age.upper()}")
            
            dealiased_available = False
            
            if has_velocity:
                with st.spinner("Processing velocity data..."):
                    if data_age == "new":
                        success = advanced_velocity_dealiasing_new_data(radar, vel_sweep)
                        if not success:
                            success = simple_velocity_dealiasing_old_data(radar, vel_sweep)
                    else:
                        success = simple_velocity_dealiasing_old_data(radar, vel_sweep)
                    
                    if success:
                        dealiased_available = True
                        # Convert to MPH
                        velocity_mph = radar.fields["corrected_velocity"].copy()
                        velocity_mph['data'] = velocity_mph['data'] * 2.237
                        velocity_mph['units'] = 'MPH'
                        radar.add_field("corrected_velocity_mph", velocity_mph, replace_existing=True)
                    else:
                        st.warning("Using original velocity data")
                        radar.add_field("corrected_velocity", radar.fields["velocity"], replace_existing=True)
                        velocity_mph = radar.fields["corrected_velocity"].copy()
                        velocity_mph['data'] = velocity_mph['data'] * 2.237
                        velocity_mph['units'] = 'MPH'
                        radar.add_field("corrected_velocity_mph", velocity_mph, replace_existing=True)
                        dealiased_available = True
            
            # Create colormaps
            dbz_values, refl_colors = create_custom_reflectivity_colormap()
            vel_values, vel_colors = create_custom_velocity_colormap()
            
            # Convert to Plotly colorscales
            refl_colorscale = [[i/(len(refl_colors)-1), f'rgb({r},{g},{b})'] for i, (r, g, b) in enumerate(refl_colors)]
            vel_colorscale = [[i/(len(vel_colors)-1), f'rgb({r},{g},{b})'] for i, (r, g, b) in enumerate(vel_colors)]
            
            # Display plots based on mode
            if display_mode == "Reflectivity" or display_mode == "Both":
                st.subheader(f"Reflectivity (Sweep {refl_sweep}) - {data_age.upper()} Data")
                
                with st.spinner("Generating reflectivity plot..."):
                    refl_fig = create_plotly_radar_plot(
                        radar, 'reflectivity', refl_sweep,
                        f"NEXRAD Reflectivity (Sweep {refl_sweep}) - dBZ",
                        refl_colorscale, -32, 94.5, max_range, show_range_rings
                    )
                    st.plotly_chart(refl_fig, use_container_width=True)
                
                # Show statistics
                sweep_slice = radar.get_slice(refl_sweep)
                refl_data = radar.fields['reflectivity']['data'][sweep_slice]
                valid_data = refl_data[~refl_data.mask] if hasattr(refl_data, 'mask') else refl_data
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Max dBZ", f"{valid_data.max():.1f}")
                with col2:
                    st.metric("Mean dBZ", f"{valid_data.mean():.1f}")
                with col3:
                    st.metric("Min dBZ", f"{valid_data.min():.1f}")
                with col4:
                    st.metric("Valid Gates", f"{len(valid_data):,}")
            
            if (display_mode == "Velocity" or display_mode == "Both") and has_velocity and dealiased_available:
                st.subheader(f"Dealiased Velocity (Sweep {vel_sweep}) - {data_age.upper()} Data")
                
                with st.spinner("Generating velocity plot..."):
                    vel_fig = create_plotly_radar_plot(
                        radar, 'corrected_velocity_mph', vel_sweep,
                        f"Dealiased Velocity (Sweep {vel_sweep}) - MPH",
                        vel_colorscale, -127, 127, max_range, show_range_rings
                    )
                    st.plotly_chart(vel_fig, use_container_width=True)
                
                # Show velocity statistics
                sweep_slice = radar.get_slice(vel_sweep)
                vel_data = radar.fields['corrected_velocity_mph']['data'][sweep_slice]
                valid_data = vel_data[~vel_data.mask] if hasattr(vel_data, 'mask') else vel_data
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Max Velocity", f"{valid_data.max():.1f} MPH")
                with col2:
                    st.metric("Mean Velocity", f"{valid_data.mean():.1f} MPH")
                with col3:
                    st.metric("Min Velocity", f"{valid_data.min():.1f} MPH")
                with col4:
                    st.metric("Valid Gates", f"{len(valid_data):,}")
                    
            elif display_mode == "Velocity" or display_mode == "Both":
                st.warning("Velocity data not available or processing failed.")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            with st.expander("Show detailed error information"):
                st.code(traceback.format_exc())
    
    else:
        st.info("Please upload a NEXRAD Level II file to begin.")
        
        # Show example of expected filename format
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Expected File Format
            NEXRAD Level II files should follow the naming convention:
            - **Format:** `KXXXYYYYMMDDHHMMSS.gz` (or .ar2v, .Z)
            - **Example:** `KHTX20240315123000.gz`
            - **Where:**
              - `KXXX` = Radar station ID (e.g., KHTX)
              - `YYYY` = Year (e.g., 2024)
              - `MM` = Month (e.g., 03)
              - `DD` = Day (e.g., 15)
              - `HH` = Hour (e.g., 12)
              - `MM` = Minute (e.g., 30)
              - `SS` = Second (e.g., 00)
            """)
        
        with col2:
            st.markdown("""
            ### Sample Radar Stations
            - **KHTX** - Huntsville, AL
            - **KBMX** - Birmingham, AL
            - **KFFC** - Atlanta, GA
            - **KJAX** - Jacksonville, FL
            - **KTLX** - Norman, OK
            - **KDDC** - Dodge City, KS
            - **KLOT** - Chicago, IL
            - **KPBZ** - Pittsburgh, PA
            
            *Data files can be downloaded from NOAA's NEXRAD archive.*
            """)
        
        # Add footer with technical info
        st.markdown("---")
        st.markdown("""
        **Technical Information:**
        - Supports both high-resolution (post-2008) and low-resolution (pre-2008) data
        - Advanced velocity dealiasing with tornadic signature detection
        - Custom meteorological color scales for accurate interpretation
        - Built with PyART, Plotly, and Streamlit
        """)

if __name__ == "__main__":
    main()