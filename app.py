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



# data
dysart = pd.read_csv(r'data/GEO_Dysart_20210408_grow15_fall5.csv')
sample = pd.read_csv(r'data/sample.csv')
df1 = dysart[['longitude', 'latitude', 'vegetation_height', 'h_conductor']]
df2 = sample[['longitude','latitude', 'vegetation_height', 'h_conductor']]

locations = {'Dysart': df1,'Goleta Santa Clara No. 1': df2}
initial_latlong = {'Dysart': [-116.9083,33.9057],'Goleta Santa Clara No. 1': [-118.6730,37.5728]}


# page layout details
st.set_page_config(page_title='Vegetation Violations Inventory', page_icon="🌲", layout='wide')

st.title('Tree Inventory')
st.write('Please use the dropdowns and sliders to modify which circuits you would like to see the tree inventory for.')


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
    df = df.sort_values(by=['vegetation_height']).reset_index(drop=True)
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
                get_position=['longitude', 'latitude'],
                auto_highlight=True,
                get_color=['r','g','b'],
                get_radius=20,
                radius_max_pixels=6,
                radius_min_pixels=2,
                radius_scale = 2,
                pickable=True,
            )
        ],
        tooltip={"html": "<b>Tree Height: </b> {vegetation_height} ft<br><b>Conductor Height: </b> {h_conductor} ft</br>", "style": {"color": "white"}}
    ))

def histogram(df):
    fig = px.histogram(df['vegetation_height'])
    return st.plotly_chart(fig, use_container_width=True)


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

png_html = get_img_with_href('data/geologo_removed.png', 'www.geo1.com')


# sidebar components
#st.sidebar.markdown(png_html, unsafe_allow_html=True)
st.sidebar.image(r'data/geologo_removed.png', use_column_width=True)

st.sidebar.header('1. Which Area Would You Like to View and Filter?')
circuits = st.sidebar.selectbox('Location', ('Dysart', 'Goleta Santa Clara No. 1'))

st.sidebar.header('2. Which Attributes Would You Like to View?')
options = st.sidebar.multiselect('Attributes',('Vegetation Height', 'Conductor Height'))

veg_height_slider = 0
conductor_height_slider = 0
st.sidebar.header('3. Filters')
if 'Vegetation Height' in options:
    veg_height_slider = st.sidebar.slider('Vegetation Height (feet)', locations[circuits].vegetation_height.min(), locations[circuits].vegetation_height.max(), (float(locations[circuits].vegetation_height.min())+3, float(locations[circuits].vegetation_height.max())-3), 0.1)
if 'Conductor Height' in options:
    conductor_height_slider = st.sidebar.slider('Conductor Height (feet)', locations[circuits].h_conductor.min(), locations[circuits].h_conductor.max(), (float(locations[circuits].h_conductor.min())+3, float(locations[circuits].h_conductor.max())-3), 0.1)
#with st.sidebar.header('4. Download Your Data'):
    #downloaded_files = st.download_button(label = '📥 Download Current Result', data=df.loc[(df['vegetation_height']>=veg_height_slider[0]) & (df['vegetation_height']<=veg_height_slider[1])].to_csv(),filename = "my_tree_results.csv")


# functionalities 
def choose_coloring():
    # split update_map() into smaller methods
    pass

def update_points_filtering_color(df):
    # split update_map() into smaller methods
    pass

def update_map():
    if (veg_height_slider == 0) and (conductor_height_slider == 0):
        return pydeck_map(locations[circuits], initial_latlong[circuits][1], initial_latlong[circuits][0])

    
    if (veg_height_slider == 0) and (conductor_height_slider != 0):
        if conductor_height_slider[0] == conductor_height_slider[1]:
            return st.info("**Error**: No data available to display, please input a range")
        else:
            filtered_df = locations[circuits].loc[(locations[circuits]['h_conductor']>=conductor_height_slider[0]) & (locations[circuits]['h_conductor']<=conductor_height_slider[1])]
            return pydeck_map(filtered_df, initial_latlong[circuits][1], initial_latlong[circuits][0])

    if (veg_height_slider != 0) and (conductor_height_slider == 0):
        if veg_height_slider[0] == veg_height_slider[1]:
            return st.info("**Error**: No data available to display, please input a range")
        else:
            filtered_df = locations[circuits].loc[(locations[circuits]['vegetation_height']>=veg_height_slider[0]) & (locations[circuits]['vegetation_height']<=veg_height_slider[1])]
            return pydeck_map(filtered_df, initial_latlong[circuits][1], initial_latlong[circuits][0])

    if (veg_height_slider !=0) and (conductor_height_slider != 0):
        if (veg_height_slider[0] == veg_height_slider[1]) or (conductor_height_slider[0] == conductor_height_slider[1]):
            return st.info("**Error**: No data available to display, please input a range")
        else:
            filtered_df = locations[circuits].loc[((locations[circuits]['vegetation_height']>=veg_height_slider[0]) & (locations[circuits]['vegetation_height']<=veg_height_slider[1]))]
            filtered_df2 = filtered_df[(filtered_df['h_conductor']>=conductor_height_slider[0]) & (filtered_df['h_conductor']<=conductor_height_slider[1])]
            return pydeck_map(filtered_df2, initial_latlong[circuits][1], initial_latlong[circuits][0])

def update_graph(df):
    if (veg_height_slider == 0) and (conductor_height_slider == 0):
        return histogram(df)
    else:
        return histogram(df.loc[(df['vegetation_height']>=veg_height_slider[0]) & (df['vegetation_height']<=veg_height_slider[1])])

def display_number_filtered():
    if (veg_height_slider == 0) and (conductor_height_slider == 0):
        return st.write('**The number of trees displayed: ** ' + str(len(locations[circuits])))
    
    if (veg_height_slider == 0) and (conductor_height_slider != 0):
        if conductor_height_slider[0] == conductor_height_slider[1]:
            pass
        else:
            filtered_df = locations[circuits].loc[(locations[circuits]['h_conductor']>=conductor_height_slider[0]) & (locations[circuits]['h_conductor']<=conductor_height_slider[1])]
            return st.write('**The number of trees displayed: ** ' + str(len(locations[circuits])))

    if (veg_height_slider != 0) and (conductor_height_slider == 0):
        if veg_height_slider[0] == veg_height_slider[1]:
            pass
        else:
            filtered_df = locations[circuits].loc[(locations[circuits]['vegetation_height']>=veg_height_slider[0]) & (locations[circuits]['vegetation_height']<=veg_height_slider[1])]
            return st.write('**The number of trees displayed: ** ' + str(len(filtered_df)))

    if (veg_height_slider !=0) and (conductor_height_slider != 0):
        if (veg_height_slider[0] == veg_height_slider[1]) or (conductor_height_slider[0] == conductor_height_slider[1]):
            pass
        else:
            filtered_df = locations[circuits].loc[((locations[circuits]['vegetation_height']>=veg_height_slider[0]) & (locations[circuits]['vegetation_height']<=veg_height_slider[1]))]
            filtered_df2 = filtered_df[(filtered_df['h_conductor']>=conductor_height_slider[0]) & (filtered_df['h_conductor']<=conductor_height_slider[1])]
            return st.write('**The number of trees displayed: ** ' + str(len(filtered_df2)))


# run all functions
display_number_filtered()
update_map()
#update_graph(locations[circuits])


# if st.button('Reset Map View'):
#     pydeck_map(locations[circuits], 0, 0)
#     pdk.data_utils.viewport_helpers.compute_view(locations[circuits])


