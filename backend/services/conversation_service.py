
import json
from sqlalchemy import text

from database import engine


# --------------------------------------------------
# CREATE NEW CONVERSATION
# --------------------------------------------------

def create_conversation(conversation_id, question):
    """Save a new conversation in Supabase."""

    query = text("""
        INSERT INTO public.textsql_conversations (
            conversation_id,
            original_question
        )
        VALUES (
            :conversation_id,
            :question
        )
        RETURNING conversation_id
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "conversation_id": conversation_id,
                "question": question
            }
        )

        return str(result.scalar_one())


# --------------------------------------------------
# GET EXISTING CONVERSATION
# --------------------------------------------------

def get_conversation(conversation_id):
    """Retrieve an active conversation."""

    query = text("""
        SELECT
            conversation_id,
            original_question,
            clarification_history,
            created_at,
            updated_at,
            expires_at
        FROM public.textsql_conversations
        WHERE conversation_id = :conversation_id
        AND expires_at > NOW()
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {"conversation_id": conversation_id}
        ).mappings().first()

        if result is None:
            return None

        return dict(result)


# --------------------------------------------------
# ADD CLARIFICATION ANSWER
# --------------------------------------------------


def add_clarification(conversation_id, answer):
    """Append a clarification answer to conversation history."""

    query = text("""
        UPDATE public.textsql_conversations
        SET
            clarification_history =
                clarification_history ||
                jsonb_build_array(CAST(:answer AS TEXT)),
            updated_at = NOW()
        WHERE conversation_id = :conversation_id
        AND expires_at > NOW()
        RETURNING conversation_id
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "conversation_id": conversation_id,
                "answer": answer
            }
        )

        return result.scalar_one_or_none() is not None



# --------------------------------------------------
# DELETE COMPLETED CONVERSATION
# --------------------------------------------------

def delete_conversation(conversation_id):
    """Delete a conversation after successful completion."""

    query = text("""
        DELETE FROM public.textsql_conversations
        WHERE conversation_id = :conversation_id
    """)

    with engine.begin() as connection:
        result = connection.execute(
            query,
            {"conversation_id": conversation_id}
        )

        return result.rowcount > 0


# --------------------------------------------------
# CLEANUP EXPIRED CONVERSATIONS
# --------------------------------------------------

def delete_expired_conversations():
    """Delete conversations that have expired."""

    query = text("""
        DELETE FROM public.textsql_conversations
        WHERE expires_at <= NOW()
    """)

    with engine.begin() as connection:
        result = connection.execute(query)

        return result.rowcount
