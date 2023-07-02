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
from io import BytesIO

# Fetch API key and URLs from Streamlit secrets
MAPBOX_API_KEY = st.secrets["mapbox"]["api_key"]
PNG_WIKI_COGEN = st.secrets["aws"]["cogeneration_png"]
JPG_EDISON = st.secrets["aws"]["edison_plant_jpg"]
JPG_GRAYS_FERRY = st.secrets["aws"]["grays_ferry_jpg"]

GEOJSON_STEAM_LOOP = st.secrets["aws"]["steamloop_geojson"]
GEOJSON_PHL_BLDGS = st.secrets["aws"]["phl_bldg_geojson"]
GEOJSON_PHL_NBRHOODS = st.secrets["aws"]["phl_nbrhoods_geojson"]

def main():
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

    st.header("Philadelphia Steam Loop Map")
    display_intersecting_neighborhoods(m, neighborhoods_gdf)

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

    m = add_custom_markers(m, marker_data)

    # Add layer control to the map
    folium.LayerControl(collapsed=True).add_to(m)
    
    # Display the map
    folium_static(m)
    
    display_legend()

    display_building_stats(bldg_gdf)     
    
    add_source_info_expanders()
    
    display_disclaimer_and_attr()
    

# -----\\ HELPER FUNCTIONS

def read_geojson_from_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers)
    f = BytesIO(response.content)
    gdf = gpd.read_file(f)
    return gdf

def add_custom_markers(folium_map, marker_data):
    ''' Adds Folium markers to the map with custom icons and popups. 
    '''
    for marker in marker_data:
        # Fetch image from Google Drive
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
        ).add_to(folium_map)
    return folium_map


def display_disclaimer_and_attr():
    # Data usgae disclaimer
    with st.expander("Disclaimer", expanded=True):
        st.markdown("""
        This map is intended to provide a general overview of the steam loop and should not be utilized for engineering or precise planning purposes. Neighboorhoold building counts are for analysis purposes only and does not infer active connections to the Vicinity steam loop. Relying on this map for other than general informational purposes could lead to inaccuracies. 
        """)
    
    st.markdown("""
    Created by Keon Monroe 
    """)

def display_legend():
    """ Displays Streamlit expander with legend for the map.
        Matches the colors of the Folium layers.
    """
    # Legend expander for the map
    with st.expander("🎨 Legend", expanded=True):
        st.markdown("""
            <div style="font-size:16px;">
                <ul style="list-style: none;">
                    <li><span style="color: #4A90E2;">&#11044;</span> - Philadelphia Steam Loop</li>
                    <li><span style="color: #008000;">&#11044;</span> - Building Footprints</li>
                    <li><span style="color: #FF0000;">&#11044;</span> - Philadelphia Neighborhoods (High # of Buildings)</li>
                    <li><span style="color: #FF8C00;">&#11044;</span> - Philadelphia Neighborhoods (Low # of Buildings)</li>
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
    """Displays the building footprints on the Folium map.
        Uses geodataframe of the building footprints and Folium map object.
    """
    # Convert GeoDataFrame to a dictionary and replace Timestamps with their string representation
    bldg_dict = bldg_gdf.__geo_interface__
    for feature in bldg_dict['features']:
        properties = feature['properties']
        for key, value in properties.items():
            if isinstance(value, pd.Timestamp):
                properties[key] = value.strftime('%Y-%m-%d %H:%M:%S')

    phl_bldg = folium.GeoJson(
        bldg_dict,
        name='Building Footprints (1000 m from steam loop)',
        style_function=lambda feature: {
            'fillColor': '#008000',
            'color': 'transparent',
            'weight': 1,
            'fillOpacity': 0,
        }
    ).add_to(folium_map)
    return folium_map

def display_intersecting_neighborhoods(folium_map, neighborhoods_gdf):
    """ Displays the intersecting neighborhoods on the Folium map as a choropleth.
        Uses geodataframe of the intersecting neighborhoods and Folium map object.
        Streamlit Expander - Neighborhood Statistics displays neighbrhood name and # of bldgs in the Folium popup. 
    """
    # Create a colormap
    max_count = neighborhoods_gdf['Join_Count'].max()
    colormap = branca.colormap.linear.OrRd_07.scale(0, max_count) # type: ignore

    # get total number where "Join_Count" > 0
    num_intersecting = len(neighborhoods_gdf[neighborhoods_gdf['Join_Count'] > 0])
    
    total_neighborhoods = len(neighborhoods_gdf)
    
    # First, sort the neighborhoods by the number of buildings
    sorted_neighborhoods = neighborhoods_gdf.sort_values(by='Join_Count', ascending=False)

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

    # filter out neighborhoods with 0 buildings
    sorted_neighborhoods = sorted_neighborhoods[sorted_neighborhoods['Join_Count'] > 0]
    
    # Create HTML list items for each neighborhood, coloring the neighborhood name by its count
    markdown_text = ''.join([
        f'<li><span style="color: {colormap(count) if count > 0 else "#000000"};">{neighborhood}</span>: {count} buildings</li>'
        for neighborhood, count in zip(sorted_neighborhoods['listname'], sorted_neighborhoods['Join_Count'])
    ])

    with st.expander("🏠 Neighborhood Statistics", expanded=False):
        st.markdown(f"""
            <div style="font-size:24px; font-weight: bold;">
                Buildings in <span style="color: #FFA500;">{num_intersecting}</span> (out of <span style="color :#FF8C00;">{total_neighborhoods}</span>) neighborhoods are nearby the Philadelphia Steam Loop.
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
            </style>
            """, unsafe_allow_html=True)
        # Using the custom CSS classes
        st.markdown(f"<p>There are approximately <span class='buildings'>{total} buildings </span><span class='total'>within 1000m</span> (about {miles:.2f}</span> miles) <span class='total'>of the steam loop.</span></p>", unsafe_allow_html=True)


def add_source_info_expanders():
    ''' Add Streamlit expanders for source information and CHP information
    '''

    # Create another expander for the CHP information, default as expanded
    with st.expander("💡 More about Combined Heat and Power (CHP)", expanded=True):
        st.markdown("""
        Combined Heat and Power (CHP), also known as cogeneration, is a highly efficient method of generating electricity and thermal energy from the same energy source. Basically, it's producing two types of energy in one go. What makes it cool is that it's a type of distributed generation, which means it generates power right where it's needed, rather than at a large plant somewhere else.

        Cogeneration captures the heat that would typically be wasted in power generation, instead using it for heating and cooling. Thus, it is highly efficient and versatile. It can use a variety of fuels, including both fossil and renewable ones. For decades, CHP has powered of large industrial, commercial, and institutional settings, as well as utility circles.
        
        CHP systems can achieve efficiencies of 65-75%, a substantial improvement over the national average of about 50% when these services are provided separately.

        Source: [U.S. Department of Energy](https://www.energy.gov/eere/iedo/combined-heat-and-power-basics)
        
        ##### More on Philadelphia's Steam Loop
        -  [Vicinity Energy (Owner)](https://www.vicinityenergy.us/locations/philadelphia)
        -  [Could Philly’s steam system provide a climate solution? PGW says no - WHYY article](https://whyy.org/articles/philadelphia-pgw-vicinity-customers-gas-steam-loop-climate-change/) 
        -  [Willow Street Steam Generation Plant - Abandoned America](https://www.abandonedamerica.us/willow-street-steam-plant)
        -  [Center City steam loop a ‘diamond in the rough,’ - Philadelphia Inquirer article](https://www.inquirer.com/business/philadelphia-steam-plant-vicinity-veolia-dicroce-20200204.html)
        """)
        
        # Wikipedia Cogeneration Image
        st.image(PNG_WIKI_COGEN, use_column_width=True) # type: ignore
        st.markdown("<div style='text-align: center; color: grey; font-size: small;'>Image Source: <a href='https://en.wikipedia.org/wiki/Cogeneration'>Wikipedia Cogeneration</a></div>", unsafe_allow_html=True)

    # Create a collapsible expander for the source information
    with st.expander("📜 Source Information", expanded=False):
        st.markdown("""
            #### The steam loop was georeferenced from two main sources: 
            -  [Vicinity Energy (Informational Brochure)](https://www.vicinityenergy.us/brochures/delivering-reliable-green-energy-to-philadelphia) 
            -  [Old Trigen Steam Distribution Map](https://hiddencityphila.org/2012/02/all-steamed-up/)
           
           #### Building footprints 
            - [2021 Micrsoft Building Footprints](https://github.com/Microsoft/USBuildingFootprints)
            
           #### Limitations
            Buildings were filtered to only include those in Philadelphia County and within 1000m of the steam loop. The counts are estimated (see Disclaimer). It is unknown to what extent buildings may draw from the steam loop (perhaps more or less than the chosen distance).</b>According to a 2020 Inquirer article, "The Center City district heating system produces steam at a central power plant and delivers it by underground pipes to about 500 buildings."
            So we can assume that there are at least 500 buildings connected to the steam loop.
            Whether additional buildings are connected, or could be connected in the future, is unknown.
            
           #### Software:
            - [GeoPandas](https://geopandas.org/)
            - [Folium](https://python-visualization.github.io/folium/)
            - [Streamlit](https://streamlit.io/)
            - [Streamlit-Folium](https://github.com/randyzwitch/streamlit-folium)
            - [QGIS](https://qgis.org/en/site/)
            - [ChatGPT (Mar 14 version)](https://openai.com/blog/chatgpt)
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()