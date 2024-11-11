from wyge.tools.base_tool import Tool, add_function
from sqlalchemy import create_engine, text
from pydantic import BaseModel, Field
from typing import List
import pandas as pd

def create_mysql_engine(user, password, host, db_name):
    if db_name:
        connection_str = f'postgresql://{user}:{password}@{host}/{db_name}'
    else:
        connection_str = f'postgresql://{user}:{password}@{host}/'
    engine = create_engine(connection_str)
    # engine = engine = create_engine(
    #     connection_str,
    #     pool_size=5,  # Adjust based on your needs
    #     max_overflow=10,  # Allow extra connections beyond pool_size
    #     pool_timeout=30,  # Wait for 30 seconds for a connection to be available
    # )
    return engine

# Function to read an Excel file and store it into a SQL table
def excel_to_sql(excel_file_path, table_name, user, password, host, db_name):
    engine = create_mysql_engine(user, password, host, db_name)
    if not table_name:
        table_name = excel_file_path.split('.')[0]
    df = pd.read_excel(excel_file_path)
    df.to_sql(table_name, con=engine, if_exists='replace', index=False)
    return (f"Data from '{excel_file_path}' stored in table '{table_name}'.")

# Function to execute a custom SQL query and print results
def execute_query(query, user, password, host, db_name):
    engine = create_mysql_engine(user, password, host, db_name)
    with engine.connect() as connection:
        try:
            result_set = connection.execute(text(query))
            output = []
            for row in result_set:
                print(row)
                output.append(str(row))#(tuple(row))
            return output
        except Exception as e:
            return str(e)

@add_function(excel_to_sql)
class ExcelToSQLConfig(BaseModel):
    """
    Model for storing Excel data into a SQL table.
    
    Attributes:
    - excel_file_path: Path to the Excel file.
    - table_name: Name of the SQL table where data will be stored.
    """
    # engine: Engine = Field(..., description="SQLAlchemy engine connected to the target database")
    excel_file_path: str = Field(..., description="Path to the Excel file")
    table_name: str = Field(..., description="Name of the table to store data")
    user: str = Field(..., description="Username for the MySQL connection")
    password: str = Field(..., description="Password for the MySQL connection")
    host: str = Field(..., description="Hostname or IP address of the MySQL server")
    db_name: str = Field(..., description="Database name")


# Model for execute_query function
@add_function(execute_query)
class QueryExecutionConfig(BaseModel):
    """
    Model for executing a SQL query.
    
    Attributes:
    - query: The SQL query to execute.
    """
    # engine: Engine = Field(..., description="SQLAlchemy engine connected to the database")
    query: str = Field(..., description="SQL query string to be executed")
    user: str = Field(..., description="Username for the MySQL connection")
    password: str = Field(..., description="Password for the MySQL connection")
    host: str = Field(..., description="Hostname or IP address of the MySQL server")
    db_name: str = Field(..., description="Database name")

    class Config:
        arbitrary_types_allowed = True

def get_metadata(host, user, password, db, tables):
    metadata = []
    for table in tables:
        table_info = {}
        query_columns = f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = '{table}';
        """
        table_info['columns'] = execute_query(query_columns, user, password, host, db)
        
        query_sample = f'SELECT * FROM "{table}" LIMIT 5;'
        table_info['sample_rows'] = execute_query(query_sample, user, password, host, db)

        metadata.append({table: table_info})
    
    return metadata


@add_function(get_metadata)
class MetadataRetrievalConfig(BaseModel):
    """
    Tool for retrieving metadata from tables in a database.
    """
    host: str = Field(..., description="Hostname or IP address of the PostgreSQL server")
    user: str = Field(..., description="Username for the PostgreSQL connection")
    password: str = Field(..., description="Password for the PostgreSQL connection")
    db: str = Field(..., description="Database name to fetch metadata from")
    tables: List[str] = Field(..., description="List of table names to retrieve metadata from")
    limit: int = Field(5, description="Number of sample rows to fetch from each table (default: 5)")

    class Config:
        arbitrary_types_allowed = True

excel_to_sql_tool = Tool(ExcelToSQLConfig)()
query_execute_tool = Tool(QueryExecutionConfig)()
metadata_tool = Tool(MetadataRetrievalConfig)()
tools = [excel_to_sql_tool, query_execute_tool]