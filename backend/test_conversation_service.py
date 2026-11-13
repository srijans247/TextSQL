
import uuid

from services.conversation_service import (
    create_conversation,
    get_conversation,
    add_clarification,
    delete_conversation
)


# Generate a unique conversation ID
conversation_id = str(uuid.uuid4())

print("\nTEST 1: Create conversation")

try:
    created_id = create_conversation(
        conversation_id,
        "Show me the best employees"
    )

    print("Created conversation:", created_id)

except Exception as error:
    print("Failed:", repr(error))
    raise


print("\nTEST 2: Retrieve conversation")

conversation = get_conversation(conversation_id)

print("Conversation:", conversation)

if conversation is None:
    raise RuntimeError("Conversation was not found.")


print("\nTEST 3: Add clarification")

success = add_clarification(
    conversation_id,
    "Employees with the highest total sales"
)

print("Clarification saved:", success)


print("\nTEST 4: Verify clarification history")

updated_conversation = get_conversation(conversation_id)

print(
    "Clarification history:",
    updated_conversation["clarification_history"]
)


print("\nTEST 5: Delete conversation")

deleted = delete_conversation(conversation_id)

print("Conversation deleted:", deleted)


print("\nAll conversation service tests completed!")
