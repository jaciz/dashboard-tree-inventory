from enum import auto
from numpy.core.numeric import NaN
from plotly import plot
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import pydeck as pdk
import os
import base64
import s3fs

# # Create connection object.
# # `anon=False` means not anonymous, i.e. it uses access keys to pull data.
# fs = s3fs.S3FileSystem(anon=False)

# # Retrieve file contents.
# # Uses st.cache to only rerun when the query changes or after 10 min.
# @st.cache(ttl=600)
# def read_file(filename):
#     with fs.open(filename) as f:
#         return f.read().decode("utf-8")

# content = read_file(r"s3://dashboard-tree-inventory/sample.csv")


# network centerline shapefiles
# network1 = gpd.read_file()
# network2 = gpd.read_file()


# vegetation data
veg1 = pd.read_csv(r'data/ElNido_TreeCounts.csv')
veg2 = pd.read_csv(r'data/BarreVillaPark_TreeCounts.csv')
df1 = veg1[['VEG_ID', 'LONGITUDE', 'LATITUDE', 'HEIGHT', 'AVG_SPREAD','TREE_SPECIES','LAST_TRIMMED']]
df2 = veg2[['VEG_ID', 'LONGITUDE','LATITUDE', 'HEIGHT', 'AVG_SPREAD','TREE_SPECIES','LAST_TRIMMED']]


locations = {'El Nido-La Cienega': df1,'Barre-Villa Park': df2}
initial_latlong = {'El Nido-La Cienega': [-118.3697,33.9710],'Barre-Villa Park': [-117.9146,33.80742]}




# page layout details
st.set_page_config(page_title='Vegetation Violations Inventory', page_icon="🌲", layout='wide')

st.title('Tree Inventory')
st.write('Please use the dropdowns and sliders to modify which circuits you would like to see the tree inventory for.')

# sidebar
# logo and adding link to logo image
@st.cache(allow_output_mutation=True)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

@st.cache(allow_output_mutation=True)
def get_img_with_href(local_img_path, target_url):
    img_format = os.path.splitext(local_img_path)[-1].replace('.', '')
    bin_str = get_base64_of_bin_file(local_img_path)
    html_code = f'''
        <a href="{target_url}">
            <img src="data:image/{img_format};base64,{bin_str}" />
        </a>'''
    return html_code

png_html = get_img_with_href('data/Geo1_TreeViewer_Logo1.png', 'http://www.geo1.com')


# sidebar components
st.sidebar.markdown(png_html, unsafe_allow_html=True)
#st.sidebar.image(r'data/Geo1_TreeViewer_Logo2.png', use_column_width=True)
st.sidebar.write("")
st.sidebar.write("")
st.sidebar.header('1. Which Area Would You Like to View and Filter?')
circuits = st.sidebar.selectbox('Location', ('El Nido-La Cienega', 'Barre-Villa Park'))

st.sidebar.header('2. Tree Species')
plant_species = locations[circuits]['TREE_SPECIES'].unique()
checkmark_list = {}
for species in plant_species:
    check = st.sidebar.checkbox(species, value=True)
    checkmark_list[species] = check

st.sidebar.header('3. Which Attributes Would You Like to View?')
options = st.sidebar.multiselect('Attributes',('Vegetation Height', 'Average Canopy Spread'))



# Add in attributes for deciduous and coniferous as a selection? or dropdown
# Add in attributes for what type of tree it is: Palm Tree, etc.


veg_height_slider = 0
canopy_spread_slider = 0
st.sidebar.header('4. Filters')
if 'Vegetation Height' in options:
    veg_height_slider = st.sidebar.slider('Vegetation Height (feet)', locations[circuits]['HEIGHT'].min(), locations[circuits]['HEIGHT'].max(), (float(locations[circuits]['HEIGHT'].min()), float(locations[circuits]['HEIGHT'].max())), 0.1)
if 'Average Canopy Spread' in options:
    canopy_spread_slider = st.sidebar.slider('Average Canopy Spread (feet)', locations[circuits]['AVG_SPREAD'].min(), locations[circuits]['AVG_SPREAD'].max(), (float(locations[circuits]['AVG_SPREAD'].min()), float(locations[circuits]['AVG_SPREAD'].max())), 0.1)

attributes = {'Vegetation Height':locations[circuits]['HEIGHT'], 'Average Canopy Spread':locations[circuits]['HEIGHT']}



# graph components 
# custom color function
def hex_to_RGB(hex):
    ''' "#FFFFFF" -> [255,255,255] '''
    # Pass 16 to the integer function for change of base
    return [int(hex[i:i+2], 16) for i in range(1,6,2)]
# https://bsouthga.dev/posts/color-gradients-with-python
def linear_gradient(df_length, start_hex, finish_hex="#FFFFFF"):
    ''' returns a gradient list of (n) colors between
    two hex colors. start_hex and finish_hex
    should be the full six-digit color string,
    including the number sign ("#FFFFFF") '''
    # Starting and ending colors in RGB form
    s = hex_to_RGB(start_hex)
    f = hex_to_RGB(finish_hex)
    # Initilize a list of the output colors with the starting color
    RGB_list = [s]
    # Calcuate a color at each evenly spaced value of t from 1 to n
    for t in range(1, df_length):
        # Interpolate RGB vector for color at the current value of t
        curr_vector = [
        int(s[j] + (float(t)/(df_length-1))*(f[j]-s[j]))
        for j in range(3)
        ]
        # Add it to our list of output colors
        RGB_list.append(curr_vector)
    return RGB_list

def pydeck_map(df, lat, long):
    df = df.sort_values(by=['HEIGHT']).reset_index(drop=True)
    color_df = pd.DataFrame(linear_gradient(len(df), "#FAF3DD", "#4A7C59"), columns=['r','g','b'])
    #df = df.drop(columns=['r','g','b'])
    df = pd.concat([df, color_df], axis = 1)
    return st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=lat,
            longitude=long,
            zoom=13,
            pitch=0),
            layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=df,
                get_position=['LONGITUDE', 'LATITUDE'],
                auto_highlight=True,
                get_color=['r','g','b'],
                get_radius=20,
                radius_max_pixels=6,
                radius_min_pixels=2,
                radius_scale = 2,
                pickable=True,
            ),
            # pdk.Layer(
            #     "LineLayer"
            # )
        ],
        tooltip={"html": "<b>Vegetation ID: </b> {VEG_ID}<br><b>Longitude: </b> {LONGITUDE}<br><b>Latitude: </b> {LATITUDE}<br><b>Species: </b> {TREE_SPECIES}<br><b>Tree Height: </b> {HEIGHT} ft<br><b>Average Canopy Spread: </b> {AVG_SPREAD} ft</br><b>Last Trimmed Date: </b> {LAST_TRIMMED}</br>", "style": {"color": "white"}}
    ))

def histogram(df):
    fig = px.histogram(df['HEIGHT'], color_discrete_sequence=['#013220'])
    fig.update_layout(
    margin=dict(l=10, r=10, t=0, b=0),
    yaxis=dict(
        title_text="Count",
        titlefont=dict(size=15),
    ),
    xaxis=dict(
        title_text="Vegetation Height",
        titlefont=dict(size=15)
    ),
    showlegend=False,
    bargap = 0.02,
    )
    fig.update_traces(
    hovertemplate="<b>Vegetation Heights:</b> %{x} ft" + "<br><b>Count:</b> %{y}</br>")
    return st.plotly_chart(fig, use_container_width=True)

def dataframe_table(df):
    return st.dataframe(df, height = 410)




# functionalities 
def choose_coloring():
    # split update_map() into smaller methods
    pass

def update_points_filtering_color(df):
    # split update_map() into smaller methods
    pass

def update_map():
    true_species=[]
    for key,value in checkmark_list.items():
        if value==True:
            true_species.append(key)

    if len(true_species) == 0:
        return st.info("**Error**: No data available to display, please select a tree species")
    else:
        filtered_species_df = locations[circuits][locations[circuits]['TREE_SPECIES'].isin(true_species)]
    
        if (veg_height_slider == 0) and (canopy_spread_slider == 0):
            return pydeck_map(filtered_species_df, initial_latlong[circuits][1], initial_latlong[circuits][0])

        if (veg_height_slider == 0) and (canopy_spread_slider != 0):
            if canopy_spread_slider[0] == canopy_spread_slider[1]:
                return st.info("**Error**: No data available to display, please input a range")
            filtered_df = filtered_species_df.loc[(filtered_species_df['AVG_SPREAD']>=canopy_spread_slider[0]) & (filtered_species_df['AVG_SPREAD']<=canopy_spread_slider[1])]
            if len(filtered_df)==0:
                return st.info("**Error**: No data available to display, please input another range")
            else:
                return pydeck_map(filtered_df, initial_latlong[circuits][1], initial_latlong[circuits][0])

        if (veg_height_slider != 0) and (canopy_spread_slider == 0):
            if veg_height_slider[0] == veg_height_slider[1]:
                return st.info("**Error**: No data available to display, please input a range")
            filtered_df = filtered_species_df.loc[(filtered_species_df['HEIGHT']>=veg_height_slider[0]) & (filtered_species_df['HEIGHT']<=veg_height_slider[1])]
            if len(filtered_df)==0:
                return st.info("**Error**: No data available to display, please input another range")
            else:
                return pydeck_map(filtered_df, initial_latlong[circuits][1], initial_latlong[circuits][0])

        if (veg_height_slider !=0) and (canopy_spread_slider != 0):
            if (veg_height_slider[0] == veg_height_slider[1]) or (canopy_spread_slider[0] == canopy_spread_slider[1]):
                return st.info("**Error**: No data available to display, please input a range")
            filtered_df = filtered_species_df.loc[((filtered_species_df['HEIGHT']>=veg_height_slider[0]) & (filtered_species_df['HEIGHT']<=veg_height_slider[1]))]
            filtered_df2 = filtered_df[(filtered_df['AVG_SPREAD']>=canopy_spread_slider[0]) & (filtered_df['AVG_SPREAD']<=canopy_spread_slider[1])]
            if len(filtered_df2)==0:
                return st.info("**Error**: No data available to display, please input another range")
            else:
                return pydeck_map(filtered_df2, initial_latlong[circuits][1], initial_latlong[circuits][0])

def update_graph(df):
    true_species=[]
    for key,value in checkmark_list.items():
        if value==True:
            true_species.append(key)

    if len(true_species) == 0:
        return st.info("**Error**")
    else:
        filtered_species_df = df[df['TREE_SPECIES'].isin(true_species)]
        
        if (veg_height_slider == 0) and (canopy_spread_slider == 0):
            return histogram(filtered_species_df)

        if (veg_height_slider == 0) and (canopy_spread_slider != 0):
            if canopy_spread_slider[0] == canopy_spread_slider[1]:
                return st.info("**Error**")
            filtered_df = filtered_species_df.loc[(filtered_species_df['AVG_SPREAD']>=canopy_spread_slider[0]) & (filtered_species_df['AVG_SPREAD']<=canopy_spread_slider[1])]
            if len(filtered_df)==0:
                return st.info("**Error**")
            else:
                return histogram(filtered_df)

        if (veg_height_slider != 0) and (canopy_spread_slider == 0):
            if veg_height_slider[0] == veg_height_slider[1]:
                return st.info("**Error**")
            filtered_df = filtered_species_df.loc[(filtered_species_df['HEIGHT']>=veg_height_slider[0]) & (filtered_species_df['HEIGHT']<=veg_height_slider[1])]
            if len(filtered_df)==0:
                return st.info("**Error**")
            else:
                return histogram(filtered_df)

        if (veg_height_slider !=0) and (canopy_spread_slider != 0):
            if (veg_height_slider[0] == veg_height_slider[1]) or (canopy_spread_slider[0] == canopy_spread_slider[1]):
                return st.info("**Error**")
            filtered_df = filtered_species_df.loc[((filtered_species_df['HEIGHT']>=veg_height_slider[0]) & (filtered_species_df['HEIGHT']<=veg_height_slider[1]))]
            filtered_df2 = filtered_df[(filtered_df['AVG_SPREAD']>=canopy_spread_slider[0]) & (filtered_df['AVG_SPREAD']<=canopy_spread_slider[1])]
            if len(filtered_df2)==0:
                return st.info("**Error**")
            else:
                return histogram(filtered_df2)

def update_table(df):
    true_species=[]
    for key,value in checkmark_list.items():
        if value==True:
            true_species.append(key)

    if len(true_species) == 0:
        return st.info("**Error**")
    else:
        filtered_species_df = df[df['TREE_SPECIES'].isin(true_species)]
        
        if (veg_height_slider == 0) and (canopy_spread_slider == 0):
            return dataframe_table(filtered_species_df)

        if (veg_height_slider == 0) and (canopy_spread_slider != 0):
            if canopy_spread_slider[0] == canopy_spread_slider[1]:
                return st.info("**Error**")
            filtered_df = filtered_species_df.loc[(filtered_species_df['AVG_SPREAD']>=canopy_spread_slider[0]) & (filtered_species_df['AVG_SPREAD']<=canopy_spread_slider[1])]
            if len(filtered_df)==0:
                return st.info("**Error**")
            else:
                return dataframe_table(filtered_df)

        if (veg_height_slider != 0) and (canopy_spread_slider == 0):
            if veg_height_slider[0] == veg_height_slider[1]:
                return st.info("**Error**")
            filtered_df = filtered_species_df.loc[(filtered_species_df['HEIGHT']>=veg_height_slider[0]) & (filtered_species_df['HEIGHT']<=veg_height_slider[1])]
            if len(filtered_df)==0:
                return st.info("**Error**")
            else:
                return dataframe_table(filtered_df)

        if (veg_height_slider !=0) and (canopy_spread_slider != 0):
            if (veg_height_slider[0] == veg_height_slider[1]) or (canopy_spread_slider[0] == canopy_spread_slider[1]):
                return st.info("**Error**")
            filtered_df = filtered_species_df.loc[((filtered_species_df['HEIGHT']>=veg_height_slider[0]) & (filtered_species_df['HEIGHT']<=veg_height_slider[1]))]
            filtered_df2 = filtered_df[(filtered_df['AVG_SPREAD']>=canopy_spread_slider[0]) & (filtered_df['AVG_SPREAD']<=canopy_spread_slider[1])]
            if len(filtered_df2)==0:
                return st.info("**Error**")
            else:
                return dataframe_table(filtered_df2)

#def species_update_map():
    true_species=[]
    for key,value in checkmark_list.items():
        if value==True:
            true_species.append(key)

    if len(true_species) == 0:
        return st.write("No species selected")
    else:
        filtered_df = locations[circuits][locations[circuits]['TREE_SPECIES'].isin(true_species)]
        return pydeck_map(filtered_df, initial_latlong[circuits][1], initial_latlong[circuits][0])



conditions = {
        'cond1':eval('(veg_height_slider == 0) and (canopy_spread_slider == 0)'),
        'cond2':eval('(veg_height_slider == 0) and (canopy_spread_slider != 0)'),
        'cond3':eval('(veg_height_slider != 0) and (canopy_spread_slider == 0)'),
        'cond4':eval('(veg_height_slider !=0) and (canopy_spread_slider != 0)'),
    }

def display_number_filtered():
    true_species=[]
    for key,value in checkmark_list.items():
        if value==True:
            true_species.append(key)

    if len(true_species) == 0:
        pass
    else:
        filtered_species_df = locations[circuits][locations[circuits]['TREE_SPECIES'].isin(true_species)]

        if conditions['cond1']:
            return st.write('**The number of trees displayed: ** ' + str(len(filtered_species_df)))
        if conditions['cond2']:
            if canopy_spread_slider[0] == canopy_spread_slider[1]:
                pass
            else:
                filtered_df = filtered_species_df.loc[(filtered_species_df['AVG_SPREAD']>=canopy_spread_slider[0]) & (filtered_species_df['AVG_SPREAD']<=canopy_spread_slider[1])]
                return st.write('**The number of trees displayed: ** ' + str(len(filtered_df)))
        if conditions['cond3']:
            if veg_height_slider[0] == veg_height_slider[1]:
                pass
            else:
                filtered_df = filtered_species_df.loc[(filtered_species_df['HEIGHT']>=veg_height_slider[0]) & (filtered_species_df['HEIGHT']<=veg_height_slider[1])]
                return st.write('**The number of trees displayed: ** ' + str(len(filtered_df)))
        if conditions['cond4']:
            if (veg_height_slider[0] == veg_height_slider[1]) or (canopy_spread_slider[0] == canopy_spread_slider[1]):
                pass
            else:
                filtered_df = filtered_species_df.loc[((filtered_species_df['HEIGHT']>=veg_height_slider[0]) & (filtered_species_df['HEIGHT']<=veg_height_slider[1]))]
                filtered_df2 = filtered_df[(filtered_df['AVG_SPREAD']>=canopy_spread_slider[0]) & (filtered_df['AVG_SPREAD']<=canopy_spread_slider[1])]
                return st.write('**The number of trees displayed: ** ' + str(len(filtered_df2)))






# run all functions
display_number_filtered()
update_map()


col1, col2 = st.columns([2,1])
with col1:
    st.write("**Vegetation Height Histogram**")
    update_graph(locations[circuits])

with col2:
    st.write("**Table**")
    update_table(locations[circuits])
    download = st.download_button(label = f'📥 Download Full Table', data=locations[circuits].to_csv(), file_name=f"{circuits}_treecounts.csv")




# if st.button('Reset Map View'):
#     pydeck_map(locations[circuits], 0, 0)
#     pdk.data_utils.viewport_helpers.compute_view(locations[circuits])


