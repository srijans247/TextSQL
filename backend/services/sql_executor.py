
import os
import time

from decimal import Decimal
from datetime import date, datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlglot import parse, exp


# --------------------------------------------------
# ENVIRONMENT CONFIGURATION
# --------------------------------------------------

load_dotenv(override=True)

DB_USERNAME = os.getenv("READONLY_DB_USERNAME")
DB_PASSWORD = os.getenv("READONLY_DB_PASSWORD")
DB_HOST = os.getenv("READONLY_DB_HOST")
DB_PORT = os.getenv("READONLY_DB_PORT", "5432")
DB_NAME = os.getenv("READONLY_DB_NAME", "postgres")

if not all([DB_USERNAME, DB_PASSWORD, DB_HOST]):
    raise RuntimeError(
        "Missing read-only database credentials in .env"
    )


# --------------------------------------------------
# READ-ONLY DATABASE CONNECTION
# --------------------------------------------------

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USERNAME,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
    query={"sslmode": "require"}
)

readonly_engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10}
)


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

MAX_ROWS = 100
MAX_QUERY_LENGTH = 10000
STATEMENT_TIMEOUT = "5000ms"

# Only these tables can be accessed.
ALLOWED_TABLES = {
    "employees",
    "departments",
    "sales"
}


# --------------------------------------------------
# FORBIDDEN SQL OPERATIONS
# --------------------------------------------------

FORBIDDEN_NODES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Create,
    exp.Drop,
    exp.Alter,
    exp.Command,
    exp.Merge,
    exp.Transaction,
    exp.Set,
    exp.Into,
)


# --------------------------------------------------
# FORBIDDEN POSTGRESQL FUNCTIONS
# --------------------------------------------------

FORBIDDEN_FUNCTIONS = {
    # File access
    "PG_READ_FILE",
    "PG_READ_BINARY_FILE",
    "PG_WRITE_FILE",
    "PG_LS_DIR",
    "PG_STAT_FILE",

    # External database access
    "DBLINK",
    "DBLINK_EXEC",

    # Delays and configuration changes
    "PG_SLEEP",
    "SET_CONFIG",

    # Sequence modifications
    "NEXTVAL",
    "SETVAL",

    # Advisory locks
    "PG_ADVISORY_LOCK",
    "PG_ADVISORY_XACT_LOCK",
    "PG_TRY_ADVISORY_LOCK",
    "PG_TRY_ADVISORY_XACT_LOCK",
    "PG_ADVISORY_UNLOCK",
    "PG_ADVISORY_XACT_UNLOCK",

    # Large object operations
    "LO_IMPORT",
    "LO_EXPORT",
    "LO_UNLINK",
    "LO_CREATE",
    "LO_OPEN",

    # Server operations
    "PG_TERMINATE_BACKEND",
    "PG_CANCEL_BACKEND",
    "PG_RELOAD_CONF",
    "PG_NOTIFY"
}


# --------------------------------------------------
# SQL VALIDATION
# --------------------------------------------------

def validate_sql(sql):
    """
    Validate SQL before execution.

    Allows only one SELECT query using approved tables.
    Checks nested queries, CTEs and forbidden functions.
    """

    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL query cannot be empty.")

    if len(sql) > MAX_QUERY_LENGTH:
        raise ValueError("SQL query is too long.")

    # Parse PostgreSQL SQL.
    try:
        statements = parse(sql, read="postgres")
    except Exception:
        raise ValueError("Invalid PostgreSQL syntax.")

    # Allow only one SQL statement.
    if len(statements) != 1 or statements[0] is None:
        raise ValueError(
            "Only one SQL statement is allowed."
        )

    query = statements[0]

    # Only SELECT queries are allowed.
    if not isinstance(query, exp.Select):
        raise ValueError(
            "Only SELECT queries are allowed."
        )

    # Reject SELECT FOR UPDATE / FOR SHARE locking queries.
    if query.args.get("locks"):
        raise ValueError(
            "Locking SELECT queries are not allowed."
        )

    # Collect CTE names so their references are not
    # incorrectly treated as unauthorized tables.
    cte_names = set()

    for cte in query.find_all(exp.CTE):
        alias = cte.args.get("alias")

        if alias and alias.this:
            cte_names.add(alias.this.name.lower())

    # Inspect the entire query tree.
    # This includes CTEs and nested subqueries.
    for node in query.walk():

        # Reject forbidden SQL operations.
        if isinstance(node, FORBIDDEN_NODES):
            raise ValueError(
                "Query contains a forbidden SQL operation."
            )

        # Check potentially dangerous functions.
        if isinstance(node, exp.Func):

            if isinstance(node, exp.Anonymous):
                function_name = node.name.upper()
            else:
                function_name = node.sql_name().upper()

            if function_name in FORBIDDEN_FUNCTIONS:
                raise ValueError(
                    f"Function {function_name} is not allowed."
                )

        # Restrict table access.
        if isinstance(node, exp.Table):

            # Reject explicitly qualified table references.
            if node.catalog or node.db:
                raise ValueError(
                    "Schema-qualified or cross-database "
                    "table access is not allowed."
                )

            table_name = node.name.lower()

            # Allow approved tables and CTE references.
            if (
                table_name not in ALLOWED_TABLES
                and table_name not in cte_names
            ):
                raise ValueError(
                    f"Access to table '{table_name}' is not allowed."
                )

    # --------------------------------------------------
    # RESULT LIMIT
    # --------------------------------------------------

    # Fetch one extra row to detect truncation.
    limit_clause = query.args.get("limit")

    if limit_clause is None:

        query = query.limit(
            MAX_ROWS + 1,
            copy=True
        )

    else:

        limit_expression = limit_clause.expression

        if (
            isinstance(limit_expression, exp.Literal)
            and not limit_expression.is_string
        ):

            try:
                requested_limit = int(limit_expression.this)

            except (ValueError, TypeError):
                requested_limit = MAX_ROWS + 1

            if requested_limit > MAX_ROWS:
                query = query.limit(
                    MAX_ROWS + 1,
                    copy=True
                )

        else:

            query = query.limit(
                MAX_ROWS + 1,
                copy=True
            )

    return query.sql(dialect="postgres")


# --------------------------------------------------
# DATABASE VALUE CONVERSION
# --------------------------------------------------

def convert_value(value):
    """Convert database values into JSON-compatible values."""

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return value


# --------------------------------------------------
# SQL EXECUTION
# --------------------------------------------------

def execute_sql(sql):
    """
    Execute a validated SELECT query.

    Uses:
    - Read-only PostgreSQL connection
    - Read-only transaction
    - Statement timeout
    - Maximum 100 returned rows
    """

    # Validate before opening the connection.
    safe_sql = validate_sql(sql)

    start_time = time.perf_counter()

    try:

        with readonly_engine.connect() as connection:

            with connection.begin():

                # Enforce read-only transaction.
                connection.execute(
                    text("SET TRANSACTION READ ONLY")
                )

                # Set query execution timeout.
                connection.execute(
                    text(
                        f"SET LOCAL statement_timeout = "
                        f"'{STATEMENT_TIMEOUT}'"
                    )
                )

                # Execute validated SQL.
                result = connection.execute(
                    text(safe_sql)
                )

                columns = list(result.keys())

                # Fetch one extra row for truncation detection.
                raw_rows = result.fetchmany(
                    MAX_ROWS + 1
                )

                truncated = len(raw_rows) > MAX_ROWS

                # Keep only the first 100 rows.
                raw_rows = raw_rows[:MAX_ROWS]

                # Convert results into JSON-compatible dictionaries.
                rows = [
                    {
                        column: convert_value(value)
                        for column, value in zip(columns, row)
                    }
                    for row in raw_rows
                ]

        execution_time = round(
            (time.perf_counter() - start_time) * 1000,
            2
        )

        return {
            "status": "success",
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
            "execution_time_ms": execution_time
        }

    except ValueError:
        raise

    except Exception as error:

        # Log the actual exception on the server.
        print(
            "SQL EXECUTION ERROR:",
            repr(error)
        )

        raise RuntimeError(
            "Query execution failed. "
            "Check the SQL and database connection."
        )
