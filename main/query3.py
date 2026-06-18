import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
import requests

@st.cache_data(show_spinner=False)
def _load_geojson():
    try:
        url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        return requests.get(url).json()
    except Exception:
        return None

@st.cache_data(show_spinner=False)
def _load_q3_data(_db, _pg_conn):
    orders = list(_db['olist_merged_orders_dataset'].find(
        {"order_delivered_customer_date": {"$exists": True, "$ne": None},
         "order_purchase_timestamp": {"$exists": True, "$ne": None}},
        {"customer_id": 1, "order_purchase_timestamp": 1, "order_delivered_customer_date": 1,
         "order_items.seller_id": 1, "order_items.freight_value": 1, "_id": 0}
    ))
    
    records = []
    for doc in orders:
        cust_id = doc.get('customer_id')
        dt_purch = pd.to_datetime(doc.get('order_purchase_timestamp'), errors='coerce')
        dt_deliv = pd.to_datetime(doc.get('order_delivered_customer_date'), errors='coerce')
        
        if pd.isnull(dt_purch) or pd.isnull(dt_deliv):
            continue
            
        delivery_days = (dt_deliv - dt_purch).days
        
        items = doc.get('order_items', [])
        if isinstance(items, list):
            for item in items:
                records.append({
                    'customer_id': cust_id,
                    'seller_id': item.get('seller_id'),
                    'freight_value': item.get('freight_value', 0),
                    'delivery_days': delivery_days
                })
                
    df_orders = pd.DataFrame(records)
    
    try:
        cust = pd.read_sql_query("SELECT customer_id, customer_state FROM olist_customers_dataset", _pg_conn)
        sell = pd.read_sql_query("SELECT seller_id, seller_state FROM olist_sellers_dataset", _pg_conn)
    except Exception:
        cust = pd.DataFrame()
        sell = pd.DataFrame()
        
    if df_orders.empty or cust.empty or sell.empty:
        return pd.DataFrame()
        
    df = pd.merge(df_orders, cust, on='customer_id', how='inner')
    df = pd.merge(df, sell, on='seller_id', how='inner')
    
    df['route_type'] = df.apply(lambda row: 'Intra-State' if row['customer_state'] == row['seller_state'] else 'Inter-State', axis=1)
    return df

class Query3:
    def __init__(self, mongo_client, pg_conn):
        self.df = _load_q3_data(mongo_client['olist'], pg_conn)
        self.geojson = _load_geojson()

    def get_aggregated_data(self):
        if self.df.empty: return pd.DataFrame()
        agg_df = self.df.groupby('route_type').agg(
            avg_freight=('freight_value', 'mean'),
            avg_delivery_days=('delivery_days', 'mean')
        ).reset_index()
        return agg_df

    def plot_comparison(self, agg_df):
        if self.df.empty: return go.Figure()
        
        # We will use subplots to show:
        # 1. Rata-rata comparison (Bar chart)
        # 2. Distribusi Freight (Box Plot)
        # 3. Distribusi Delivery (Box Plot)
        # 4. Proporsi Transaksi (Pie Chart)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Rata-rata Metrik (Ongkos Kirim & Hari)", 
                "Proporsi Transaksi: Intra vs Inter",
                "Distribusi Ongkos Kirim (BRL)",
                "Distribusi Waktu Pengiriman (Hari)"
            ),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "box"}, {"type": "box"}]]
        )
        
        # 1. Rata-rata Metrik
        if not agg_df.empty:
            fig.add_trace(go.Bar(
                x=agg_df['route_type'], y=agg_df['avg_freight'],
                name='Rata-rata Ongkos Kirim', marker_color='#636EFA',
                offsetgroup=0
            ), row=1, col=1)
            
            fig.add_trace(go.Bar(
                x=agg_df['route_type'], y=agg_df['avg_delivery_days'],
                name='Rata-rata Waktu (Hari)', marker_color='#EF553B',
                offsetgroup=1
            ), row=1, col=1)
            
        # 2. Pie Chart Proporsi
        route_counts = self.df['route_type'].value_counts()
        fig.add_trace(go.Pie(
            labels=route_counts.index, values=route_counts.values,
            marker=dict(colors=['#636EFA', '#EF553B'])
        ), row=1, col=2)
        
        # 3. Boxplot Freight (Using a sample if data is large, but plotly can handle it. Let's limit outliers view)
        fig.add_trace(go.Box(
            x=self.df['route_type'], y=self.df['freight_value'],
            name='Ongkos Kirim', marker_color='#636EFA', showlegend=False
        ), row=2, col=1)
        
        # 4. Boxplot Delivery
        fig.add_trace(go.Box(
            x=self.df['route_type'], y=self.df['delivery_days'],
            name='Waktu Pengiriman', marker_color='#EF553B', showlegend=False
        ), row=2, col=2)
        
        # Layout modifications
        fig.update_layout(
            title='Analisis Dampak Jarak Geografis dan Pola Distribusi Transaksi',
            height=800,
            template='plotly_white',
            barmode='group',
            showlegend=True,
            # Let Plotly use the default legend position (on the right) to avoid overlapping
            margin=dict(t=80, b=50, l=50, r=50)
        )
        
        # Set y-axis ranges for box plots to filter extreme outliers and show distribution better
        p95_freight = self.df['freight_value'].quantile(0.95)
        p95_days = self.df['delivery_days'].quantile(0.95)
        if p95_freight > 0: fig.update_yaxes(range=[0, p95_freight * 1.5], row=2, col=1)
        if p95_days > 0: fig.update_yaxes(range=[0, p95_days * 1.5], row=2, col=2)
        
        return fig

    def get_state_flow_data(self):
        if self.df.empty: return pd.DataFrame()
        state_df = self.df.groupby('customer_state').agg(
            avg_freight=('freight_value', 'mean'),
            avg_delivery_days=('delivery_days', 'mean'),
            total_orders=('customer_id', 'count')
        ).reset_index()
        return state_df

    def plot_map(self, state_df, metric):
        if state_df.empty:
            return px.choropleth(title="Tidak ada data")
            
        color_col = 'avg_freight' if metric == 'Ongkos Kirim' else 'avg_delivery_days'
        title_text = f"Peta Rata-rata {metric} berdasarkan Negara Bagian Pembeli (Brazil)"
        
        if self.geojson is not None:
            # We have the geojson, let's plot a real map
            fig = px.choropleth(
                state_df,
                geojson=self.geojson,
                locations='customer_state',
                featureidkey='properties.sigla',
                color=color_col,
                color_continuous_scale='Viridis',
                scope='south america',
                title=title_text,
                hover_data=['total_orders']
            )
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(template='plotly_white', height=600)
            return fig
        else:
            # Fallback to bar chart if geojson failed to load
            fig = px.bar(
                state_df.sort_values(color_col, ascending=False).head(15),
                x='customer_state',
                y=color_col,
                title=title_text + " (Data Peta Gagal Dimuat)",
                color=color_col,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(template='plotly_white')
            return fig
