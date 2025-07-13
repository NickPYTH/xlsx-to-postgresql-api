from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
from io import BytesIO
from sqlalchemy import create_engine, text
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def map_dtypes_to_postgres(df):
    """Определение типов данных для PostgreSQL на основе DataFrame"""
    type_mapping = {
        'int64': 'BIGINT',
        'float64': 'DOUBLE PRECISION',
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'TIMESTAMP',
        'object': 'TEXT'
    }
    
    column_types = {}
    for column, dtype in df.dtypes.items():
        pg_type = type_mapping.get(str(dtype), 'TEXT')
        
        if str(dtype) == 'object':
            try:
                pd.to_datetime(df[column])
                pg_type = 'TIMESTAMP'
            except (ValueError, TypeError):
                max_len = df[column].astype(str).str.len().max()
                if not pd.isna(max_len) and max_len < 255:
                    pg_type = f'VARCHAR({int(max_len * 1.5)})'
        
        column_types[column] = pg_type
    
    return column_types

def create_postgres_table(engine, table_name, column_types, if_exists='replace'):
    """Создание таблицы в PostgreSQL с правильным использованием SQLAlchemy"""
    with engine.begin() as conn:  # Используем begin() для управления транзакцией
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))  # Используем text()
        
        columns_sql = []
        for column, pg_type in column_types.items():
            # Экранируем имена столбцов
            safe_column = f'"{column}"' if not column.isidentifier() else column
            columns_sql.append(f"{safe_column} {pg_type}")
        
        create_sql = f"CREATE TABLE {table_name} (\n    " + ",\n    ".join(columns_sql) + "\n)"
        
        # Выполняем с использованием text()
        conn.execute(text(create_sql))

@api_view(['POST'])
def upload_xlsx_to_postgres(request):
    """
    Обработка POST-запроса с XLSX-файлом для загрузки в PostgreSQL
    """
    try:
        # Получение параметров из запроса
        table_name = request.data.get('table_name')
        sheet_name = request.data.get('sheet_name', 0)
        if_exists = request.data.get('if_exists', 'replace')
        
        if not table_name:
            return Response(
                {"error": "Parameter 'table_name' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file uploaded"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Чтение файла
        xlsx_file = request.FILES['file']
        file_data = BytesIO(xlsx_file.read())
        
        try:
            df = pd.read_excel(file_data, sheet_name=sheet_name)
            df = df.where(pd.notnull(df), None)
        except Exception as e:
            logger.error(f"Error reading XLSX file: {str(e)}")
            return Response(
                {"error": f"Invalid XLSX file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Получение конфигурации БД
        db_config = settings.DATABASES['default']
        
        # Создание подключения
        engine = create_engine(
            f"postgresql://{db_config['USER']}:{db_config['PASSWORD']}@"
            f"{db_config['HOST']}:{db_config['PORT']}/{db_config['NAME']}"
        )
        
        # Определение типов колонок
        column_types = map_dtypes_to_postgres(df)
        
        # Создание таблицы
        try:
            create_postgres_table(engine, table_name, column_types, if_exists)
        except Exception as e:
            logger.error(f"Error creating table: {str(e)}")
            return Response(
                {"error": f"Failed to create table: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Загрузка данных
        try:
            df.to_sql(
                table_name,
                engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=10000
            )
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return Response(
                {"error": f"Failed to load data: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response(
            {
                "status": "success",
                "table": table_name,
                "rows_imported": len(df),
                "columns": list(df.columns)
            },
            status=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return Response(
            {"error": f"Internal server error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )