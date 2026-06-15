import streamlit as st
import pandas as pd
from database import get_postgre_connection, get_mongo_connection
from main.queries import fetch_postgre_data, fetch_mongo_data
from main.query1 import Query1
from main.query2 import Query2
from main.query3 import Query3

class DashboardApp:
    def __init__(self):
        st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")
        self._init_connections()
        self._load_models()

    def _init_connections(self):
        self.pg_conn, pg_msg = get_postgre_connection()
        self.mg_client, mg_msg = get_mongo_connection()
        
        # Bottom pop-up connection
        if self.pg_conn and self.mg_client:
            st.toast("Koneksi Database (PostgreSQL & MongoDB) Berhasil! ✅", icon="🚀")
        else:
            if not self.pg_conn: st.toast(pg_msg, icon="❌")
            if not self.mg_client: st.toast(mg_msg, icon="❌")

    def _load_models(self):
        with st.spinner("Memuat Data..."):
            if self.mg_client:
                self.q1 = Query1(self.mg_client)
            else:
                self.q1 = None
                
            if self.mg_client and self.pg_conn:
                self.q2 = Query2(self.mg_client, self.pg_conn)
                self.q3 = Query3(self.mg_client, self.pg_conn)
            else:
                self.q2 = None
                self.q3 = None

    def run(self):
        st.title("📊 Multi-Database E-Commerce Dashboard")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Tren Musiman (Q1-Q4)", 
            "Penggerak Lonjakan Musiman", 
            "Jarak Spasial (Inter vs Intra)", 
            "Data Mentah (Raw Data)"
        ])
        
        with tab1:
            self._render_tab1()
            
        with tab2:
            self._render_tab2()
            
        with tab3:
            self._render_tab3()
            
        with tab4:
            self._render_tab4()

    def _render_tab1(self):
        st.header("Fluktuasi Volume Pemesanan dan Pendapatan (2017 - Mid 2018)")
        if not self.q1 or self.q1.df.empty:
            st.warning("Data tidak tersedia atau koneksi database gagal.")
            return
            
        years = ['All'] + sorted(self.q1.df['year'].dropna().unique().astype(int).tolist())
        quarters = ['All', 1, 2, 3, 4]
        
        col1, col2 = st.columns(2)
        with col1:
            sel_year = st.selectbox("Pilih Tahun:", years, key="t1_year")
        with col2:
            sel_quarter = st.selectbox("Pilih Kuartal:", quarters, key="t1_quarter")
            
        agg_data = self.q1.get_aggregated_data(sel_year, sel_quarter)
        fig = self.q1.plot(agg_data)
        st.plotly_chart(fig, use_container_width=True)

    def _render_tab2(self):
        st.header("Penggerak Lonjakan Musiman / Produk")
        if not self.q2 or self.q2.df.empty:
            st.warning("Data tidak tersedia atau koneksi database gagal.")
            return
            
        st.subheader("Top 5 Kategori Produk")
        years = ['All'] + sorted(self.q2.df['year'].dropna().unique().astype(int).tolist())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            sel_year = st.selectbox("Pilih Tahun:", years, key="t2_year")
        with col2:
            period_type = st.selectbox("Tipe Periode:", ['Kuartal', 'Bulan'], key="t2_period_type")
        with col3:
            if period_type == 'Kuartal':
                vals = ['All', 1, 2, 3, 4]
            else:
                vals = ['All'] + list(range(1, 13))
            sel_period = st.selectbox(f"Pilih {period_type}:", vals, key="t2_period")
            
        top_cats = self.q2.get_top_categories(sel_year, period_type, sel_period)
        fig_bar = self.q2.plot_top_categories(top_cats)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.subheader("Tren Kategori Spesifik")
        categories = sorted(self.q2.df['product_category_name'].dropna().unique().tolist())
        col_cat, col_time = st.columns(2)
        with col_cat:
            sel_cat = st.selectbox("Pilih Kategori Produk:", categories, key="t2_cat")
        with col_time:
            time_type = st.selectbox("Tipe Agregasi:", ['Bulanan', 'Kuartal', 'Tahunan'], key="t2_time")
            
        trend_df = self.q2.get_category_trend(sel_cat, time_type)
        fig_trend = self.q2.plot_trend(trend_df, sel_cat)
        st.plotly_chart(fig_trend, use_container_width=True)

    def _render_tab3(self):
        st.header("Inter vs Intra-State: Dampak Geografis")
        if not self.q3 or self.q3.df.empty:
            st.warning("Data tidak tersedia atau koneksi database gagal.")
            return
            
        agg_df = self.q3.get_aggregated_data()
        fig_comp = self.q3.plot_comparison(agg_df)
        st.plotly_chart(fig_comp, use_container_width=True)
        
        st.subheader("Distribusi Rata-Rata Metrik per State Pembeli")
        metric = st.radio("Pilih Metrik untuk Peta:", ['Ongkos Kirim', 'Waktu Pengiriman'])
        state_df = self.q3.get_state_flow_data()
        fig_map = self.q3.plot_map(state_df, metric)
        st.plotly_chart(fig_map, use_container_width=True)

    def _render_tab4(self):
        st.header("Raw Data Explorer")
        st.write("Menggunakan fetcher dasar PostgreSQL dan MongoDB.")
        
        db_choice = st.selectbox("Pilih Sumber Data:", ["PostgreSQL (Customers)", "PostgreSQL (Sellers)", "PostgreSQL (Products)", "MongoDB (Orders)", "MongoDB (Payments)"])
        
        if db_choice == "PostgreSQL (Customers)":
            df = fetch_postgre_data(self.pg_conn, "SELECT * FROM olist_customers_dataset LIMIT 50")
            if df is not None: st.dataframe(df)
        elif db_choice == "PostgreSQL (Sellers)":
            df = fetch_postgre_data(self.pg_conn, "SELECT * FROM olist_sellers_dataset LIMIT 50")
            if df is not None: st.dataframe(df)
        elif db_choice == "PostgreSQL (Products)":
            df = fetch_postgre_data(self.pg_conn, "SELECT * FROM olist_products_dataset LIMIT 50")
            if df is not None: st.dataframe(df)
        elif db_choice == "MongoDB (Orders)":
            df = fetch_mongo_data(self.mg_client, 'olist', 'olist_merged_orders_dataset')
            if df is not None and not df.empty:
                if '_id' in df.columns: df = df.drop(columns=['_id'])
                st.dataframe(df)
        elif db_choice == "MongoDB (Payments)":
            df = fetch_mongo_data(self.mg_client, 'olist', 'olist_order_payments_dataset')
            if df is not None and not df.empty:
                if '_id' in df.columns: df = df.drop(columns=['_id'])
                st.dataframe(df)

if __name__ == "__main__":
    app = DashboardApp()
    app.run()