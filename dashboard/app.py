import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import pandas as pd
import pydeck as pdk
from PIL import Image

# Design
st.set_page_config(page_title="Alertas Sismicas",
                   page_icon="bar_chart:",
                   layout="wide")

result=st.experimental_get_query_params() #Get params of url

country=result['val'][0]
latitude=result['val'][1]
longitude=result['val'][2]
depth=result['val'][3]
mag=result['val'][4]
sistype=result['val'][5]

# Creating layout
if sistype=='leve':
    level='Leve :large_green_circle:'
    delta='ML'
    rgba='[0,204,0,160]'
    recm='bajo.jpeg'
elif sistype=='medio':
    level='Medio :large_yellow_circle:'
    delta='ML'
    rgba='[255,255,0,160]'
    recm='medio.jpeg'
elif sistype=='alto':
    level='Alto :red_circle:'
    delta='-ML'
    rgba='[255,0,0,160]'
    recm='alto.jpeg'
else:
    level=':white_circle: Desconocido'
    delta='ML'
    rgba='[255,255,0,160]'
    recm='bajo.jpeg'

if country=='usa':
    flag=':flag-us:'
elif country=='japon':
    flag=':flag-jp:'
elif country=='chile':
    flag=':flag-cl:'
else:
    flag=':flag-us:'

# Load the credentials from secrets.toml
creds = st.secrets["gcp"]

# Authorize the client with the retrieved credentials
client = gspread.service_account_from_dict(creds)

# Open the Google Sheet by its title or URL
sheet = client.open("Feedback usuario (respuestas)")

# Access the specific worksheet within the sheet
worksheet = sheet.get_worksheet(0)

menu = ['Home', 'Feedback']
choice = st.sidebar.selectbox("Menu", menu)

if choice=='Home':
    st.markdown('# {0} Intensidad: {1}'.format(flag, level)) #Level
    st.markdown('***')
    d={'lat':[float(latitude)], 'lon':[float(longitude)]}
    df=pd.DataFrame(d)
    col1,col2,col3=st.columns(3)
    col1.metric(label='Magnitud', value=mag, delta=delta)
    col2.metric(label='Profundidad', value=depth, delta='Km')
    col3.markdown('## [Ver últimos 20 :eye:](https://us-central1-alerta-sismos-386306.cloudfunctions.net/function-mongo)')

    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
        latitude=float(latitude),
        longitude=float(longitude),
        zoom=5,
        pitch=50,
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=df,
            get_position='[lon, lat]',
            get_color=rgba,
            get_radius=float(mag)*8000,
            ),
        ],
    ))

    #Recommendations
    st.markdown('***')
    st.markdown('## Recomendaciones')
    image = Image.open('infografia.png')
    image_b=Image.open(recm)
    st.image(image_b)
    st.image(image)

if choice=='Feedback':
    st.subheader('Ayúdanos a mejorar...')
    with st.form(key='formulario'):
        fecha = datetime.datetime.now()
        formatted_datetime = fecha.strftime('%d/%m/%y %H:%M:%S')
        input1 = st.selectbox('Sentiste el ultimo sismo?', options=['Sí', 'No'])
        input2 = st.selectbox("Califica nuestros servicios (bajo 1 y alto 5)", options=['1', '2', '3', '4', '5'])
        input3 = st.selectbox('Compartirías nuestra aplicación?', options=['Sí', 'No'])
        input4 = st.text_area('Algún comentario de mejora?')

        row = [formatted_datetime, input1, input2, input3, input4]
        boton = st.form_submit_button(label='Subir')
    if boton:
        st.success('Has subido tu información con éxito!')
        worksheet.append_row(row)
