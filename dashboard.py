import geopandas as gpd
import leafmap.foliumap as leafmap


import streamlit as st



parks_name = "https://raw.githubusercontent.com/benehiebl/maps_traceve/main/data/parks.geojson"
vpo_name = "https://raw.githubusercontent.com/benehiebl/maps_traceve/main/data/vpo.geojson"
eve_name = "https://raw.githubusercontent.com/benehiebl/maps_traceve/main/data/gen_cover_eve.wgs84.COG.tif"
dec_name = "https://raw.githubusercontent.com/benehiebl/maps_traceve/main/data/gen_cover_dec.wgs84.COG.tif"
class_name = 'https://api.ellipsis-drive.com/v3/path/e6c55e3d-154f-4f61-b477-128a4af5fd81/raster/timestamp/e8234b7e-c85a-461a-a12a-99754b1a72ed/tile/{z}/{x}/{y}?style=d68b956d%2d541d%2d4256%2d8901%2d8ef163c7a33c&token=epat_Kkh0lVilBZMTZFwzvyBP5IkYqQBH3cZLjPU333j30KmJlBATsYdRI4gODBANy9rW'
sib_eve_name = "https://raw.githubusercontent.com/benehiebl/maps_traceve/main/data/sib_cover_eve.wgs84.COG.tif"
sib_dec_name = "https://raw.githubusercontent.com/benehiebl/maps_traceve/main/data/sib_cover_dec.wgs84.COG.tif"
sib_class_name = "https://api.ellipsis-drive.com/v3/path/2b46a0fb-bbb8-47fa-84b5-31b707e6ea50/raster/timestamp/e5831b26-33d5-4463-b5e0-f0408004d3b8/tile/{z}/{x}/{y}?style=8dd14ae9%2d5d1a%2d4efe%2dadeb%2db9792b175099&token=epat_uMqm47CrbhbMCKKt9wjGG2IZsPntPh7bHfAl9nxrP1kjpuFd9efOR1zSam6pbyRx"

colors = [(255, 113, 36), (1, 3, 131), (164, 227, 157), (114, 124, 216), (12, 201, 2), (12, 89, 1), (7, 37, 233)]
labels = ["azonal", "boreal", "mediterranean broad", "mediterranean needle", "submediterranean", "temperate broad", "temperate needle"]

# To set a webpage title, header and subtitle
st.set_page_config(page_title = "TRACEVE forest type and cover maps",layout = 'wide')
st.header("TRACEVE forest type and cover maps")
#st.subheader("Interact with this dashboard using the widgets on the sidebar")
st.markdown("- forest type maps were produced based on Italian Forest Vegetation Base and annual Sentinel-2 time series from 2017 to 2023 using an InceptionTime ensemble\n" \
            "- cover maps were produced using the Vegetation Plot observation collected in Sibillini and Gennargentu Nationalpark and an aggregated annual Sentinel-2 time series\n\n" \
        "NOTE: drag the forest type legend to avoid overlaps...")



img_sel = st.checkbox("Show phenology in full size")


m2 = leafmap.Map(basemap="Esri.WorldImagery")#, height="1000px", width="1500px")
m2.add_basemap("Esri.WorldImagery")

m2.add_tile_layer(url=class_name,
                  name="Gennargentu forest type",
                  attribution="gen_classes")

m2.add_cog_layer(eve_name,
        vmin=0, vmax=100,
        colormap_name="greens",
        name="Gennargentu Cover EVE")

m2.add_cog_layer(dec_name,
        vmin=0, vmax=100,
        colormap_name="greens",
        name="Gennargentu Cover DEC")

m2.add_tile_layer(url=sib_class_name,
                  name="Sibillini forest type",
                  attribution="sib_classes")

m2.add_cog_layer(sib_eve_name,
        vmin=0, vmax=100,
        colormap_name="greens",
        name="Sibillini Cover EVE")

m2.add_cog_layer(sib_dec_name,
        vmin=0, vmax=100,
        colormap_name="greens",
        name="Sibillini Cover DEC")

parks = gpd.read_file(parks_name)[["siteName", "geometry"]]
style = {"fillColor": "#00000000"}
m2.add_gdf(parks, layer_name="Parks", style_callback=lambda x: style)

vpos = gpd.read_file(vpo_name)
#style = {"fillColor": "#00000000"}
m2.add_gdf(vpos, layer_name="VPOs")#, style_callback=lambda x: style)
if img_sel:
            m2.add_circle_markers_from_xy(vpos, popup="img", max_width=550)

m2.add_legend(title="Forest Type", labels=labels, colors=colors, draggable=True, position="topright")
m2.add_colormap(label="Cover %", cmap="Greens", vmin=0, vmax=100, position=(6,1), width=3, height=0.2, label_size=9, transparent=True)

try:
        m2.add_inspector_gui(position='topright', opened=True)
except: pass


#m2.to_html("./map_sibgen.html")
m2.to_streamlit()
