
from services.sql_executor import execute_sql, validate_sql


# Test 1: Simple SELECT query
print("\nTEST 1: Simple SELECT")

try:
    result = execute_sql(
        "SELECT employee_id, employee_name, salary FROM employees"
    )
    print(result)
except Exception as error:
    print("Failed:", error)


# Test 2: JOIN query
print("\nTEST 2: JOIN")

try:
    result = execute_sql("""
        SELECT e.employee_name, d.department_name
        FROM employees e
        JOIN departments d
        ON e.department_id = d.department_id
    """)
    print(result)
except Exception as error:
    print("Failed:", error)


# Test 3: UPDATE query should be rejected
print("\nTEST 3: UPDATE rejection")

try:
    validate_sql(
        "UPDATE employees SET salary = 90000 WHERE employee_id = 1"
    )
    print("ERROR: UPDATE was not rejected!")
except ValueError as error:
    print("Successfully rejected:", error)


# Test 4: Maximum 100 rows

# Test 4: Maximum 100 rows
print("\nTEST 4: Row limit")

try:
    result = execute_sql("""
        SELECT e.employee_id
        FROM employees e
        CROSS JOIN employees e2
        CROSS JOIN employees e3
        CROSS JOIN employees e4
        CROSS JOIN employees e5
    """)

    print("Returned rows:", result["row_count"])
    print("Truncated:", result["truncated"])

except Exception as error:
    print("Failed:", error)

