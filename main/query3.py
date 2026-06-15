import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

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

    def get_aggregated_data(self):
        if self.df.empty: return pd.DataFrame()
        agg_df = self.df.groupby('route_type').agg(
            avg_freight=('freight_value', 'mean'),
            avg_delivery_days=('delivery_days', 'mean')
        ).reset_index()
        return agg_df

    def plot_comparison(self, agg_df):
        fig = go.Figure()
        if agg_df.empty: return fig
        
        fig.add_trace(go.Bar(
            x=agg_df['route_type'],
            y=agg_df['avg_freight'],
            name='Rata-rata Ongkos Kirim (BRL)',
            yaxis='y',
            marker_color='indianred'
        ))
        
        fig.add_trace(go.Bar(
            x=agg_df['route_type'],
            y=agg_df['avg_delivery_days'],
            name='Rata-rata Waktu Pengiriman (Hari)',
            yaxis='y2',
            marker_color='lightsalmon'
        ))
        
        fig.update_layout(
            title='Perbandingan Rute Pengiriman: Intra-State vs Inter-State',
            xaxis=dict(title='Jenis Rute'),
            yaxis=dict(title='Ongkos Kirim (BRL)', side='left'),
            yaxis2=dict(title='Waktu Pengiriman (Hari)', side='right', overlaying='y', showgrid=False),
            barmode='group',
            template='plotly_white',
            legend=dict(x=0.01, y=1.1, orientation='h')
        )
        return fig

    def get_state_flow_data(self):
        if self.df.empty: return pd.DataFrame()
        # Summarize by customer_state
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
        
        # We can just show a bar chart of top 10 states if we don't have geojson for Brazil
        # It's safer and easier than trying to load Brazil's geojson in streamlit without external dependency.
        fig = px.bar(
            state_df.sort_values(color_col, ascending=False).head(15),
            x='customer_state',
            y=color_col,
            title=title_text,
            color=color_col,
            color_continuous_scale='Viridis'
        )
        fig.update_layout(template='plotly_white')
        return fig
