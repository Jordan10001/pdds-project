Keterangan Library
1. Pakai Stremlit
2. Plotly untuk visualisasi
3. Pandas

Keterangan cara kerja
1. Menggunakan gabungan query
2. Hasil analisis harus bisa dynamic 
contoh dari rumusan ke 1 itu kita bisa pilih quertal dan tahun jadi ada dua dropdown
contoh dari rumusan ke 2 itu kita bisa pilih catrgory product dan nantik terlihat kita bisa pilih pertahun perbulan atau per quartal



Rumusan Masalah
1. [SQL - Trend Musiman] "Bagaimana fluktuasi total volume pemesanan dan total pendapatan (revenue) platform jika diagregasi berdasarkan kuartal (Q1-Q4) selama periode tahun 2017 hingga pertengahan 2018?"
2. [SQL - Penggerak Lonjakan Musiman / Produk] "Pada kuartal dengan lonjakan transaksi tertinggi (peak season), kategori produk apa yang mengalami peningkatan persentase penjualan paling signifikan dibandingkan kuartal lainnya?"
3. [SQL - Inter Vs Intra, Jarak Spasial]"Bagaimana pengaruh perbedaan wilayah geografis (intra-state vs inter-state) antara lokasi penjual dan pembeli terhadap biaya logistik (freight value) dan efisiensi waktu pengiriman barang (delivery performance), serta bagaimana pola distribusinya pada transaksi e-commerce Olist?" 

Data yang digunakan: 
    olist_customers_dataset.csv, 
    olist_sellers_dataset.csv, 
    olist_products_dataset.csv, 
    olist_payment_dataset.json,
    olist_merged_orders_dataset.json

Relational Database (PostgreSQL): olist_customers_dataset.csv, olist_sellers_dataset.csv, olist_products_dataset.csv,  
NoSQL Database (MongoDB): olist_payment_dataset.json, olist_merged_orders_dataset.json

2. For each problem/challenge, explain how you intend to solve, and perhaps, to visualize.
Problem 1: Tren Musiman (Fluktuasi Volume dan Pendapatan)
Cara Menyelesaikan (How to Solve): Kami akan melakukan ekstraksi dimensi waktu (Bulan dan Kuartal) dari kolom order_purchase_timestamp pada document olist_merged_orders_dataset.json Selanjutnya, kami melakukan query gabungan dengan document olist_payment_dataset.json atau agregasi price dari Order Items untuk mendapatkan nilai pendapatan (revenue). Data kemudian di-group by berdasarkan Kuartal (Q1-Q4) dan Tahun untuk menghitung COUNT(order_id) dan SUM(payment_value).
Visualisasi: 
    Multi-axis Line Chart (Grafik Garis Ganda). Sumbu X merepresentasikan waktu (Kuartal/Tahun). Sumbu Y sebelah kiri merepresentasikan total volume pesanan (bar), dan sumbu Y sebelah kanan merepresentasikan total pendapatan (garis tren).

Problem 2: Penggerak Lonjakan Musiman (Produk)
Cara Menyelesaikan (How to Solve): Berdasarkan hasil dari Problem 1 (menemukan kuartal peak season), kami akan memfilter document olist_merged_orders_dataset.json hanya pada kuartal tersebut. Kami melakukan query antara olist_merged_orders_dataset.json, dan olist_products_dataset.csv. Kami akan menghitung COUNT(product_id) yang dikelompokkan (Group By) berdasarkan product_category_name, lalu membandingkan persentase peningkatannya terhadap kuartal sebelumnya menggunakan Window Function (seperti LAG()) di SQL.
Visualisasi: 
    Treemap atau Horizontal Bar Chart. Visualisasi ini akan menyoroti (menggunakan warna mencolok) top 5 kategori produk yang menjadi tulang punggung penjualan pada kuartal tersibuk tersebut.

Problem 3: Inter vs Intra, Jarak Spasial 
Cara Menyelesaikan (How to Solve): Kami akan melakukan query gabungan antara olist_merged_orders_dataset.json (pada array order_items) dengan olist_customers_dataset.csv menggunakan kunci customer_id, serta olist_sellers_dataset.csv menggunakan kunci seller_id 
Visualisasi: 
    Dual-Axis Grouped Bar Chart: Menampilkan perbandingan rata-rata ongkos kirim (freight value) dan rata-rata durasi pengiriman (hari) antara rute Intra-State dan Inter-State. 
    Choropleth Geospatial Map / Flow Map: Peta wilayah Brazil yang memberikan garis alur (flow) transaksi dari kluster seller_state terbanyak menuju customer_state, dengan gradasi warna pada area pembeli untuk menunjukkan wilayah yang menanggung ongkos kirim tertinggi atau mengalami keterlambatan pengiriman terlama. 



Keterangan lain lain
aku sudah siapi kode nya untuk database kamu tinggal panggil aja
kemudian aku mau kamu terapin oop jadi kode nya rapih dan tiap rumusan masalah di straem lit nya di bagi per tab jadi ada 3 tab serta tab ke 4 untuk menunjukan raw data.
dan tiap query buat satu file per rumusan masalah jadi jangan di jadiin satu file.
kemudian di stremlit halamn utama berikan pop up bawah koneksi databasenya terhubung

Keterangan Tambahan
Untuk Mongo nama databasenya olist dan nama colectionya sama seperti nama yang di data olist_payment_dataset.json, olist_merged_orders_dataset.json
Untuk Postgre nama kolom nya sama perisi seperti ini     olist_customers_dataset.csv, olist_sellers_dataset.csv, olist_products_dataset.csv

Hanya dari mongo dan postgre namanya tidak termasuk extension file nya jadi tanpa .json dan .csv. tetapi semua data sudah ready kok
