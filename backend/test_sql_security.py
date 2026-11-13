
from services.sql_executor import validate_sql


def run_test(name, sql, should_pass=False):
    print(f"\n{name}")

    try:
        result = validate_sql(sql)

        if should_pass:
            print("PASSED:", result)
        else:
            print("FAILED: Unsafe SQL was accepted!")

    except ValueError as error:

        if should_pass:
            print("FAILED:", error)
        else:
            print("PASSED: Rejected:", error)


# Test 1: Approved table
run_test(
    "TEST 1: Approved table",
    "SELECT * FROM employees",
    should_pass=True
)

# Test 2: Unauthorized table
run_test(
    "TEST 2: Unauthorized table",
    "SELECT * FROM users"
)

# Test 3: Dangerous function
run_test(
    "TEST 3: Dangerous function",
    "SELECT pg_sleep(10)"
)

# Test 4: Multiple SQL statements
run_test(
    "TEST 4: Multiple statements",
    "SELECT * FROM employees; SELECT * FROM sales"
)

# Test 5: Nested write operation
run_test(
    "TEST 5: Nested write operation",
    """
    WITH changed AS (
        DELETE FROM employees
        RETURNING employee_id
    )
    SELECT * FROM changed
    """
)

# Test 6: Approved JOIN
run_test(
    "TEST 6: Approved JOIN",
    """
    SELECT e.employee_name, d.department_name
    FROM employees e
    JOIN departments d
    ON e.department_id = d.department_id
    """,
    should_pass=True
)

# Test 7: Schema-qualified table
run_test(
    "TEST 7: Schema-qualified table",
    "SELECT * FROM public.employees"
)
