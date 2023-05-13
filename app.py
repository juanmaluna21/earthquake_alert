import requests
import json
import pandas as pd
from config.db import conn
import time

# Cycle for country: get_last_quake --> check_not_exist --> save_mongo

def get_last_quake():
    countries={'usa':'https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&orderby=time','japan':'https://www.jma.go.jp/bosai/quake/data/list.json','chile':'https://api.xor.cl/sismo/recent'}
    for country in countries:
        quake=get_quake_by_country(country, countries[country])
        if check_not_exist(quake['time'],quake['country']):
            save_mongo(quake)
            print('1 new quake for "{0}" added'.format(quake['country']))
        else:
            print('0 new quake for "{0}" added'.format(quake['country']))
        
def check_not_exist(time, country): #Verify if quake exists for 'country'
    if conn.sismology.quakes.find_one({'time':time,'country':country})!=None:
        return False 
    else:
        return True
        
def save_mongo(quake): #Save into mongo latest quake    
    #Inserting document
    db=conn['sismology']
    collection=db['quakes']
    collection.insert_one(quake)

#Manage country
def get_quake_by_country(country,url):
  if country=='usa':
    df=pd.read_csv(url)
    df=df[['time','latitude','longitude','depth','mag','place']] #Valid fields
    df=df.head(1) #Top 1 order by time
    df=df.squeeze() #Serializing
    quake={'time':df['time'], 'latitude':df['latitude'], 'longitude':df['longitude'], 'depth':df['depth'], 'mag':df['mag'], 'place':df['place'], 'country':country} #Typing for mongo
  elif country=='japan':
    r=requests.get(url) #Get data from api
    r=r.text #Text of body
    r=json.loads(r) #Convert to json format 
    r=r[0] #Top 1 order by time    
    vars=r['cod'][1:]
    vars=vars.replace('+',',')
    vars=vars.replace('-',',')
    vars=vars.replace('/','')
    vars=vars.split(',')
    lat=vars[0]
    lon=vars[1]
    dept=vars[2] #Converting depth to 'km'
    quake={'time':r['at'], 'latitude':lat, 'longitude':lon, 'depth':dept, 'mag':r['mag'], 'place':r['en_anm'], 'country':country} #Typing for mongo
  elif country=='chile':
    r=requests.get(url) #Get data from api
    r=r.text #Text of body
    r=json.loads(r) #Convert to json format 
    r=r['events'][0] #Top 1 order by time   
    quake={'time':r['local_date'], 'latitude':r['latitude'], 'longitude':r['longitude'], 'depth':r['depth'], 'mag':r['magnitude']['value'], 'place':r['geo_reference'], 'country':country} #Typing for mongo
  return quake

start=time.time()
print(get_last_quake())
stop=time.time()
print('--Elapsed--> ', stop-start)
