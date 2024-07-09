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
import geopandas as gpd
import leafmap.foliumap as leafmap


import streamlit as st



parks_name = "/home/c7161037/Desktop/map_dashboard/data/parks.geojson"
vpo_name = "/home/c7161037/Desktop/map_dashboard/data/vpo.geojson"
eve_name = "/home/c7161037/Desktop/map_dashboard/data/gen_cover_eve.wgs84.COG.tif"
dec_name = "/home/c7161037/Desktop/map_dashboard/data/gen_cover_dec.wgs84.COG.tif"
class_name = "/home/c7161037/Desktop/map_dashboard/data/gen_classes.wgs84.COG.tif"
sib_eve_name = "/home/c7161037/Desktop/map_dashboard/data/sib_cover_eve.wgs84.COG.tif"
sib_dec_name = "/home/c7161037/Desktop/map_dashboard/data/sib_cover_dec.wgs84.COG.tif"
sib_class_name = "/home/c7161037/Desktop/map_dashboard/data/sib_classes.wgs84.COG.tif"

colors = [(255, 113, 36), (1, 3, 131), (164, 227, 157), (114, 124, 216), (12, 201, 2), (12, 89, 1), (7, 37, 233)]
labels = ["azonal", "boreal", "mediterranean broad", "mediterranean needle", "submediterranean", "temperate broad", "temperate needle"]

# To set a webpage title, header and subtitle
st.set_page_config(page_title = "TRACEVE forest type and cover maps",layout = 'wide')
st.header("TRACEVE forest type and cover maps")
st.subheader("Interact with this dashboard using the widgets on the sidebar")
st.markdown("- forest type maps were produced based on Italian Forest Vegetation Base and annual Sentinel-2 time series from 2017 to 2023 using an InceptionTime ensemble\n" \
            "- cover maps were produced using the Vegetation Plot observation collected in Sibillini and Gennargentu Nationalpark and an aggregated annual Sentinel-2 time series\n\n" \
        "NOTE: drag the forest type legend to avoid overlaps...")

#sel = st.multiselect(label="Select forest types that should be masked from the map:",
#                     options=labels)




# add filters
#with st.echo():

m2 = leafmap.Map(basemap="Esri.WorldImagery")#, height="1000px", width="1500px")
m2.add_basemap("Esri.WorldImagery")





m2.add_raster(class_name ,
        layer_name="Gennargentu forest type")

m2.add_raster(eve_name,
        vmin=0, vmax=100,
        cmap="Greens",
        layer_name="Gennargentu Cover EVE")

m2.add_raster(dec_name,
        vmin=0, vmax=100,
        cmap="Greens",
        layer_name="Gennargentu Cover DEC")

m2.add_raster(sib_class_name ,
        layer_name="Sibillini forest type")

m2.add_raster(sib_eve_name,
        vmin=0, vmax=100,
        cmap="Greens",
        layer_name="Sibillini Cover EVE")

m2.add_raster(sib_dec_name,
        vmin=0, vmax=100,
        cmap="Greens",
        layer_name="Sibillini Cover DEC")

parks = gpd.read_file(parks_name)[["siteName", "geometry"]]
style = {"fillColor": "#00000000"}
m2.add_gdf(parks, layer_name="Parks", style_callback=lambda x: style)

vpos = gpd.read_file(vpo_name)
#style = {"fillColor": "#00000000"}
m2.add_gdf(vpos, layer_name="VPOs")#, style_callback=lambda x: style)
#m2.add_circle_markers_from_xy(vpos, popup="img")

m2.add_legend(title="Forest Type", labels=labels, colors=colors, draggable=True, position="topright")
m2.add_colormap(label="Cover %", cmap="Greens", vmin=0, vmax=100, position="bottomright", transparent=True)

try:
        m2.add_inspector_gui(position='topright', opened=True)
except: pass

#legend1 = """
#<div style="position: fixed; bottom: 50px; left: 10px; width: 150px; height: 150px; 
#            border:2px solid grey; z-index:9999; font-size:14px; background-color:white;">
#    <p style="margin: 5px;">Legend 1</p>
#    <i style="background: #FF0000"></i> 0<br>
#    <i style="background: #00FF00"></i> 1<br>
#    <i style="background: #0000FF"></i> 2<br>
#    <i style="background: #FFFF00"></i> 3<br>
#    <i style="background: #FF00FF"></i> 4<br>
#    <i style="background: #00FFFF"></i> 5<br>
#    <i style="background: #000000"></i> 6<br>
#</div>
#"""
#
#legend2 = """
#<div style="position: fixed; bottom: 50px; left: 170px; width: 150px; height: 150px; 
#            border:2px solid grey; z-index:9999; font-size:14px; background-color:white;">
#    <p style="margin: 5px;">Legend 2</p>
#    <i style="background: #FF0000"></i> 0<br>
#    <i style="background: #00FF00"></i> 1<br>
#    <i style="background: #0000FF"></i> 2<br>
#    <i style="background: #FFFF00"></i> 3<br>
#    <i style="background: #FF00FF"></i> 4<br>
#    <i style="background: #00FFFF"></i> 5<br>
#    <i style="background: #000000"></i> 6<br>
#</div>
#"""
#
## Add legends to the map
#m2.get_root().html.add_child(folium.Element(legend1))
#m2.get_root().html.add_child(folium.Element(legend2))

m2.to_streamlit()
