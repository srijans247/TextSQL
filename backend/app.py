import os
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from google.genai.errors import ServerError

from database import test_connection, get_database_schema

from services.sql_generator import generate_sql
from services.sql_executor import execute_sql

from services.conversation_service import (
    create_conversation,
    get_conversation,
    add_clarification,
    delete_conversation
)

from services.chat_history_service import (
    save_chat,
    get_all_chats,
    get_chat,
    delete_chat
)


# ==================================================
# FLASK APPLICATION CONFIGURATION
# ==================================================

app = Flask(__name__)
CORS(app)


# ==================================================
# HELPER: VALIDATE UUID
# ==================================================

def is_valid_uuid(value):
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


# ==================================================
# HOME ROUTE
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "success",
        "message": "Text-to-SQL API is running!"
    }), 200


# ==================================================
# DATABASE HEALTH CHECK
# ==================================================

@app.route("/health", methods=["GET"])
def health():

    try:
        connected = test_connection()

        return jsonify({
            "status": "healthy",
            "database_connected": connected
        }), 200

    except Exception:

        app.logger.exception(
            "Database health check failed"
        )

        return jsonify({
            "status": "unhealthy",
            "database_connected": False
        }), 500


# ==================================================
# DATABASE SCHEMA
# ==================================================

@app.route("/schema", methods=["GET"])
def schema():

    try:
        database_schema = get_database_schema()

        return jsonify({
            "status": "success",
            "tables": database_schema
        }), 200

    except Exception:

        app.logger.exception(
            "Schema retrieval failed"
        )

        return jsonify({
            "status": "error",
            "message": "Unable to retrieve database schema."
        }), 500


# ==================================================
# GENERATE SQL
# ==================================================

@app.route("/generate-sql", methods=["POST"])
def generate_sql_route():

    try:
        data = request.get_json(silent=True) or {}

        question = data.get("question", "")

        if not isinstance(question, str) or not question.strip():
            return jsonify({
                "status": "error",
                "message": "Question is required."
            }), 400

        if len(question) > 10000:
            return jsonify({
                "status": "error",
                "message": "Question is too long."
            }), 400

        result = generate_sql(question.strip())

        return jsonify(result), 200

    except ValueError as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except ServerError as error:

        app.logger.warning(
            "Gemini API unavailable: %s", error
        )

        return jsonify({
            "status": "error",
            "message": "Gemini is temporarily unavailable. Please try again."
        }), 503

    except Exception:

        app.logger.exception(
            "SQL generation failed"
        )

        return jsonify({
            "status": "error",
            "message": "SQL generation failed. Please try again."
        }), 500


# ==================================================
# EXECUTE SQL
# ==================================================

@app.route("/execute-sql", methods=["POST"])
def execute_sql_route():

    try:
        data = request.get_json(silent=True) or {}

        sql = data.get("sql", "")

        if not isinstance(sql, str) or not sql.strip():
            return jsonify({
                "status": "error",
                "message": "SQL query is required."
            }), 400

        result = execute_sql(sql.strip())

        return jsonify(result), 200

    except ValueError as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except Exception:

        app.logger.exception(
            "SQL execution failed"
        )

        return jsonify({
            "status": "error",
            "message": "SQL execution failed. Please try again."
        }), 500


# ==================================================
# CHAT WITH CLARIFICATION ENGINE
# ==================================================

@app.route("/chat", methods=["POST"])
def chat():

    try:
        data = request.get_json(silent=True) or {}

        conversation_id = data.get("conversation_id")

        # ==========================================
        # NEW CONVERSATION
        # ==========================================

        if not conversation_id:

            question = data.get("question", "")

            if not isinstance(question, str) or not question.strip():
                return jsonify({
                    "status": "error",
                    "message": "Question is required."
                }), 400

            question = question.strip()

            if len(question) > 10000:
                return jsonify({
                    "status": "error",
                    "message": "Question is too long."
                }), 400

            # Generate SQL using Gemini
            result = generate_sql(question)

            # Check whether clarification is required
            if result["status"] == "needs_clarification":

                conversation_id = str(uuid.uuid4())

                # Save clarification conversation in Supabase
                create_conversation(
                    conversation_id,
                    question
                )

                return jsonify({
                    "status": "needs_clarification",
                    "conversation_id": conversation_id,
                    "clarification": result["clarification"]
                }), 200

            # Execute generated SQL
            execution_result = execute_sql(result["sql"])

            return jsonify({
                "status": "success",
                "sql": result["sql"],
                "data": execution_result
            }), 200

        # ==========================================
        # CONTINUE EXISTING CONVERSATION
        # ==========================================

        if not is_valid_uuid(conversation_id):
            return jsonify({
                "status": "error",
                "message": "Invalid conversation ID."
            }), 400

        # Retrieve conversation from Supabase
        conversation = get_conversation(conversation_id)

        if conversation is None:

            return jsonify({
                "status": "error",
                "message": "Conversation not found or expired."
            }), 404

        answer = data.get("answer", "")

        if not isinstance(answer, str) or not answer.strip():
            return jsonify({
                "status": "error",
                "message": "Clarification answer is required."
            }), 400

        answer = answer.strip()

        if len(answer) > 10000:
            return jsonify({
                "status": "error",
                "message": "Clarification answer is too long."
            }), 400

        # Save clarification answer in Supabase
        saved = add_clarification(
            conversation_id,
            answer
        )

        if not saved:
            return jsonify({
                "status": "error",
                "message": "Conversation could not be updated or has expired."
            }), 404

        # Retrieve updated conversation
        conversation = get_conversation(conversation_id)

        if conversation is None:
            return jsonify({
                "status": "error",
                "message": "Conversation not found or expired."
            }), 404

        # Read clarification history
        history = conversation["clarification_history"]

        # Handle JSON returned as a string if necessary
        if isinstance(history, str):
            import json
            history = json.loads(history)

        # Combine original question and clarification history
        combined_question = (
            "Original user question: "
            + conversation["original_question"]
            + "\nClarification history:\n"
            + "\n".join(
                f"User clarification {i + 1}: {item}"
                for i, item in enumerate(history)
            )
        )

        # Generate SQL again using Gemini
        result = generate_sql(combined_question)

        # Another clarification is required
        if result["status"] == "needs_clarification":

            return jsonify({
                "status": "needs_clarification",
                "conversation_id": conversation_id,
                "clarification": result["clarification"]
            }), 200

        # Execute generated SQL
        execution_result = execute_sql(result["sql"])

        # Delete clarification conversation after success
        delete_conversation(conversation_id)

        return jsonify({
            "status": "success",
            "sql": result["sql"],
            "data": execution_result
        }), 200

    except ValueError as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except ServerError as error:

        app.logger.warning(
            "Gemini API unavailable: %s", error
        )

        return jsonify({
            "status": "error",
            "message": "Gemini is temporarily unavailable. Please try again."
        }), 503

    except Exception:

        app.logger.exception(
            "Chat endpoint failed"
        )

        return jsonify({
            "status": "error",
            "message": "Something went wrong while processing your request."
        }), 500


# ==================================================
# SAVE CHAT HISTORY
# ==================================================

@app.route("/chat-history", methods=["POST"])
def save_chat_history():

    try:
        data = request.get_json(silent=True) or {}

        chat_id = data.get("chat_id")
        title = data.get("title")
        messages = data.get("messages")

        if not isinstance(title, str) or not title.strip():
            return jsonify({
                "status": "error",
                "message": "Chat title is required."
            }), 400

        if len(title) > 200:
            return jsonify({
                "status": "error",
                "message": "Chat title is too long."
            }), 400

        if not isinstance(messages, list):
            return jsonify({
                "status": "error",
                "message": "Messages must be a list."
            }), 400

        if len(messages) > 500:
            return jsonify({
                "status": "error",
                "message": "Too many messages."
            }), 400

        # Generate chat ID if not supplied
        if not chat_id:
            chat_id = str(uuid.uuid4())

        elif not is_valid_uuid(chat_id):
            return jsonify({
                "status": "error",
                "message": "Invalid chat ID."
            }), 400

        # Save chat in Supabase
        saved_id = save_chat(
            chat_id,
            title.strip(),
            messages
        )

        return jsonify({
            "status": "success",
            "chat_id": saved_id,
            "message": "Chat saved successfully."
        }), 200

    except (TypeError, ValueError) as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

    except Exception:

        app.logger.exception(
            "Saving chat history failed"
        )

        return jsonify({
            "status": "error",
            "message": "Unable to save chat history."
        }), 500


# ==================================================
# GET ALL CHAT HISTORY
# ==================================================

@app.route("/chat-history", methods=["GET"])
def retrieve_chat_history():

    try:
        chats = get_all_chats()

        return jsonify({
            "status": "success",
            "chats": chats
        }), 200

    except Exception:

        app.logger.exception(
            "Retrieving chat history failed"
        )

        return jsonify({
            "status": "error",
            "message": "Unable to retrieve chat history."
        }), 500


# ==================================================
# GET ONE CHAT
# ==================================================

@app.route("/chat-history/<chat_id>", methods=["GET"])
def retrieve_one_chat(chat_id):

    try:

        if not is_valid_uuid(chat_id):
            return jsonify({
                "status": "error",
                "message": "Invalid chat ID."
            }), 400

        chat_data = get_chat(chat_id)

        if chat_data is None:
            return jsonify({
                "status": "error",
                "message": "Chat not found."
            }), 404

        return jsonify({
            "status": "success",
            "chat": chat_data
        }), 200

    except Exception:

        app.logger.exception(
            "Retrieving individual chat failed"
        )

        return jsonify({
            "status": "error",
            "message": "Unable to retrieve chat."
        }), 500


# ==================================================
# DELETE CHAT HISTORY
# ==================================================

@app.route("/chat-history/<chat_id>", methods=["DELETE"])
def remove_chat_history(chat_id):

    try:

        if not is_valid_uuid(chat_id):
            return jsonify({
                "status": "error",
                "message": "Invalid chat ID."
            }), 400

        deleted = delete_chat(chat_id)

        if not deleted:
            return jsonify({
                "status": "error",
                "message": "Chat not found."
            }), 404

        return jsonify({
            "status": "success",
            "message": "Chat deleted successfully."
        }), 200

    except Exception:

        app.logger.exception(
            "Deleting chat history failed"
        )

        return jsonify({
            "status": "error",
            "message": "Unable to delete chat."
        }), 500


# ==================================================
# RUN FLASK APPLICATION
# ==================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
