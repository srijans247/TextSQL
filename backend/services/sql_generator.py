
import os
import json
from dotenv import load_dotenv
from google import genai
from sqlglot import parse, exp

from database import get_database_schema

load_dotenv(override=True)

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def generate_sql(question):
    """Generate a PostgreSQL SELECT query from a natural-language question."""

    if not API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing from .env")

    if not question or not question.strip():
        raise ValueError("Please provide a question.")

    # Retrieve the actual Supabase database schema
    schema = get_database_schema()

    if not schema:
        raise RuntimeError("No database tables were found.")

    schema_text = json.dumps(schema, indent=2)

    client = genai.Client(api_key=API_KEY)

    prompt = f"""
You are an expert PostgreSQL query generator.

DATABASE SCHEMA:
{schema_text}

USER QUESTION:
{question}

INSTRUCTIONS:
1. Understand the user's question.
2. Use only tables and columns from the supplied schema.
3. Generate PostgreSQL SELECT queries only.


4. CLARIFICATION IS MANDATORY WHEN THE USER'S INTENT IS AMBIGUOUS.

5. Do not guess what subjective words mean.

6. Words such as "best", "top", "good", "better",
   "highest-performing" and "most successful" require clarification
   when multiple reasonable interpretations exist.

7. Example:
   If the user asks "Show me the best employees",
   DO NOT generate SQL immediately.

   Return a JSON response with:
   - status: needs_clarification
   - sql: empty string
   - clarification: How would you like to define the best employees:
     highest total sales, highest performance rating, or highest salary?

8. Generate SQL only after the user provides enough information
   to identify the intended metric.

9. Never silently choose a metric just because a matching
   database column exists.

10. Ask only one concise clarification question at a time.


SECURITY:
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
  CREATE or TRUNCATE statements.
- Never generate multiple statements.
- Never use SELECT INTO.

Return valid JSON with these fields:
{{
    "status": "success" or "needs_clarification",
    "sql": "SQL query or empty string",
    "clarification": "Question or empty string"
}}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "temperature": 0
        }
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        raise ValueError("Gemini returned invalid JSON.")

    status = result.get("status")

    if status == "needs_clarification":
        clarification = result.get("clarification", "").strip()

        if not clarification:
            raise ValueError("Gemini returned an empty clarification.")

        return {
            "status": "needs_clarification",
            "clarification": clarification
        }

    if status != "success":
        raise ValueError("Unexpected response from Gemini.")

    generated_sql = result.get("sql", "").strip()

    if not generated_sql:
        raise ValueError("Gemini did not generate SQL.")

    # Parse SQL using PostgreSQL syntax
    statements = parse(generated_sql, read="postgres")

    if len(statements) != 1 or statements[0] is None:
        raise ValueError("Only one SQL statement is allowed.")

    query = statements[0]

    # Only allow a SELECT query
    if not isinstance(query, exp.Select):
        raise ValueError("Only SELECT queries are allowed.")

    # Reject SELECT INTO
    if query.args.get("into") is not None:
        raise ValueError("SELECT INTO is not allowed.")

    return {
        "status": "success",
        "sql": generated_sql
    }
