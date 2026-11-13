
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL

load_dotenv(override=True)

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

if not all([DB_USERNAME, DB_PASSWORD, DB_HOST]):
    raise RuntimeError("Missing database credentials in .env")

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USERNAME,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
    query={"sslmode": "require"}
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10}
)


def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Database connection successful!")
            return result.scalar() == 1
    except Exception as e:
        print("DATABASE CONNECTION ERROR:", repr(e))
        raise


def get_database_schema():
    inspector = inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names(schema="public"):
        columns = inspector.get_columns(table_name, schema="public")

        schema[table_name] = [
            {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": column["nullable"]
            }
            for column in columns
        ]

    return schema
