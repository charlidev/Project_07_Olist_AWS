import awswrangler as wr
import pandas as pd
import datetime

def lambda_handler(event, context):
    bucket_name = 'olist-datalake-carlos-dev-2026'
    
    hoy = datetime.datetime.now()
    particion = f"year={hoy.year}/month={hoy.month:02d}/day={hoy.day:02d}/"
    
    ruta_silver = f"s3://{bucket_name}/dev/silver/{particion}"
    ruta_gold_base = f"s3://{bucket_name}/dev/gold/" 
    
    try:
        print("Leyendo archivos desde Silver...")
        df_orders = wr.s3.read_parquet(f"{ruta_silver}olist_orders_dataset.parquet")
        df_items = wr.s3.read_parquet(f"{ruta_silver}olist_order_items_dataset.parquet")
        df_payments = wr.s3.read_parquet(f"{ruta_silver}olist_order_payments_dataset.parquet")
        df_customers = wr.s3.read_parquet(f"{ruta_silver}olist_customers_dataset.parquet")
        df_products = wr.s3.read_parquet(f"{ruta_silver}olist_products_dataset.parquet")
        
        print("Construyendo Dimensiones...")
        
        dim_customers = df_customers[['customer_id', 'customer_unique_id', 'customer_zip_code_prefix', 'customer_city', 'customer_state']].drop_duplicates()
        
        wr.s3.to_parquet(df=dim_customers, path=f"{ruta_gold_base}dim_customers/{particion}data.parquet", dataset=False)
        
        dim_products = df_products[['product_id', 'product_category_name', 'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm']].drop_duplicates()
        wr.s3.to_parquet(df=dim_products, path=f"{ruta_gold_base}dim_products/{particion}data.parquet", dataset=False)
        
        df_orders['order_purchase_timestamp'] = pd.to_datetime(df_orders['order_purchase_timestamp'], errors='coerce')
        dim_time = pd.DataFrame({
            'time_id': df_orders['order_purchase_timestamp'].dt.date.astype(str),
            'date': df_orders['order_purchase_timestamp'].dt.date,
            'year': df_orders['order_purchase_timestamp'].dt.year,
            'month': df_orders['order_purchase_timestamp'].dt.month,
            'day': df_orders['order_purchase_timestamp'].dt.day
        }).dropna().drop_duplicates()
        wr.s3.to_parquet(df=dim_time, path=f"{ruta_gold_base}dim_time/{particion}data.parquet", dataset=False)
        
        print("Construyendo Tabla de Hechos...")
        fact_orders = df_orders[['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp']].copy()
        fact_orders = fact_orders.merge(df_items[['order_id', 'product_id', 'price', 'freight_value']], on='order_id', how='left')
        fact_orders = fact_orders.merge(df_payments[['order_id', 'payment_type', 'payment_value']], on='order_id', how='left')
        fact_orders['time_id'] = fact_orders['order_purchase_timestamp'].dt.date.astype(str)
        fact_orders = fact_orders[['order_id', 'customer_id', 'product_id', 'time_id', 'order_status', 'payment_type', 'price', 'freight_value', 'payment_value']]
        
        wr.s3.to_parquet(df=fact_orders, path=f"{ruta_gold_base}fact_orders/{particion}data.parquet", dataset=False)
        
        return {'statusCode': 200, 'body': "Éxito: Modelo guardado con jerarquía de carpetas correcta."}
        
    except Exception as e:
        return {'statusCode': 500, 'body': f"Fallo: {str(e)}"}