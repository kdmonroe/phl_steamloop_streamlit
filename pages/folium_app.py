import streamlit as st
import folium
from folium.raster_layers import TileLayer
from streamlit_folium import folium_static
import requests
import geopandas as gpd
import json 
import pandas as pd
import branca
import base64
import numpy as np
from io import BytesIO

# Fetch API key and URLs from Streamlit secrets
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]
PNG_WIKI_COGEN = st.secrets["aws"]["cogeneration_png"]
PNG_DISTRICT_ENERGY = st.secrets["aws"]["district_energy_png"]
JPG_EDISON = st.secrets["aws"]["edison_plant_jpg"]
JPG_GRAYS_FERRY = st.secrets["aws"]["grays_ferry_jpg"]

GEOJSON_STEAM_LOOP = st.secrets["aws"]["steamloop_geojson"]
GEOJSON_PHL_BLDGS = st.secrets["aws"]["phl_bldg_geojson"]
GEOJSON_PHL_NBRHOODS = st.secrets["aws"]["phl_nbrhoods_geojson"]


def main():
    """
    folium_app.py
    Entry point for the Streamlit application. This function fetches GeoJSON data for the Philadelphia steam loop, 
    nearby buildings, and neighborhoods. The function then creates a Streamlit Folium map with this data, displaying a satellite 
    view, the steam loop, buildings, neighborhoods, and custom markers for cogeneration plants. 

    The map also features a legend and layer control, and statistics about the buildings and neighborhoods are displayed 
    below the map.

    The application includes expanders for source information and a disclaimer.
    """

    # Fetch GeoJSON data with geopandas
    steamloop_gdf = read_geojson_from_url(GEOJSON_STEAM_LOOP)
    bldg_gdf = read_geojson_from_url(GEOJSON_PHL_BLDGS)
    neighborhoods_gdf = read_geojson_from_url(GEOJSON_PHL_NBRHOODS)

    # Make sure both GeoDataFrames are using the same CRS
    neighborhoods_gdf = neighborhoods_gdf.to_crs(steamloop_gdf.crs)

    tileurl = 'https://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}@2x.png?access_token=' + str(MAPBOX_API_KEY)

    m = folium.Map(location=[39.9526, -75.1652], zoom_start=13, tiles=None, attr="Bing", control_scale=True) # type: ignore

    # Add TileLayer
    tile_layer = TileLayer(
        tiles=tileurl,
        attr='Mapbox',
        name='Mapbox Satellite View',
        overlay=False
    )
    tile_layer.add_to(m)

    st.markdown("""
        # Map of Philadelphia's Steam Loop
        Philadelphia's district heating system centrally generates steam, distributing it to roughly 500 buildings via a network of underground pipes. The map displayed below provides a visual representation of this steam loop, along with neighborhoods and buildings in proximity, which are likely connected to the system. Cogeneration plants (the primary sources of steam for the loop) are also displayed on the map.
    """)

    folium_map, colormap = generate_folium_map(m, neighborhoods_gdf)
    
    # Add markers
    marker_data = [
        {
            # 2600 Christian St
            "lat": 39.9423456,
            "lon": -75.1884788,
            "name": "Grays Ferry Vicinity Energy cogeneration plant",
            "image_url": JPG_GRAYS_FERRY
        }, 
        {   # 908 Sansom St
            "lat": 39.949610, 
            "lon": -75.157476, 
            "name": "Edison Plant",
            "image_url": JPG_EDISON
        }
    ]

    m = add_steam_loop_layer(m, steamloop_gdf)
    m = add_phl_bldg_layer(m, bldg_gdf)

    m = add_custom_markers(m, marker_data, "Cogeneration Plants")

    # Add layer control to the map
    folium.LayerControl(collapsed=True).add_to(m)
    
    # Display the map
    folium_static(m)
    
    # Define the marker image URL
    marker_image_url = "http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png"

    # Display the legend
    display_legend(marker_image_url)
    
    display_building_stats(bldg_gdf)     
    
    display_bldgs_nearby_expander(neighborhoods_gdf, colormap)
    
    add_source_info_expanders()
    
    display_disclaimer_and_attr()
    

# -----\\ HELPER FUNCTIONS

@st.cache_data(ttl=None, persist=None)
def read_geojson_from_url(url):
    """ Reads GeoJSON data from a URL and returns a GeoDataFrame.
        Uses caching to avoid re-downloading the data.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    f = BytesIO(response.content)
    gdf = gpd.read_file(f)

    # Convert all datetime columns to string
    datetime_cols = gdf.select_dtypes(include=[np.datetime64]).columns.tolist()
    for col in datetime_cols:
        gdf[col] = gdf[col].astype(str)
    
    return gdf

def add_custom_markers(folium_map, marker_data, marker_name="Custom Markers"):
    ''' Adds Folium markers to the map with custom icons and popups. 
    '''
    # Create a FeatureGroup for the markers
    marker_group = folium.FeatureGroup(name=marker_name)
    
    for marker in marker_data:
        image = requests.get(marker["image_url"]).content
        encoded = base64.b64encode(image).decode()

        # Define image dimensions
        img_width, img_height = 120, 120  # You can modify these values as needed

        # Create HTML
        html = '<p>{}</p><br><img src="data:image/png;base64,{}" width="{}" height="{}">'.format(marker["name"], encoded, img_width, img_height)

        # Create iframe with HTML
        iframe = folium.IFrame(html=html, width=img_width+20, height=img_height+50)  # type: ignore # Adjust iframe dimensions here

        # Use a custom marker icon
        icon_url = 'http://icons.iconarchive.com/icons/paomedia/small-n-flat/1024/map-marker-icon.png'
        icon = folium.CustomIcon(icon_url, icon_size=(28, 30))  # The size of the icon image file

        # Add marker to map with custom icon
        folium.Marker(
            location=[marker["lat"], marker["lon"]],
            popup=folium.Popup(iframe, max_width=img_width+20),
            icon=icon
        ).add_to(marker_group)
    
    # Add marker group to the map
    marker_group.add_to(folium_map)
    
    return folium_map


def display_disclaimer_and_attr():
    """ 
    Displays the disclaimer and attribution for the map.
    Uses HTML to style the text and Streamlit's expander widget to hide the section by default.
    """

    with st.expander("Disclaimer", expanded=True):
        st.markdown("""
        <style>
            .disclaimer {
                font-size: 0.9em;
            }
            .attribution {
                font-size: 0.8em;
                color: #808080;
            }
        </style>
        <p class='disclaimer'>This map is designed for educational and informational purposes and is not suitable for precise planning or engineering purposes. The counts of buildings within neighborhoods are demonstrated for analytical purposes and do not confirm active connections to the steam loop. Using this map for any purpose beyond obtaining general information may result in inaccuracies.</p>
        """, unsafe_allow_html=True)



def display_legend(marker_image_url):
    """ 
    Displays the legend for the map with the specified marker image.
    """
    # Fetch marker image and encode in base64
    image = requests.get(marker_image_url).content
    encoded_marker_image = base64.b64encode(image).decode()
    
    # Legend expander for the map
    with st.expander("🎨 Legend", expanded=True):
        st.markdown(f"""
            <div style="font-size:16px;">
                <ul style="list-style: none;">
                    <li><span style="color: #4A90E2;">&#11044;</span> - Philadelphia Steam Loop</li>
                    <li><span style="color: #008000;">&#11044;</span> - Building Footprints</li>
                    <li><span style="color: #FF0000;">&#11044;</span> - Philadelphia Neighborhoods (High # of Buildings)</li>
                    <li><span style="color: #FF8C00;">&#11044;</span> - Philadelphia Neighborhoods (Low # of Buildings)</li>
                    <li><img src="data:image/png;base64,{encoded_marker_image}" style="width:14px;height:15px;"> - Cogeneration Plant (Click to View) </li>
                </ul>
            </div>
        """, unsafe_allow_html=True)


def add_steam_loop_layer(folium_map, steamloop_gdf):
    """ Displays the steam loop on the Folium map.
        Uses geodataframe of the steam loop and Folium map object.
    """
    steam_loop = folium.GeoJson(
        steamloop_gdf,
        name='Philadelphia Steam Loop',
        style_function=lambda feature: {
            'fillColor': '#C0C0C0',  # silver color
            'color': '#4A90E2',  # muted blue
            'weight': 5,  # this controls the thickness of the outline. Set it as per your requirement.
            'fillOpacity': 0.5,
        }
    ).add_to(folium_map)
    return folium_map

def add_phl_bldg_layer(folium_map, bldg_gdf):
    """ Displays the building footprints on the Folium map.
        Uses geodataframe of the building footprints and Folium map object.
    """
    
    phl_bldg = folium.GeoJson(
        bldg_gdf,
        name='Building Footprints (1000 m from steam loop)',
        style_function=lambda feature: {
            'fillColor': '#008000',
            'color': 'transparent',
            'weight': 1,
            'fillOpacity': 0.5,
        }
    ).add_to(folium_map)
    return folium_map

def generate_folium_map(folium_map, neighborhoods_gdf):
    """ Generates the Folium map with the steam loop, building footprints, and neighborhood polygons.
    """
    # Create a colormap
    max_count = neighborhoods_gdf['Join_Count'].max()
    colormap = branca.colormap.linear.OrRd_07.scale(0, max_count)

    # Apply the colormap to the neighborhoods GeoDataFrame
    neighborhoods_gdf['color'] = neighborhoods_gdf['Join_Count'].map(lambda count: colormap(count) if count > 0 else '#000000')
    
    # Convert timestamp columns to string
    for col in neighborhoods_gdf.columns:
        if isinstance(neighborhoods_gdf[col].dtype, pd.core.dtypes.dtypes.DatetimeTZDtype):
            neighborhoods_gdf[col] = neighborhoods_gdf[col].astype(str)

    # Convert the GeoPandas DataFrame to GeoJSON
    neighborhoods_data = json.loads(neighborhoods_gdf.to_json())

    # Create GeoJSON layer with styling for neighborhoods
    neighborhoods_layer = folium.GeoJson(
        neighborhoods_data,
        name='Philadelphia Neighborhoods',
        style_function=lambda feature: {
            'color': feature['properties']['color'], 
            'weight': 1,
            'fillOpacity': 0.5,  # 50% opacity
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["listname", "Join_Count"], 
            aliases=["Neighborhood:", "Building Count:"],
            localize=True
        )  # add tooltips
    ).add_to(folium_map)

    # Add the colormap to the map
    colormap.add_to(folium_map)

    return folium_map, colormap


def display_bldgs_nearby_expander(neighborhoods_gdf, colormap):

    # get total number where "Join_Count" > 0
    num_intersecting = len(neighborhoods_gdf[neighborhoods_gdf['Join_Count'] > 0])
    
    total_neighborhoods = len(neighborhoods_gdf)
    
    # First, sort the neighborhoods by the number of buildings
    sorted_neighborhoods = neighborhoods_gdf.sort_values(by='Join_Count', ascending=False)

    # filter out neighborhoods with 0 buildings
    sorted_neighborhoods = sorted_neighborhoods[sorted_neighborhoods['Join_Count'] > 0]
    
    # Create HTML list items for each neighborhood, coloring the neighborhood name by its count
    markdown_text = ''.join([
        f'<li><span style="color: {colormap(count) if count > 0 else "#000000"};">{neighborhood}</span>: {count} buildings</li>'
        for neighborhood, count in zip(sorted_neighborhoods['listname'], sorted_neighborhoods['Join_Count'])
    ])

    with st.expander("🏠 Nearby Buildings Statistics", expanded=False):
        st.markdown(f"""
            <div style="font-size:24px; font-weight: bold;">
                Roughly <span style="color: #FFA500;">{num_intersecting}</span> neighborhoods (from a total of <span style="color :#FF8C00;">{total_neighborhoods}</span>) are close to the Philadelphia Steam Loop. Here's how many buildings they have:
            </div>
            <div style="font-size:18px;">
                <ol>
                    {markdown_text}
                </ol>
            </div>
        """, unsafe_allow_html=True)

def display_building_stats(gdf):
    ''' Display building statistics in a Streamlit expander
    '''
    total = len(gdf)
    with st.expander("🏢 Building Statistics", expanded=True):
        miles = 1000 / 1609.34 # converting meters to miles
        # define custom CSS
        st.markdown("""
            <style>
                .total {
                    color: orange;
                }
                .buildings {
                    color: #FFC966;
                }
                .estimate {
                    font-size: 0.8em;
                }
            </style>
            """, unsafe_allow_html=True)
        # Using the custom CSS classes
        st.markdown(f"""
                    <p>There are approximately <span class='buildings'>{total} buildings </span><span class='total'> within 1000m</span> (about {miles:.2f}</span> miles) <span class='total'> of the steam loop.</p>
                    
                    <h4 class='estimate'>Estimated using Microsoft Building Footprints dataset and georeferenced steam loop data.</h4>
                    """
                    , unsafe_allow_html=True)


def add_source_info_expanders():
    ''' Add Streamlit expanders for source information and CHP information
    '''

    # Create another expander for the CHP information, default as expanded
    with st.expander("💡 More about Combined Heat and Power (CHP)", expanded=True):
        st.markdown("""
        District energy systems are characterized by one or more central plants producing hot water, steam, and/or chilled water, which then flows through a network of insulated pipes to provide hot water, space heating, and/or air conditioning for nearby buildings. District energy systems serve a variety of end-use markets, including downtowns (central business districts), college and university campuses, hospitals and healthcare facilities, airports, military bases, and industrial complexes. By combining loads for multiple buildings, district energy systems create economies of scale that help reduce energy costs and enable the use
        of high-efficiency technologies such as combined heat and power (CHP).

        Source: [U.S. Department of Energy, Combined Heat and Power Technology Fact Sheet Series](https://www.energy.gov/sites/prod/files/2020/10/f79/District%20Energy%20Technology%20Fact%20Sheet_9.25.20_compliant.pdf)
        
        ##### More on Philadelphia's Steam Loop
        -  [Vicinity Energy (Owner)](https://www.vicinityenergy.us/locations/philadelphia)
        -  [How A Combined Cycle Power Plant Works | Gas Power Generation](https://www.youtube.com/watch?v=KVjtFXWe9Eo&t=12s)
        -  [Could Philly’s steam system provide a climate solution? PGW says no - WHYY article](https://whyy.org/articles/philadelphia-pgw-vicinity-customers-gas-steam-loop-climate-change/) 
        -  [Willow Street Steam Generation Plant - Abandoned America](https://www.abandonedamerica.us/willow-street-steam-plant)
        -  [Center City steam loop a ‘diamond in the rough,’ - Philadelphia Inquirer article](https://www.inquirer.com/business/philadelphia-steam-plant-vicinity-veolia-dicroce-20200204.html)
        """)

        # District Energy Image
        st.image(PNG_DISTRICT_ENERGY, use_column_width=True)
        st.markdown("<div style='text-align: center; color: grey; font-size: small;'>Visual depiction of a District Energy Supply</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; color: grey; font-size: small;'>Image Source: <a href='https://www.youtube.com/watch?v=7BznKyEb0bc&t=60s'>International District Energy Association (YouTube)</a></div>", unsafe_allow_html=True)


        # Wikipedia Cogeneration Image
        st.image(PNG_WIKI_COGEN, use_column_width=True)
        st.markdown("<div style='text-align: center; color: grey; font-size: small;'>Image Source: <a href='https://en.wikipedia.org/wiki/Cogeneration'>Wikipedia Cogeneration</a></div>", unsafe_allow_html=True)

    with st.expander("📜 Source Information", expanded=False):
        st.markdown("""
            The steam loop was georeferenced from two main sources: 
            - [Vicinity Energy (Informational Brochure)](https://www.vicinityenergy.us/brochures/delivering-reliable-green-energy-to-philadelphia) 
            - [Old Trigen Steam Distribution Map](https://hiddencityphila.org/2012/02/all-steamed-up/)
        
            #### Building Footprints + Neighborhoods
            - [Building Footprints, 2021 Microsoft](https://github.com/Microsoft/USBuildingFootprints)
            - [Philadelphia Neighborhoods, Azavea](https://github.com/azavea/geo-data/blob/master/Neighborhoods_Philadelphia/Neighborhoods_Philadelphia.geojson)
            
            #### Limitations
           Buildings were filtered to only include those in Philadelphia County and within 1000 meters of the steam loop and counts are estimated (see Disclaimer). It is unknown to what specific extent or general area buildings could connect to the system. 1000 meters is a generalized estimate. According to a <a href="https://www.inquirer.com/business/philadelphia-steam-plant-vicinity-veolia-dicroce-20200204.html" target="_blank">2020 Inquirer article</a>, 
            The Center City district heating system produces steam at a central power plant and delivers it by underground pipes to about 500 buildings.
                    
            The steam loop's current energy capacity is unknown. Whether additional buildings are connected, or could be connected in the future, is also unknown. 
            
            #### Software
            - [GeoPandas](https://geopandas.org/)
            - [Folium](https://python-visualization.github.io/folium/)
            - [Streamlit](https://streamlit.io/)
            - [Streamlit-Folium](https://github.com/randyzwitch/streamlit-folium)
            - [QGIS](https://qgis.org/en/site/)
            - [ChatGPT (Mar 14 version)](https://openai.com/blog/chatgpt)
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()