from services.sql_generator import generate_sql

question = "Show employees earning more than 60000"

try:
    result = generate_sql(question)

    print("\nGenerated SQL result:")
    print(result)

except Exception as error:
    print("\nError:", error)