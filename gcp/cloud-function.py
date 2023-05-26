import pymongo
import requests
from urllib.request import urlopen
import json as json
import numpy as np
import pandas as pd
import asyncio
from telegram import Bot
from sklearn.cluster import KMeans
import re
import emoji

def connect_to_mongodb():
    # Conexión a MongoDB Atlas
    client = pymongo.MongoClient("mongodb+srv://vansik:Dcshooes_4@cluster1.e3cwjp7.mongodb.net/Api_whatsaap?retryWrites=true&w=majority&serverSelectionTimeoutMS=50000")
    db = client["Api_whatsaap"]
    collection = db["Api"]

    return collection

def transformacion_usa(df):
    #elimino columnas innecesarias
    df= df.drop(columns=['magType', 'nst', 'gap', 'dmin', 'rms', 'net', 'id','updated','type', 'horizontalError', 'depthError', 'magError', 'magNst', 'status', 'locationSource', 'magSource'])
    #coloco todos los registros en minusculas
    df= df.applymap(lambda x: x.lower() if isinstance(x, str) else x)
    #Vamos a redondear las columnas de variables float
    df[['latitude','longitude','depth','mag']]=df[['latitude','longitude','depth','mag']].round(1)
    #eliminamos duplicados
    df= df.drop_duplicates()
    #agrego una columna "country" con el nombre del pais respectivo en caso que necesite identificar en procesos posteriores
    df['country']='usa'

    #cambiamos el formato de fecha para estandarizarla junto con los otros datasets
    df['time'] = pd.to_datetime(df['time'])
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    return df    

def transformacion_japon(df):
    #eliminamos las columnas que no vamos a utilizar
    df= df.drop(columns=['ctt','eid','rdt','ttl','ift','ser','anm','acd','maxi','int','json','en_ttl'])
    # Extraemos la información de la columna 'cod'
    df[['latitude', 'longitude', 'depth']] = df['cod'].str.extract(r'(\+[\d\.]+)\+(\d+\.\d+)\-(\d+)').astype(float)
    df = df.drop(columns='cod')

    #convertimos a float la columna "depth"
    df['depth'] = df['depth'].astype('float64')
    #dividimos por mil para llevar la unidad de medida a KM para mantener la misma en todos los datasets
    df['depth'] = (df['depth'] / 1000)
    df['mag'] = df['mag'].replace({'': np.nan}).astype('float64')
    #renombramos columnas
    df = df.rename(columns={'at': 'time', 'en_anm': 'place'})
    #reordenamos columnas
    orden = ['time', 'latitude', 'longitude', 'depth', 'mag', 'place']
    df = df[orden]

    #todo a minusculas
    df=df.applymap(lambda x: x.lower() if isinstance(x,str) else x)
    #agrego una columna "country" con el nombre del pais respectivo en caso que necesite identificar en procesos posteriores
    df['country']='japon'
    
    #Vamos a redondear las columnas de variables float
    df[['latitude','longitude','depth','mag']]=df[['latitude','longitude','depth','mag']].round(1)

    #reemplazamos los "ｍ不明" ("desconocido en español") de la columna "mag" por NaN
    df['mag'] = df['mag'].replace({'ｍ不明': np.nan, '': np.nan})
    
    #eliminamos duplicados
    df= df.drop_duplicates()
    
    #substituimos los Nones por NaN
    df['longitude'] = df['longitude'].replace({None: np.nan, '': np.nan})
    df['latitude'] = df['latitude'].replace({None: np.nan, '': np.nan})

    #cambiamos el formato de fecha para estandarizarla junto con los otros datasets
    df['time'] = pd.to_datetime(df['time'])
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')

    #elimino los registos nulos pero solo aquellos que son nulos en todas las columnas
    df = df.dropna(subset=['latitude', 'longitude', 'depth', 'mag','place'], how='all')
    df=df.head(1)
    return df    

def transformacion_chile(df):
    #Elminamos las columnas innecesarias y nos quedamos solo con la columna "events"
    df= df.drop(columns=['status_code','status_description'])

    #Extraemos la informacion y la adjuntamos al dataframe como nuevas columnas
    df['time']= df['events'].apply(lambda x : x['utc_date'])
    df['latitude']= df['events'].apply(lambda x : x['latitude'])
    df['longitude']=df['events'].apply(lambda x: x['longitude'])
    df['depth']=df['events'].apply(lambda x: x['depth'])
    df['mag']=df['events'].apply(lambda x: x['magnitude']['value'])
    df['place']=df['events'].apply(lambda x: x['geo_reference'])

    #Eliminamos la columna "events", ahora ya no la necesitamos
    df= df.drop(columns=['events'])

    #Pasamos todo a minusculas
    df= df.applymap(lambda x : x.lower() if isinstance(x,str) else x)
    #Agrego una columna "country" con el nombre del pais respectivo en caso que necesite identificar en procesos posteriores
    df['country']= 'chile'

    #convertimos el tipo de la columna "depth" a float para mantener la misma estructura en todos los datasets
    df['depth']= df['depth'].astype('Float64')
    #eliminamos duplicados
    df= df.drop_duplicates()
    #Vamos a redondear las columnas de variables float
    df[['latitude','longitude','depth','mag']]=df[['latitude','longitude','depth','mag']].round(1)

    #cambiamos el formato de fecha para estandarizarla junto con los otros datasets
    df['time'] = pd.to_datetime(df['time'])
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    df=df.head(1)
    return df

def etiquetado(df):
    #separamos los campos que quiero para ejecutar el modelo
    df = df.dropna()
    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    X= df[['depth','mag']]
    #seleccionamos el modelo
    kmeans= KMeans(n_clusters=4, random_state=0)
    #entrenamos el modelo
    kmeans.fit(X)
    #traigo las etiquetas
    etiquetas= kmeans.labels_
    #Agregamos las etiquetas al dataset
    df['etiquetas']= etiquetas
    # Reemplazamos los valores de las etiquetas por 'leve', 'medio' y 'alto'
    df['etiquetas'].replace({2: 'leve', 3: 'medio', 1: 'alto'}, inplace=True)
    df=df.reset_index()
    df=df.head(3)
    # Reemplazamos los valores de las etiquetas específicos dentro del DataFrame
    df.loc[df['etiquetas'] == 'leve', 'etiquetas'] = 'leve'
    df.loc[df['etiquetas'] == 'medio', 'etiquetas'] = 'medio'
    df.loc[df['etiquetas'] == 'alto', 'etiquetas'] = 'alto'
    return df

async def send_telegram_notification(record):
    # Configurar el token del bot de Telegram
    telegram_token = '6086740780:AAHcLxljbhtvMfkO_Srad1-EQdVmViigzN4' 
    mapbox_token = 'pk.eyJ1IjoidmFuc2lrIiwiYSI6ImNsaG9tbmJiODBhMmQzZmxwdnd3eTVtdHYifQ.RnG-yRvarNlfb3WxneET_Q'
    map_style = 'vansik/clhp2wbfu01da01peackketh1'


    # Crear una instancia del bot de Telegram
    bot = Bot(token=telegram_token)

    etiqueta = record['etiquetas']
    if etiqueta == 0:
        return
    if etiqueta == 'leve':
        mensaje = "¡Sismo leve! 🚨\nRevisar las conexiones de luz, gas y agua. 💡🔥💧"
    elif etiqueta == 'alto':
        mensaje = "¡Sismo fuerte! 🔥🚨\nSi es posible, evacuar. De lo contrario, buscar resguardo en un sitio seguro. 🏃‍♂️🏃‍♀️🚪"
    elif etiqueta == 'medio':
        mensaje = "¡Sismo medio! 🌎🚨\nResguardate bajo una mesa o la cama. 🛌👍"
    else: 
        pass
        
    # Extraer detalles del terremoto
    country = record['country']
    magnitude = record['mag']
    latitude = record['latitude']
    longitude = record['longitude']
    depthh = record['depth']
    etiquetass = record['etiquetas']

    if country == 'usa':
        emoji_country = "🇺🇸"
    elif country == 'chile':
        emoji_country = "🇨🇱"
    elif country == 'japon':
        emoji_country = "🇯🇵"
    else:
        emoji_country = ""
    
    # Otros detalles del terremoto según la estructura del DataFrame
    #map_url = f'https://api.mapbox.com/styles/v1/{map_style}/static/pin-s+ff0000({longitude},{latitude})/{longitude},{latitude},5/600x400?access_token={mapbox_token}'
    map_url2 = f'https://sismic-alert.streamlit.app/?val={country}&val={latitude}&val={longitude}&val={depthh}&val={magnitude}&val={etiquetass}'
    # Crear la palabra clave enlazada a la URL completa
    url_keyword = f'<a href="{map_url2}">Ver mapa y otros detalles</a>'
    # Crear el mensaje
    message_text = f"¡Se ha detectado un sismo en {country} {emoji_country}!\n" \
                   f"Nivel: {mensaje} \n" \
                   f"{url_keyword} \n"

    # Enviar el mensaje al grupo de Telegram
    await bot.send_message(chat_id='-904835114', text=message_text, parse_mode="html")

    print('Notificación de Telegram enviada')    


def main(request):
    #importamos la informacion a traves de la API
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&orderby=time"
    df_usa= pd.read_csv(url)
    pd.set_option('display.max_columns', None)

    # Obtener datos de la API
    url = "https://www.jma.go.jp/bosai/quake/data/list.json"
    response = requests.get(url)
    data = response.json()
    df_japon = pd.DataFrame(data)

    #traemos la informacion a traves de la API
    url = "https://api.xor.cl/sismo/recent"
    response = requests.get(url)
    data = response.json()
    df_chile = pd.DataFrame(data)   


    # Transformar datos
    df_usa= transformacion_usa(df_usa)
    df_japon= transformacion_japon(df_japon)
    df_chile= transformacion_chile(df_chile)
    
    # Concatenar los DataFrames
    combined_df = pd.concat([df_japon, df_chile,df_usa], ignore_index=True)

    # Aplico el modelo de Machine Learning
    combined_df=etiquetado(combined_df)

    # Conexión a MongoDB Atlas
    collection = connect_to_mongodb()

    # Validar y filtrar terremotos con la misma fecha
    for record in combined_df.to_dict('records'):
        date = record['time']
        existing_record = collection.find_one({'time': date})
        if existing_record is None:
            # Insertar el registro en la colección de MongoDB
            collection.insert_one(record)

            # Enviar mensaje de telegram
            asyncio.run(send_telegram_notification(record))

    return "ETL process completed successfully"