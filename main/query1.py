import pandas as pd
import plotly.graph_objects as go
import streamlit as st

@st.cache_data(show_spinner=False)
def _load_q1_data(_db):
    orders = list(_db['olist_merged_orders_dataset'].find(
        {"order_purchase_timestamp": {"$gte": "2017-01-01", "$lt": "2018-07-01"}},
        {"order_id": 1, "order_purchase_timestamp": 1, "_id": 0}
    ))
    payments = list(_db['olist_order_payments_dataset'].find(
        {}, {"order_id": 1, "payment_value": 1, "_id": 0}
    ))
    
    df_orders = pd.DataFrame(orders)
    df_payments = pd.DataFrame(payments)
    
    if df_orders.empty or df_payments.empty:
        return pd.DataFrame()
        
    df_orders['order_purchase_timestamp'] = pd.to_datetime(df_orders['order_purchase_timestamp'], errors='coerce')
    df_orders = df_orders.dropna(subset=['order_purchase_timestamp'])
    df_orders['year'] = df_orders['order_purchase_timestamp'].dt.year
    df_orders['quarter'] = df_orders['order_purchase_timestamp'].dt.quarter
    
    df = pd.merge(df_orders, df_payments, on='order_id', how='left')
    return df

class Query1:
    def __init__(self, mongo_client):
        self.df = _load_q1_data(mongo_client['olist'])

    def get_aggregated_data(self, selected_year, selected_quarter):
        if self.df.empty: return pd.DataFrame()
        df_filtered = self.df.copy()
        if selected_year != 'All':
            df_filtered = df_filtered[df_filtered['year'] == int(selected_year)]
        if selected_quarter != 'All':
            df_filtered = df_filtered[df_filtered['quarter'] == int(selected_quarter)]
            
        agg_df = df_filtered.groupby(['year', 'quarter']).agg(
            total_orders=('order_id', 'nunique'),
            total_revenue=('payment_value', 'sum')
        ).reset_index()
        agg_df['period'] = agg_df['year'].astype(int).astype(str) + '-Q' + agg_df['quarter'].astype(int).astype(str)
        agg_df = agg_df.sort_values(['year', 'quarter'])
        return agg_df

    def plot(self, agg_df):
        fig = go.Figure()
        if agg_df.empty: return fig
        fig.add_trace(go.Bar(
            x=agg_df['period'],
            y=agg_df['total_orders'],
            name='Total Volume Pemesanan',
            yaxis='y',
            marker_color='royalblue'
        ))
        fig.add_trace(go.Scatter(
            x=agg_df['period'],
            y=agg_df['total_revenue'],
            name='Total Pendapatan (Revenue)',
            mode='lines+markers',
            yaxis='y2',
            line=dict(color='firebrick', width=3)
        ))
        fig.update_layout(
            title='Fluktuasi Volume Pemesanan dan Pendapatan (2017 - Mid 2018)',
            xaxis=dict(title='Periode (Tahun-Kuartal)'),
            yaxis=dict(title='Total Volume Pemesanan', side='left'),
            yaxis2=dict(title='Total Pendapatan', side='right', overlaying='y', showgrid=False),
            legend=dict(x=0.01, y=1.1, orientation='h'),
            template='plotly_white'
        )
        return fig
