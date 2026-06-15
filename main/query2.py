import pandas as pd
import plotly.express as px
import streamlit as st

@st.cache_data(show_spinner=False)
def _load_q2_data(_db, _pg_conn):
    query = "SELECT product_id, product_category_name FROM olist_products_dataset"
    try:
        df_prod = pd.read_sql_query(query, _pg_conn)
    except Exception:
        df_prod = pd.DataFrame()
        
    orders = list(_db['olist_merged_orders_dataset'].find(
        {}, {"order_purchase_timestamp": 1, "order_items.product_id": 1, "_id": 0}
    ))
    
    records = []
    for doc in orders:
        dt = doc.get('order_purchase_timestamp')
        items = doc.get('order_items', [])
        if isinstance(items, list):
            for item in items:
                records.append({
                    'date': dt,
                    'product_id': item.get('product_id')
                })
                
    df_orders = pd.DataFrame(records)
    if df_orders.empty or df_prod.empty:
        return pd.DataFrame()
        
    df_orders['date'] = pd.to_datetime(df_orders['date'], errors='coerce')
    df_orders = df_orders.dropna(subset=['date'])
    df_orders['year'] = df_orders['date'].dt.year
    df_orders['quarter'] = df_orders['date'].dt.quarter
    df_orders['month'] = df_orders['date'].dt.month
    
    df = pd.merge(df_orders, df_prod, on='product_id', how='inner')
    return df

class Query2:
    def __init__(self, mongo_client, pg_conn):
        self.df = _load_q2_data(mongo_client['olist'], pg_conn)

    def get_top_categories(self, year, period_type, period_val):
        if self.df.empty: return pd.DataFrame()
        df_filtered = self.df.copy()
        
        if year != 'All':
            df_filtered = df_filtered[df_filtered['year'] == int(year)]
            
        if period_type == 'Kuartal' and period_val != 'All':
            df_filtered = df_filtered[df_filtered['quarter'] == int(period_val)]
        elif period_type == 'Bulan' and period_val != 'All':
            df_filtered = df_filtered[df_filtered['month'] == int(period_val)]
            
        agg_df = df_filtered.groupby('product_category_name').size().reset_index(name='total_penjualan')
        agg_df = agg_df.sort_values('total_penjualan', ascending=False).head(5)
        return agg_df

    def plot_top_categories(self, agg_df):
        if agg_df.empty:
            return px.bar(title="Tidak ada data")
        fig = px.bar(
            agg_df, 
            x='total_penjualan', 
            y='product_category_name', 
            orientation='h',
            title='Top 5 Kategori Produk pada Periode Terpilih', 
            color='total_penjualan',
            color_continuous_scale='Blues'
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, template='plotly_white')
        return fig
        
    def get_category_trend(self, category, time_type):
        if self.df.empty: return pd.DataFrame()
        df_cat = self.df[self.df['product_category_name'] == category]
        
        if time_type == 'Tahunan':
            agg = df_cat.groupby('year').size().reset_index(name='sales')
            agg['period'] = agg['year'].astype(int).astype(str)
        elif time_type == 'Kuartal':
            agg = df_cat.groupby(['year', 'quarter']).size().reset_index(name='sales')
            agg['period'] = agg['year'].astype(int).astype(str) + '-Q' + agg['quarter'].astype(int).astype(str)
        elif time_type == 'Bulanan':
            agg = df_cat.groupby(['year', 'month']).size().reset_index(name='sales')
            agg['period'] = agg['year'].astype(int).astype(str) + '-' + agg['month'].astype(int).astype(str).str.zfill(2)
        else:
            agg = pd.DataFrame()
        return agg

    def plot_trend(self, agg_df, category):
        if agg_df.empty:
            return px.line(title="Tidak ada data")
        fig = px.line(
            agg_df, 
            x='period', 
            y='sales', 
            markers=True, 
            title=f'Tren Penjualan untuk Kategori: {category}'
        )
        fig.update_layout(template='plotly_white', xaxis_title="Periode", yaxis_title="Total Penjualan")
        return fig
