import cv2
import streamlit as st
import base64
import numpy as np
import pandas as pd
import base64
import io
from io import BytesIO
import matplotlib.pyplot as plt
import time

def empty_space(num_lines=1):
    """Adds empty lines to the Streamlit app."""
    for _ in range(num_lines):
        st.write("")

def stream_data(assitance_response:str):
    for word in assitance_response.split(" "):
        yield word + " "
        time.sleep(0.022)

# Function to display the logo at the center
def display_logo_center(logo_image_file):
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; height: 150px;">
        <img src="data:image/png;base64,{base64.b64encode(open(logo_image_file, 'rb').read()).decode()}" width="200">
    </div>
    """, unsafe_allow_html=True)
    
#Function to add app background image
def add_bg_from_local(image_file):
     with open(image_file, "rb") as image_file:
         encoded_string = base64.b64encode(image_file.read())
     st.markdown(f"""<style>.stApp {{background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
     background-size: cover}}</style>""", unsafe_allow_html=True)
     
def display_ocr_image(img, results):
    img_np = np.array(img)
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    font = cv2.FONT_HERSHEY_COMPLEX

    for index, detection in enumerate(results):
        top_left = tuple([int(val) for val in detection[0][0]])
        bottom_right = tuple([int(val) for val in detection[0][2]])
        cv2.rectangle(img_bgr, top_left, bottom_right, (57, 255, 20), thickness=2)
        cv2.putText(img_bgr, str(index), top_left, font, 1, (0, 0, 255), 2, cv2.LINE_AA)

    # Convert the image from BGR (OpenCV) to RGB (Streamlit)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)  
    st.image(img_rgb, channels="RGB", use_column_width=True) 


def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()
    
def convert_df_to_excel(df_dict):
    buffer = io.BytesIO()    
    writer = pd.ExcelWriter(buffer, engine='xlsxwriter')
    for file_name, df in df_dict.items(): 
        df.to_excel(writer, sheet_name=f'{file_name}', index=False)

    writer.close()
    return buffer

def get_user_info():
    headers = st.context.headers
    return dict(
        user_name=headers.get("X-Forwarded-Preferred-Username"),
        user_email=headers.get("X-Forwarded-Email"),
        user_id=headers.get("X-Forwarded-User"),
    )