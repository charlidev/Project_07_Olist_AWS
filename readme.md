# 🛒 Serverless Data Lakehouse en AWS (Arquitectura Medallón)

## Descripción del Proyecto
Este proyecto implementa una arquitectura de datos moderna y 100% *serverless* en Amazon Web Services (AWS) utilizando el dataset público de E-commerce de Olist. El objetivo principal es construir un flujo automatizado (Pipeline) que ingeste datos crudos, los limpie, los transforme a formato columnar y construya un modelo dimensional (Esquema de Estrella) listo para la toma de decisiones en herramientas de Business Intelligence (BI).

## Arquitectura y Tecnologías
El proyecto sigue las mejores prácticas de la **Arquitectura Medallón** (Bronze, Silver, Gold), orquestando microservicios nativos de la nube para garantizar escalabilidad y bajo costo.

*   **Almacenamiento (Data Lake):** Amazon S3
*   **Cómputo / ETL:** AWS Lambda (Python 3.12, Pandas, AWS Data Wrangler / Boto3)
*   **Orquestación:** AWS Step Functions
*   **Metadatos y Catálogo:** AWS Glue (Crawlers & Data Catalog)
*   **Consulta (Data Warehouse virtual):** Amazon Athena (Serverless SQL)
*   **Visualización:** Power BI

## Flujo de Datos (Data Pipeline)

1.  **Capa Bronze (Raw):** 
    *   Una función Lambda lee los archivos CSV desde una zona de *Staging*.
    *   Transfiere los datos a la capa Bronze particionándolos por fecha de ingesta (`year=YYYY/month=MM/day=DD`) para habilitar cargas incrementales.
2.  **Capa Silver (Cleansed):** 
    *   Lectura de los datos crudos utilizando Pandas mediante *AWS Data Wrangler*.
    *   Limpieza de cadenas de texto (TRIM) y estandarización de valores nulos (N/A).
    *   Conversión de archivos CSV a formato **Parquet** para optimizar el almacenamiento y los costos de escaneo.
3.  **Capa Gold (Curated):** 
    *   Transformación y modelado dimensional.
    *   Creación de un Esquema de Estrella puro: separando el contexto en tablas de dimensiones (`dim_customers`, `dim_products`, `dim_time`) y las métricas en una tabla de hechos (`fact_orders`).
4.  **Explotación:** 
    *   AWS Glue Crawlers infieren el esquema automatizadamente y construyen el catálogo de datos.
    *   Amazon Athena consulta los archivos Parquet mediante SQL estándar.

## Retos Técnicos y Soluciones

Durante el desarrollo de esta arquitectura, se resolvieron diversos desafíos propios del cómputo distribuido y la gestión de Data Lakes:

*   **Cuellos de botella de CPU y Memoria (Timeouts):** 
    El procesamiento en memoria de Pandas dentro de AWS Lambda provocaba errores de *Timeout* con los recursos por defecto. Esto se solucionó escalando la memoria de la función a 2048 MB, lo cual desbloqueó proporcionalmente mayor poder de vCPU, reduciendo el tiempo de procesamiento de varios minutos a escasos segundos.
*   **Corrupción del Catálogo por Particiones Huérfanas:** 
    En los Data Lakes, "la carpeta es la tabla". Guardar múltiples entidades directamente dentro de una misma partición de fecha causó que el Crawler de AWS Glue aislara los esquemas creando tablas duplicadas con sufijos alfanuméricos. Esto se corrigió rediseñando la jerarquía de S3 bajo el estándar estricto de: `Capa -> Tabla -> Partición -> Archivo` (ej. `gold/fact_orders/year=2026/month=10/day=10/data.parquet`), logrando un catálogo limpio.
*   **Sincronización de Metadatos en Athena:** 
    Se implementó el comando `MSCK REPAIR TABLE` para forzar a Amazon Athena a reconocer e indexar las nuevas carpetas de partición generadas por el pipeline, permitiendo la lectura exitosa de los registros.

##  Estructura del Repositorio
*   `/src/`: Contiene los scripts de Python ejecutados en las AWS Lambdas.
*   `/orchestration/`: Contiene la definición en JSON (Amazon States Language) de la máquina de estado de Step Functions.
*   `/docs/`: Diagramas de arquitectura y evidencia visual de la ejecución del pipeline y las consultas en Athena.