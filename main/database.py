import psycopg2
from pymongo import MongoClient
import streamlit as st

POSTGRES_CONFIG = "postgresql://neondb_owner:npg_r6aof1iNIzxl@ep-green-lab-a1r5lkwm-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

MONGO_URI = "mongodb+srv://mongodb:admin@gacorr.wilufag.mongodb.net/?appName=gacorr" 

def get_postgre_connection():
    try:
        conn = psycopg2.connect(POSTGRES_CONFIG)
        return conn, "Koneksi PostgreSQL Berhasil! ✅"
    except Exception as e:
        return None, f"Koneksi PostgreSQL Gagal: {e} ❌"

def get_mongo_connection():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        return client, "Koneksi MongoDB Berhasil! ✅"
    except Exception as e:
        return None, f"Koneksi MongoDB Gagal: {e} ❌"