import psycopg2
from pymongo import MongoClient
import streamlit as st

POSTGRES_CONFIG = "YOUR-POSTGRESQL-DATABASE"

MONGO_URI = "YOUR-MONGODB-DATABASE" 

def get_postgre_connection():
    try:
        conn = psycopg2.connect(POSTGRES_CONFIG)
        return conn, "Koneksi PostgreSQL Berhasil! "
    except Exception as e:
        return None, f"Koneksi PostgreSQL Gagal: {e} "

def get_mongo_connection():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        return client, "Koneksi MongoDB Berhasil! "
    except Exception as e:
        return None, f"Koneksi MongoDB Gagal: {e} "
