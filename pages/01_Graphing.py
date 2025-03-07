import streamlit as st
st.set_page_config(layout="wide", page_title="Topography Viewer") # Must be the first Streamlit command

if 'temp_files' not in st.session_state: # Initialize session states
    st.session_state.temp_files = []
if 'location_data' not in st.session_state:
    st.session_state.location_data = {
        'center_point': {
            'lat': None,
            'lon': None
        },
        'location': None,
        'scale': None,  # elevation
        'city_info': None,
        'bounds': None,
        'map_object': None  # Add storage for the map object itself
    }

# if 'map_object' not in st.session_state:
#     st.session_state.map_object = None
# if 'last_map_key' not in st.session_state:
#     st.session_state.last_map_key = None
if 'elevation' not in st.session_state:
    st.session_state.elevation = None
if 'data' not in st.session_state:
    st.session_state.data = None
if 'current_tiff_path' not in st.session_state:
    st.session_state.current_tiff_path = None
if 'needs_processing' not in st.session_state:
    st.session_state.needs_processing = False

# Function to clean up old temporary files
def cleanup_old_temp_files():
    for file_path in st.session_state.temp_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error removing temp file {file_path}: {str(e)}")
    st.session_state.temp_files = []
# st.write('st.session_state.temp_files', st.session_state.temp_files)
# st.write('st.session_state.current_tiff_path', st.session_state.current_tiff_path)
# st.write('st.session_state.needs_processing', st.session_state.needs_processing)

from components.sidebar import show_sidebar # Import sidebar
show_sidebar()

from src.topography.graph_types.terrain_3d import create_3d_plot, create_adjusted_3d_plot, downsample_for_3d
from src.topography.graph_types.ridge_plots import create_ridge_plot_optimized, create_adjusted_ridge_plot
from src.topography.graph_types.dem_plots import create_dem_plot, create_adjusted_dem_plot
from src.map_utils.map_operations import create_map, get_map_parameters
from src.weather.get_weather import get_weather_data
from src.config.data_source_config import get_data_source, get_base_path
from src.data_sources.file_parseing import combine_tiff_files, calculate_zoom_bounds
from src.database.db_utils import (
    get_all_states, 
    get_cities_in_state, 
    get_city_info,
    get_city_zipcodes,
    get_city_ips
)
from src.topography.topography_operations import (
    load_and_downsample_tiff,
    load_and_resize,
    clamp_bounds
)
from streamlit_folium import st_folium
from dotenv import load_dotenv
load_dotenv() # Load environment variables

import matplotlib.pyplot as plt
import pandas as pd
import tempfile
import folium
import gc
import os
import threading
from PIL import Image
import io
from tqdm import tqdm
from src.satellite.get_satellite import get_satellite_image
import cv2




















# Cache the database queries
@st.cache_data
def load_states():
    return get_all_states()

@st.cache_data
def load_cities(state):
    return get_cities_in_state(state)

@st.cache_data
def load_city_info(city, state):
    return get_city_info(city, state)


















st.title("Topography Viewer")









# Create three equal-width columns
col1, col2, col3 = st.columns(3)
# Load and resize images to be the same size
target_width = 400  # You can adjust this value
target_height = 300  # Set a fixed height for all images
# Function to resize image to fixed dimensions
def load_and_resize(image_path, width, height):
    img = Image.open(image_path)
    return img.resize((width, height))
# Display images with use_container_width=True to make them fill their columns
with col1:
    img1 = load_and_resize('images/left.png', target_width, target_height)
    st.image(img1, use_container_width=True)
with col2:
    img2 = load_and_resize('images/right.png', target_width, target_height)
    st.image(img2, use_container_width=True)
with col3:
    img3 = load_and_resize('images/bottom.png', target_width, target_height)
    st.image(img3, use_container_width=True)







# Initialize data source
print("Initializing data source...")  # Debug print
data_source = get_data_source('mounted_s3')  # Explicitly use mounted_s3 source
print(f"Data source type: {type(data_source).__name__}")  # Debug print
# Initialize location_data and combined_tiff_path
location_data = None
combined_tiff_path = None












# Graph selection
st.header("Select Visualizations")
checkbox_options = {
    'Satellite View': st.checkbox('Satellite View', value=False),
    'Street View': st.checkbox('Street View', value=True),
    'DEM Graph': st.checkbox('DEM Graph', value=True),
    'Ridge Graph': st.checkbox('Ridge Graph', value=False),
    '3D Graph': st.checkbox('3D Graph', value=False),
}

# Get selected options
selected_graphs = [option for option, state in checkbox_options.items() if state]









# Location selection UI
st.write("### Select Location Method")
input_method = st.radio(
    "Choose input method:",
    ["City Selection", "Single Point with Scale"]
)

# City selection logic
if input_method == "City Selection":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        states = load_states()
        state = st.selectbox("Select State", options=states, key='state_select')
        
    with col2:
        if state:
            cities = load_cities(state)
            city = st.selectbox("Select City", options=cities, key='city_select')
            
    with col3:
        elevation = st.number_input("Elevation (meters)", min_value=100, max_value=1000, value=500, key='elevation_input')
   
    if st.button("Get City Data", use_container_width=True):
        # Clear all previous data
        cleanup_old_temp_files()
        st.session_state.data = None
        st.session_state.bounds = None
        st.session_state.location_data['map_object'] = None
        
        city_data = load_city_info(city, state)
        if city_data and city_data['latitude'] and city_data['longitude']:
            # Update session state with all location data
            st.session_state.location_data.update({
                'center_point': {
                    'lat': city_data['latitude'],
                    'lon': city_data['longitude']
                },
                'location': f"{city}, {state}",  # Set the location
                'lat': city_data['latitude'],  # Add direct lat/lon access
                'lon': city_data['longitude'],
                'scale': elevation,
                'city_info': city_data,
                'bounds': calculate_zoom_bounds(city_data['latitude'], city_data['longitude'], elevation),
                'map_object': None
            })
            
            # Create temporary file path
            temp_dir = tempfile.gettempdir()
            st.session_state.current_tiff_path = os.path.join(temp_dir, f"{city}_{state}_combined.tif")
            st.session_state.temp_files.append(st.session_state.current_tiff_path)
            st.session_state.needs_processing = True
        else:
            st.error("No coordinate data available for this city.")

# Single point with scale selection
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        lat = st.number_input("Latitude", value=40.73)
    with col2:
        lon = st.number_input("Longitude", value=-73.93)
    with col3:
        elevation = st.number_input("Elevation (meters)", min_value=100, max_value=1000, value=500)

    if st.button("Submit Point", use_container_width=True):
        # Clear all previous data
        cleanup_old_temp_files()
        st.session_state.data = None
        st.session_state.bounds = None
        st.session_state.location_data['map_object'] = None
        
        # Update session state with point data
        st.session_state.location_data.update({
            'center_point': {
                'lat': lat,
                'lon': lon
            },
            'location': f"({lat:.4f}°, {lon:.4f}°)",  # Set the location
            'lat': lat,  # Add direct lat/lon access
            'lon': lon,
            'scale': elevation,
            'city_info': None,
            'bounds': calculate_zoom_bounds(lat, lon, elevation),
            'map_object': None
        })
        
        # Create temporary file path
        temp_dir = tempfile.gettempdir()
        st.session_state.current_tiff_path = os.path.join(temp_dir, f"point_{lat}_{lon}_combined.tif")
        st.session_state.temp_files.append(st.session_state.current_tiff_path)
        st.session_state.needs_processing = True
        
        # Force rerun to process the new data
        # st.rerun()










# Modify the information panel section to include zip codes and IPs
if (st.session_state.location_data['location'] is not None and 
    st.session_state.location_data['city_info'] is not None):
    
    # Get weather data
    weather_info = get_weather_data(
        st.session_state.location_data['lat'],
        st.session_state.location_data['lon']
    )
    
    # Create tabs for different types of information
    tab1, tab2, tab3 = st.tabs(["Basic Info", "Zip Codes", "IP Addresses"])
    
    with tab1:
        # Create four columns for basic information
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.subheader("Location")
            st.write("**Coordinates:**")
            st.write(f"Latitude: {st.session_state.location_data['lat']:.4f}°N")
            st.write(f"Longitude: {st.session_state.location_data['lon']:.4f}°W")
        
        with col2:
            st.subheader("City Information")
            st.write(f"Population (2024): {st.session_state.location_data['city_info']['population_2024']:,}")
            st.write(f"Density: {st.session_state.location_data['city_info']['density_per_mile2']:,.0f} per sq mile")
            st.write(f"Area: {st.session_state.location_data['city_info']['area_mile2']:.2f} sq miles")
        
        with col3:
            if st.session_state.location_data['bounds']:
                st.subheader("Bounding Box")
                bounds = st.session_state.location_data['bounds']
                st.write(f"North: {bounds.top:.4f}°")
                st.write(f"South: {bounds.bottom:.4f}°")
                st.write(f"East: {bounds.right:.4f}°")
                st.write(f"West: {bounds.left:.4f}°")
        
        with col4:
            st.subheader("Current Weather")
            if 'error' in weather_info:
                st.error(weather_info['error'])
            else:
                st.write(f"**Temperature:** {weather_info['temperature']:.1f}°F")
                st.write(f"**Feels Like:** {weather_info['feels_like']:.1f}°F")
                st.write(f"**Humidity:** {weather_info['humidity']}%")
                st.write(f"**Wind Speed:** {weather_info['wind_speed']} mph")
                st.write(f"**Conditions:** {weather_info['description']}")
                
                if weather_info['alerts']:
                    st.warning("⚠️ Weather Alerts")
                    for alert in weather_info['alerts']:
                        with st.expander(f"Alert: {alert['event']}"):
                            st.write(alert['description'])
    
    with tab2:
        st.subheader(f"Zip Codes for {st.session_state.location_data['city_info']['city_name']}, {st.session_state.location_data['city_info']['state_name']}")
        zipcodes = get_city_zipcodes(st.session_state.location_data['city_info']['city_name'], st.session_state.location_data['city_info']['state_name'])
        if zipcodes:
            # Create a grid layout for zip codes
            cols = st.columns(5)  # Display in 5 columns
            for idx, zipcode in enumerate(zipcodes):
                cols[idx % 5].write(zipcode)
        else:
            st.info("No zip codes found for this city.")
   
    with tab3:
        st.subheader(f"IP Addresses for {st.session_state.location_data['city_info']['city_name']}, {st.session_state.location_data['city_info']['state_name']}")
        ip_addresses = get_city_ips(st.session_state.location_data['city_info']['city_name'], st.session_state.location_data['city_info']['state_name'])
        if ip_addresses:
            # Display IP addresses in a table
            ip_df = pd.DataFrame(ip_addresses, columns=['IP Address'])
            st.dataframe(ip_df, hide_index=True)
        else:
            st.info("No IP addresses found for this city.") 









        
# async def waiting(task):
#     result = await task()
#     return result

# Process location data and create visualizations
if selected_graphs and st.session_state.current_tiff_path and st.session_state.location_data['center_point']['lat']:
    if st.session_state.needs_processing:
        try:
            # Combine TIFF files using session state data
            input_dir = get_base_path(data_source)
            success = combine_tiff_files(
                input_dir=input_dir,
                output_path=st.session_state.current_tiff_path,
                lat=st.session_state.location_data['center_point']['lat'],
                lon=st.session_state.location_data['center_point']['lon'],
                elevation=st.session_state.location_data['scale']
            )
            
            if success:
                # Load the data first
                data, trash = load_and_downsample_tiff(st.session_state.current_tiff_path)
                bounds = calculate_zoom_bounds(
                    st.session_state.location_data['center_point']['lat'],
                    st.session_state.location_data['center_point']['lon'],
                    st.session_state.location_data['scale']
                )
                
                # Update session state after successful load
                st.session_state.data = data
                st.session_state.bounds = bounds
                st.session_state.location_data['bounds'] = bounds
                st.session_state.needs_processing = False
            else:
                st.error("Failed to combine TIFF files")
                st.stop()
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            st.stop()
    
    # Create columns based on number of selected graphs
    num_cols = min(1, len(selected_graphs))
    cols = st.columns(num_cols)
    
    for i, graph_type in enumerate(selected_graphs):
        try:
            col_idx = i % num_cols
            with cols[col_idx]:
                st.subheader(graph_type)
                
                if graph_type == 'Street View':
                    try:
                        lat = st.session_state.location_data['center_point']['lat']
                        lon = st.session_state.location_data['center_point']['lon']
                        
                        # Create map if it doesn't exist
                        if st.session_state.location_data['map_object'] is None:
                            map_params = get_map_parameters(
                                lat=lat,
                                lon=lon,
                                use_ip_location=True,
                                city_info=st.session_state.location_data.get('city_info')
                            )
                            
                            st.session_state.location_data['map_object'] = create_map(
                                lat=lat,
                                lon=lon,
                                zoom=map_params['zoom']
                            )
                        
                        # Display the map
                        st_folium(
                            st.session_state.location_data['map_object'],
                            width="100%",
                            height=600,
                            returned_objects=[],
                            key=f"map_{lat}_{lon}"
                        )
                    except Exception as e:
                        st.error(f"Error displaying map: {str(e)}")
                        st.error(f"Location data: {st.session_state.location_data}")
                
                elif graph_type == 'DEM Graph':
                    coordinates = {
                        'lat': st.session_state.location_data['center_point']['lat'],
                        'lon': st.session_state.location_data['center_point']['lon']
                    }
                    fig_dem = create_dem_plot(st.session_state.data, st.session_state.bounds, coordinates)
                    if fig_dem:
                        st.pyplot(fig_dem)
                        plt.close(fig_dem)
                
                elif graph_type == 'Ridge Graph':
                    coordinates = {
                        'lat': st.session_state.location_data['center_point']['lat'],
                        'lon': st.session_state.location_data['center_point']['lon']
                    }
                    title = f"{coordinates['lat']},\n{coordinates['lon']}"
                    fig_ridge = create_ridge_plot_optimized(st.session_state.data, title=title)
                    if fig_ridge:
                        st.pyplot(fig_ridge)
                        plt.close(fig_ridge)
                
                elif graph_type == '3D Graph':
                    plot_data = downsample_for_3d(st.session_state.data)
                    fig_3d = create_3d_plot(plot_data, st.session_state.bounds)
                    if fig_3d:
                        st.plotly_chart(fig_3d)
                
                elif graph_type == 'Satellite View':
                    try:
                        bounds = st.session_state.location_data['bounds']
                        
                        # Add a button to fetch satellite imagery
                        if st.button("Fetch Satellite Image", key="fetch_satellite"):
                            with st.spinner("Fetching satellite imagery..."):
                                # Create progress bar container
                                progress_container = st.empty()
                                progress_bar = progress_container.progress(0, text="Downloading satellite imagery...")
                                
                                def update_progress(progress):
                                    progress_bar.progress(progress, text=f"Downloading tiles... {int(progress * 100)}%")
                                
                                # Get the satellite image
                                image = get_satellite_image(
                                    bounds.top,
                                    bounds.left,
                                    bounds.bottom,
                                    bounds.right,
                                    zoom=12 if st.session_state.location_data['scale'] >= 500 else 14,
                                    progress_callback=update_progress
                                )
                                
                                progress_container.empty()
                                
                                if image is not None and image.size > 0:
                                    # Convert BGR to RGB for display
                                    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                                    
                                    # Store the image in session state
                                    st.session_state.satellite_image = image_rgb
                                    
                                    # Show coordinates
                                    st.session_state.satellite_coords = {
                                        'top': bounds.top,
                                        'left': bounds.left,
                                        'bottom': bounds.bottom,
                                        'right': bounds.right
                                    }
                                else:
                                    st.error("Failed to fetch satellite imagery - no image data received")
                        
                        # Display the image if it exists in session state
                        if 'satellite_image' in st.session_state:
                            st.image(st.session_state.satellite_image, use_container_width=True)
                            
                            # Show coordinates if they exist
                            if 'satellite_coords' in st.session_state:
                                coords = st.session_state.satellite_coords
                                # st.write("**Coordinates:**")
                                # st.write(f"Top-left: ({coords['top']:.4f}°N, {coords['left']:.4f}°W)")
                                # st.write(f"Bottom-right: ({coords['bottom']:.4f}°N, {coords['right']:.4f}°W)")
                    
                    except Exception as e:
                        st.error(f"Error fetching satellite imagery: {str(e)}")
                        import traceback
                        st.error(f"Stack trace: {traceback.format_exc()}")
    




                    # st.info(f"{graph_type} visualization coming soon!")
        except Exception as e:
            st.error(f"Error processing {graph_type}: {str(e)}")
else:
    if not selected_graphs:
        st.warning("Please select at least one visualization type")
    if not st.session_state.location_data['center_point']['lat']:
        pass

# Add to the cleanup sections where we clear other session state variables
if 'satellite_image' in st.session_state:
    del st.session_state.satellite_image
if 'satellite_coords' in st.session_state:
    del st.session_state.satellite_coords




















