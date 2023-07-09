# Philadelphia Steam Loop Map - Streamlit Web App

This Streamlit app  visualizes the Philadelphia Steam Loop system and its intersection with nearby building footprints and neighborhood boundaries in the city. Additional research on Combined Heat and Power (Cogeneration) energy  is included.

- The app leverages [GeoPandas](https://geopandas.org/), [Branca](https://python-visualization.github.io/branca/), 
[Streamlit-Folium](https://github.com/randyzwitch/streamlit-folium), and [Streamlit](https://streamlit.io/). It is hosted on [Streamlit Community Cloud](https://streamlit.io/cloud).
- The application uses [Mapbox API](https://www.mapbox.com/) for the satellite basemap in Folium
- Source data URLs are loaded using [Streamlit Secret Management](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)


## Installation

To install and run the web application locally, follow these steps:

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/phl_steamloop_streamlit.git
    ```

2. Navigate to the directory:
    ```bash
    cd phl_steamloop_streamlit
    ```

3. Create a new python environment with conda or pipenv. Activate it, then install the required libraries using  `requirements.txt`:

    ```python
    pip install -r requirements.txt
    ```

4. Navigate to `pages`. Update the `secrets.toml` in the same directory. Then run the Streamlit app:
    ```bash
    streamlit run folium_app.py
    ```

5.  Navigate to the localhost URL displayed in your terminal (usually `http://localhost:8501`).

Please note that the Mapbox API key and the source URLs from Streamlit secrets. You need to add your own Mapbox API key and URLs into the Streamlit `secrets.toml` file for the application to work.



## Disclaimer

Please be aware that this map is intended to provide a general overview of the steam loop and should not be utilized for engineering or precise planning purposes. Its primary function is to serve as an informational tool. Relying on this map for other than informational purposes could lead to inaccuracies.

## Contact 

If you encounter any issues while running the project, please open an issue on the GitHub repository or reach out via [email](mailto:keon.monroe@gmail.com).

Happy Mapping!
