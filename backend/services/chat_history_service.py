
import json
from sqlalchemy import text

from database import engine


# ==================================================
# SAVE OR UPDATE CHAT HISTORY
# ==================================================

def save_chat(chat_id, title, messages):
    """Save a chat or update an existing chat."""

    query = text("""
        INSERT INTO public.textsql_chat_history (
            chat_id,
            title,
            messages
        )
        VALUES (
            :chat_id,
            :title,
            CAST(:messages AS JSONB)
        )
        ON CONFLICT (chat_id)
        DO UPDATE SET
            title = EXCLUDED.title,
            messages = EXCLUDED.messages,
            updated_at = NOW()
        RETURNING chat_id
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "chat_id": chat_id,
                "title": title,
                "messages": json.dumps(messages)
            }
        )

        return str(result.scalar_one())


# ==================================================
# GET ALL CHAT HISTORY
# ==================================================

def get_all_chats():
    """Retrieve all saved chats, newest first."""

    query = text("""
        SELECT
            chat_id,
            title,
            messages,
            created_at,
            updated_at
        FROM public.textsql_chat_history
        ORDER BY updated_at DESC
    """)

    with engine.connect() as connection:
        result = connection.execute(query).mappings().all()

        chats = []

        for row in result:
            chat = dict(row)

            # Convert UUID and timestamps into JSON-compatible values.
            chat["chat_id"] = str(chat["chat_id"])
            chat["created_at"] = chat["created_at"].isoformat()
            chat["updated_at"] = chat["updated_at"].isoformat()

            chats.append(chat)

        return chats


# ==================================================
# GET ONE CHAT
# ==================================================

def get_chat(chat_id):
    """Retrieve a specific saved conversation."""

    query = text("""
        SELECT
            chat_id,
            title,
            messages,
            created_at,
            updated_at
        FROM public.textsql_chat_history
        WHERE chat_id = :chat_id
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"chat_id": chat_id}
        ).mappings().first()

        if result is None:
            return None

        chat = dict(result)

        chat["chat_id"] = str(chat["chat_id"])
        chat["created_at"] = chat["created_at"].isoformat()
        chat["updated_at"] = chat["updated_at"].isoformat()

        return chat


# ==================================================
# DELETE CHAT
# ==================================================

def delete_chat(chat_id):
    """Delete a saved conversation."""

    query = text("""
        DELETE FROM public.textsql_chat_history
        WHERE chat_id = :chat_id
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {"chat_id": chat_id}
        )

        return result.rowcount > 0
