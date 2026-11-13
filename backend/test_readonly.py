
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv(override=True)

url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("READONLY_DB_USERNAME"),
    password=os.getenv("READONLY_DB_PASSWORD"),
    host=os.getenv("READONLY_DB_HOST"),
    port=int(os.getenv("READONLY_DB_PORT", "5432")),
    database=os.getenv("READONLY_DB_NAME", "postgres"),
    query={"sslmode": "require"}
)

engine = create_engine(url, pool_pre_ping=True)

try:
    with engine.connect() as connection:
        print("Connection successful!")

        print(
            "Read-only mode:",
            connection.execute(
                text("SHOW transaction_read_only")
            ).scalar()
        )

        print(
            "Test query:",
            connection.execute(text("SELECT 1")).scalar()
        )

except Exception as error:
    print("Connection failed:", repr(error))

finally:
    engine.dispose()
