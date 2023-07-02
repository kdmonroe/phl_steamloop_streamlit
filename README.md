# Philadelphia Steam Loop Map - Streamlit Web App

This project is a Streamlit application that visualizes the Philadelphia Steam Loop system and its intersection with building footprints and neighborhood boundaries in the city. The application leverages various Python libraries including Streamlit, Folium, Geopandas, and Branca.

The application uses Mapbox API for the satellite base map and also integrates with Google Drive for fetching necessary images and GeoJSON data.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.6 or later
- A Mapbox API key
- URLs for necessary images and GeoJSON data, stored in a Streamlit secret file.

## Installation

To install and run the web application, follow these steps:

1. Clone the repository:

```bash
git clone https://github.com/your-username/phl_steamloop_streamlit.git
```

2. Navigate to the directory:
```bash
cd phl_steamloop_streamlit
```

3. Install the requirements:
```bash
pip install -r requirements.txt
```

4. Run the Streamlit app:
```bash
streamlit run app.py
```

5.  Navigate to the localhost URL displayed in your terminal (usually `http://localhost:8501`).

Please note that the Mapbox API key and the Google Drive URLs are fetched from Streamlit secrets. You need to add your own Mapbox API key and URLs into the Streamlit `secrets.toml` file for the application to work.

## Acknowledgement

This project was created by Keon Monroe. You can check out the source code on [GitHub](https://github.com/kdmonroe/phl_steamloop_streamlit).

## Disclaimer

Please be aware that this map is intended to provide a general overview of the steam loop and should not be utilized for engineering or precise planning purposes. Its primary function is to serve as an informational tool. Relying on this map for other than informational purposes could lead to inaccuracies.

## Contact 

If you encounter any issues while running the project, please open an issue on the GitHub repository or reach out via [email](mailto:keon.monroe@gmail.com).

Happy Mapping!
