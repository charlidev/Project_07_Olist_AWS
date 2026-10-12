import boto3
import datetime

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = 'olist-datalake-carlos-dev-2026'
    prefix_origen = 'dev/staging/'
    prefix_destino_base = 'dev/bronze/'
    
    # Generar partición basada en la fecha actual
    hoy = datetime.datetime.now()
    particion = f"year={hoy.year}/month={hoy.month:02d}/day={hoy.day:02d}/"
    
    archivos_procesados = 0
    
    try:
        # Listar archivos en la ruta de staging
        respuesta = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix_origen)
        
        if 'Contents' not in respuesta:
            return {'statusCode': 200, 'body': 'No se encontraron archivos en staging.'}
            
        for obj in respuesta['Contents']:
            origen_key = obj['Key']
            
            # Omitir la carpeta raíz si S3 la devuelve como un objeto
            if origen_key == prefix_origen:
                continue
                
            # Extraer el nombre del archivo
            nombre_archivo = origen_key.split('/')[-1]
            destino_key = f"{prefix_destino_base}{particion}{nombre_archivo}"
            
            # Copiar el archivo de staging a bronze
            s3_client.copy_object(
                CopySource={'Bucket': bucket_name, 'Key': origen_key},
                Bucket=bucket_name,
                Key=destino_key
            )
            archivos_procesados += 1
            print(f"Copiado exitosamente: {origen_key} -> {destino_key}")
            
        return {
            'statusCode': 200,
            'body': f"Éxito: {archivos_procesados} archivos transferidos a Bronze."
        }
        
    except Exception as e:
        print(f"Error detectado: {str(e)}")
        return {'statusCode': 500, 'body': f"Fallo en la ejecución: {str(e)}"}