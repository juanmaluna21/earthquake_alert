import os
from pymongo import MongoClient

conn = MongoClient('mongodb+srv://v1c4r10us:{0}@cluster0.cisx8.mongodb.net/?retryWrites=true&w=majority'.format(os.environ['MONGO_CONN']))
