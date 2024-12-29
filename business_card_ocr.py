import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import mysql.connector
import io



# connect the database
mydb=mysql.connector.connect(
    user='admin',
    host='localhost',
    password='12345',auth_plugin='mysql_native_password')

mycursor=mydb.cursor()
mycursor.execute('CREATE DATABASE if not exists bizcardx_db')
mycursor.execute('Use bizcardx_db')

#tittle
st.markdown("<h1 style='text-align: center; color: blue ;'>Extracting Business Card Data with OCR </h1>", unsafe_allow_html=True)


# extract the data
def extracted_text(picture):
    ext_dic = {'Name': [], 'Designation': [], 'Company name': [], 'Contact': [], 'Email': [], 'Website': [],
               'Address': [], 'Pincode': []}

    ext_dic['Name'].append(result[0])
    ext_dic['Designation'].append(result[1])

    for m in range(2, len(result)):
        if result[m].startswith('+') or (result[m].replace('-', '').isdigit() and '-' in result[m]):
            ext_dic['Contact'].append(result[m])

        elif '@' in result[m] and '.com' in result[m]:
            small = result[m].lower()
            ext_dic['Email'].append(small)

        elif 'www' in result[m] or 'WWW' in result[m] or 'wwW' in result[m]:
            small = result[m].lower()
            ext_dic['Website'].append(small)

        elif 'TamilNadu' in result[m] or 'Tamil Nadu' in result[m] or result[m].isdigit():
            ext_dic['Pincode'].append(result[m])

        elif re.match(r'^[A-Za-z]', result[m]):
            ext_dic['Company name'].append(result[m])

        else:
            removed_colon = re.sub(r'[,;]', '', result[m])
            ext_dic['Address'].append(removed_colon)

    for key, value in ext_dic.items():
        if len(value) > 0:
            concatenated_string = ' '.join(value)
            ext_dic[key] = [concatenated_string]
        else:
            value = 'NA'
            ext_dic[key] = [value]

    return ext_dic


#if selected == "Image":
image = st.file_uploader(label="Upload the image", type=['png', 'jpg', 'jpeg'], label_visibility="hidden")
@st.cache_data
def load_image():
    reader = easyocr.Reader(['en'], model_storage_directory=".")
    return reader
reader_1 = load_image()
if image is not None:
    input_image = Image.open(image)
    # Setting Image size
    st.image(input_image, width=350, caption='Uploaded Image')
    st.markdown(
        f'<style>.css-1aumxhk img {{ max-width: 300px; }}</style>',
        unsafe_allow_html=True
    )
    result = reader_1.readtext(np.array(input_image), detail=0)
    # creating dataframe
    ext_text = extracted_text(result)
    df = pd.DataFrame(ext_text)
    st.dataframe(df)
    # Converting image into bytes
    image_bytes = io.BytesIO()
    input_image.save(image_bytes, format='PNG')
    image_data = image_bytes.getvalue()
    # Creating dictionary
    data = {"Image": [image_data]}
    df_1 = pd.DataFrame(data)
    concat_df = pd.concat([df, df_1], axis=1)
    # Database
    col1, col2, col3 = st.columns([1, 6, 1])
        
    col_1, col_2 = st.columns([4, 4])
    with col_1:
        modified_n = st.text_input('Name', ext_text["Name"][0])
        modified_d = st.text_input('Designation', ext_text["Designation"][0])
        modified_c = st.text_input('Company name', ext_text["Company name"][0])
        modified_con = st.text_input('Mobile', ext_text["Contact"][0])
        concat_df["Name"], concat_df["Designation"], concat_df["Company name"], concat_df[
            "Contact"] = modified_n, modified_d, modified_c, modified_con
    with col_2:
        modified_m = st.text_input('Email', ext_text["Email"][0])
        modified_w = st.text_input('Website', ext_text["Website"][0])
        modified_a = st.text_input('Address', ext_text["Address"][0][1])
        modified_p = st.text_input('Pincode', ext_text["Pincode"][0])
        concat_df["Email"], concat_df["Website"], concat_df["Address"], concat_df[
            "Pincode"] = modified_m, modified_w, modified_a, modified_p
    col3, col4 = st.columns([4, 4])
    
    with col4:
        Upload = st.button("Upload")
   
    if Upload:
        with st.spinner("In progress"):
            mycursor.execute(
                "CREATE TABLE IF NOT EXISTS BUSINESS_CARD(NAME VARCHAR(50), DESIGNATION VARCHAR(100), "
                "COMPANY_NAME VARCHAR(100), CONTACT VARCHAR(35), EMAIL VARCHAR(100), WEBSITE VARCHAR("
                "100), ADDRESS TEXT, PINCODE VARCHAR(100))")
            mydb.commit()
            A = "INSERT INTO BUSINESS_CARD(NAME, DESIGNATION, COMPANY_NAME, CONTACT, EMAIL, WEBSITE, ADDRESS, " \
                "PINCODE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            for index, i in concat_df.iterrows():
                result_table = (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7])
                mycursor.execute(A, result_table)
                mydb.commit()
                st.success('SUCCESSFULLY UPLOADED', icon="✅")
    
else:
    st.write("Upload an image")
