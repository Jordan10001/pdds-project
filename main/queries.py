import pandas as pd

def fetch_postgre_data(conn, query):
    if conn:
        return pd.read_sql_query(query, conn)
    return None

def fetch_mongo_data(client, db_name, collection_name, limit=10):
    if client:
        db = client[db_name]
        collection = db[collection_name]
        data = list(collection.find().limit(limit))
        return pd.DataFrame(data)
    return None