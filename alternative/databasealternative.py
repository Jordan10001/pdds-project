# database.py
from pymongo import MongoClient
import certifi 

MONGO_URI = "mongodb+srv://USERNAME:PASSWORD@cluster0.xxxx.mongodb.net/nama_db?retryWrites=true&w=majority"

def get_mongo_connection():
    try:
        # tlsCAFile agar tidak error sertifikat SSL di Windows/Mac
        client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
        
        client.admin.command('ping')
        return client, "MongoDB Atlas Connected ✅"
    except Exception as e:
        return None, f"Mongo Error: {str(e)[:50]}... ❌"