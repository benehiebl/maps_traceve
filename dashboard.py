import geopandas as gpd
import leafmap.foliumap as leafmap
import pystac_client
import planetary_computer as pc
import datetime
import numpy as np


import streamlit as st
#from streamlit_folium import st_folium



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

#st.subheader("Interact with this dashboard using the widgets on the sidebar")
#st.markdown("- **forest type maps were produced based on Italian Forest Vegetation Base and annual Sentinel-2 time series from 2017 to 2023 using an InceptionTime ensemble**\n" \
#            "- **cover maps were produced using the Vegetation Plot observation collected in Sibillini and Gennargentu Nationalpark and an aggregated annual Sentinel-2 time series**\n\n" \
#        "**TIPPS:**\n" \
#        "- Use the full-screen button on the left side for a better experience (but make sure to memorize the legend/colormap befor...)\n" \
#        "- if the map appears white press the Rerun button in the upper right corner of the page")




### INTEGRATE PLANETARY COMPUTER
side = st.sidebar
## INPUTS 
side.header("TRACEVE forest type and cover maps")

img_sel = side.checkbox("Show phenology in full size")

with side.container(border=True):
        with st.popover("Planetary Computer STAC Catalog"):
                #with st.form(key="my_form"):
                collection = st.selectbox("Planetary Computer Collection", ("sentinel-2-l2a", "landsat-c2-l2"))
                #if collection=="sentinel-2-l2a":
                tile = st.text_input("Tile/Pathrow (Sibillini 33TUH/190031/190030/191030, Gennargentu 32TNK/192032)", "33TUH" if collection=="sentinel-2-l2a" else "192032")
                #elif collection=="landsat-c2-l2":
                        #path = st.text_input("Path (Sibillini 190/, Gennargentu 132)", "33TUH")
                        #row = st.text_input("Sentinel-2 tile (Sibillini 33TUH, Gennargentu 32TNK)", "33TUH")
                #search_start = st.date_input("Start date", "2023-01-01")
                search_period = st.date_input("Search period", (datetime.date(2023, 1, 1), datetime.date(2023, 12, 31)))
                search_period = [date.strftime("%Y-%m-%d") for date in search_period]
                cloud_cover = st.number_input("Cloud Cover", min_value=0, max_value=100, step=5, value=10)
                        #pc_button = st.form_submit_button(label='Submit')

        show_sat = st.checkbox("Show Sat Imagery")

        if show_sat:
                try:
                        catalog = pystac_client.Client.open(
                                "https://planetarycomputer.microsoft.com/api/stac/v1",
                                modifier=pc.sign_inplace)

                        if collection=="sentinel-2-l2a":
                                search = catalog.search(
                                        collections=[collection],
                                        query = {"s2:mgrs_tile": dict(eq=tile),
                                                "eo:cloud_cover": {"lt": cloud_cover}},
                                        datetime=[search_period[0], search_period[1]],
                                        )
                        elif collection=="landsat-c2-l2":
                                search = catalog.search(
                                        collections=[collection],
                                        query = {"landsat:wrs_path": dict(eq=tile[:3]),
                                                "landsat:wrs_row": dict(eq=tile[3:]),
                                                "eo:cloud_cover": {"lt": cloud_cover}},
                                        datetime=[search_period[0], search_period[1]],
                                        )

                        ic = search.item_collection_as_dict()
                except:
                        st.markdown("Sometimes Planetary Computer does not like us...The request exceeded the maximum allowed time. Please try again later!")


                st.markdown(f'**Found {len(ic["features"])} items for {tile}**')
                if len(ic["features"])>1:
                        n_sat = st.slider("", min_value=1, max_value=len(ic["features"]), value=1)
                else: n_sat = 1
                n_sat = (len(ic["features"])+1) - n_sat
                st.markdown(f'**Selected Item:    {ic["features"][n_sat-1]["properties"]["datetime"][:10]}**')
                pos_bands = [["B02", "B03", "B04", "B05", "B06", "B06", "B07", "B08", "B11", "B12", "SCL", "NDVI"], 
                        ["red", "blue", "green", "nir08", "swir16", "swir22", "NDVI"]]
                #band = st.multiselect("Bands", pos_bands[0] if collection=="sentinel-2-l2a" else pos_bands[1], default="NDVI")
                band = st.text_input("Band, Band Combination, NDVI or an expression", "NDVI")
                



side.markdown("You can fin further information on usage and data [here](https://github.com/benehiebl/maps_traceve)")



m2 = leafmap.Map(basemap="Esri.WorldImagery", height=2000)#, height="1000px", width="1500px")
m2.add_basemap("Esri.WorldTopoMap")
m2.add_basemap("Esri.WorldImagery")

if show_sat:
        if band.startswith("exp:"):
                st.write(band[4:])
                m2.add_stac_layer(collection=collection,
                              item=ic["features"][n_sat-1]["id"],
                              expression=band[4:],
                              rescale="-1,1",
                              colormap_name="reds",
                              #vmin=0, vmax=1,
                              name=band)  
                m2.add_colormap(label=band,
                                cmap="Reds",
                                vmin=-1, vmax=1, position=(25,1), width=3, height=0.2, label_size=9, transparent=True)
        if band=="NDVI":
                m2.add_stac_layer(collection=collection,
                              item=ic["features"][n_sat-1]["id"],
                              expression="(B08-B04)/(B08+B04)" if collection=="sentinel-2-l2a" else "(nir08-red)/(nir08+red)",
                              rescale="-1,1",
                              colormap_name="brg",
                              vmin=0, vmax=1,
                              name="NDVI")  
                m2.add_colormap(label="NDVI",
                                cmap="brg",
                                vmin=-1, vmax=1, position=(25,1), width=3, height=0.2, label_size=9, transparent=True)
        else:
                m2.add_stac_layer(collection=collection,
                              item=ic["features"][n_sat-1]["id"],
                              #expression=band,
                              assets=band,
                              name=str(band))


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
m2.to_streamlit(height=800)
#st_data = st_folium(m2, height=1000)
