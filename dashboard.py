import xarray as xr
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pydeck as pdk
#plt.style.use(["science"])

import scienceplots
import rasterio

import streamlit as st

import dashboard_utils as da
import folium


# To set a webpage title, header and subtitle
st.set_page_config(page_title = "TRACEVE forest type and cover maps",layout = 'wide')
st.header("Visualize Sentinel-2 spectral characteristics of different forest cover distributions in the shrub and tree layer")
st.subheader("Interact with this dashboard using the widgets on the sidebar")

sib_classes = rasterio.open()

m = folium.Map([37, 0], zoom_start=10)
tile = folium.TileLayer(
        tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr = 'Esri',
        name = 'Esri Satellite',
        overlay = False,
        control = True
       ).add_to(m)

