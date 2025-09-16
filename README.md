# NEXRAD Radar Data Viewer

A professional-quality Streamlit application for visualizing NEXRAD weather radar data from the National Weather Service. Access high-resolution reflectivity and velocity data from 160+ radar stations across the United States.

## Features

- **Comprehensive Radar Coverage**: Access data from all NEXRAD stations across the US
- **Location-Based Search**: Find radars by city/place name or select stations directly
- **Date Range**: Historical data from 1991 to present day
- **High-Quality Visualization**: Professional radar plots with proper colormaps
- **Velocity Dealiasing**: Advanced processing for accurate wind measurements
- **Dual-Product Display**: Side-by-side reflectivity and velocity visualization

## Installation

1. Clone this repository:
```bash
git clone <your-repo-url>
cd nexrad-radar-viewer
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Streamlit application:
```bash
streamlit run app.py
```

## Usage

1. **Select Date**: Choose any date from June 1991 to present
2. **Choose Location Method**:
   - Search by city/place name to find nearby radars
   - Or select directly from the radar station list
3. **Select Radar Station**: Pick from available stations within range
4. **Choose Scan Time**: Select from available radar scans for that date
5. **Generate Plot**: Click to create the radar visualization

## Data Sources

- **NEXRAD Data**: National Weather Service via NOAA
- **Geocoding**: OpenStreetMap via GeoPy
- **Visualization**: PyART (Python ARM Radar Toolkit)

## Technical Details

### Radar Products
- **Reflectivity**: Precipitation intensity (dBZ scale)
- **Velocity**: Radial wind component (m/s, dealiased)

### Processing Features
- Automatic sweep pairing for reflectivity and velocity
- Velocity dealiasing using region-based algorithms
- High-resolution and super-resolution data support
- Quality control and data validation

### Visualization
- Professional colormap matching NWS standards
- Geographic coordinate system with proper projections
- State boundaries, coastlines, and gridlines
- Automatic range scaling based on radar location

## System Requirements

- Python 3.8+
- 4GB+ RAM (for processing radar files)
- Internet connection (for data download)

## File Structure

```
nexrad-radar-viewer/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .gitignore         # Git ignore patterns
```

## Performance Notes

- Radar file downloads can take 1-3 minutes depending on file size
- Processing includes automatic velocity dealiasing which may take additional time
- Files are temporarily downloaded and automatically cleaned up after processing
- Caching is implemented for location lookups and file listings

## Limitations

- Data availability depends on NOAA archive status
- Some historical dates may have limited or no data
- Download speeds depend on NOAA server performance
- Maximum range: 230 miles from radar station

## Contributing

This project is based on the original radar processing code by Sekai Chandra (@Sekai_WX). 

To contribute:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

This project is for educational and research purposes. NEXRAD data is provided by NOAA/National Weather Service and is in the public domain.

## Troubleshooting

**Common Issues:**

1. **"No data available"**: Check if the selected date falls within radar operation periods
2. **Slow downloads**: NOAA servers can be slow during peak usage
3. **Processing errors**: Some older or corrupted files may fail - try a different time
4. **Memory issues**: Close other applications if processing fails

**Getting Help:**
- Check the NOAA radar status page for known outages
- Verify date is within available range (post-1991)
- Try different radar stations if one fails

## Acknowledgments

- **Sekai Chandra (@Sekai_WX)**: Original radar processing algorithms
- **PyART Development Team**: Python radar toolkit
- **NOAA/National Weather Service**: NEXRAD data provision
- **Streamlit Team**: Web application framework