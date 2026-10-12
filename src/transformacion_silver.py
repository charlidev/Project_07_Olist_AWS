import awswrangler as wr
import pandas as pd
import datetime

def lambda_handler(event, context):
    bucket_name = 'olist-datalake-carlos-dev-2026'
    
    # Generar partición basada en la fecha actual
    hoy = datetime.datetime.now()
    particion = f"year={hoy.year}/month={hoy.month:02d}/day={hoy.day:02d}/"
    
    ruta_bronze = f"s3://{bucket_name}/dev/bronze/{particion}"
    ruta_silver = f"s3://{bucket_name}/dev/silver/{particion}"
    
    archivos_procesados = 0
    
    try:
        # Listar todos los archivos en la ruta de Bronze del día de hoy
        archivos_bronze = wr.s3.list_objects(ruta_bronze)
        
        if not archivos_bronze:
            return {'statusCode': 200, 'body': 'No se encontraron archivos en Bronze para procesar hoy.'}
            
        for archivo in archivos_bronze:
            # 1. Leer el CSV directamente desde S3 a un DataFrame de Pandas
            df = wr.s3.read_csv(archivo)
            
            # 2. Transformaciones Silver (Limpieza básica)
            cols_texto = df.select_dtypes(include=['object']).columns
            
            # Limpiar espacios en blanco al inicio y final (TRIM)
            df[cols_texto] = df[cols_texto].apply(lambda x: x.str.strip())
            
            # Rellenar valores nulos SOLO en las columnas de texto
            df[cols_texto] = df[cols_texto].fillna("N/A")
            
            # Extraer el nombre base
            nombre_base = archivo.split('/')[-1].replace('.csv', '')
            destino_parquet = f"{ruta_silver}{nombre_base}.parquet"
            
            # 3. Guardar el DataFrame como Parquet en S3
            wr.s3.to_parquet(
                df=df,
                path=destino_parquet,
                dataset=False
            )
            
            archivos_procesados += 1
            print(f"Transformado y guardado: {nombre_base}.parquet")
            
        return {
            'statusCode': 200,
            'body': f"Éxito: {archivos_procesados} archivos convertidos a Parquet en Silver."
        }
        
    except Exception as e:
        print(f"Error detectado: {str(e)}")
        return {'statusCode': 500, 'body': f"Fallo en la ejecución: {str(e)}"}