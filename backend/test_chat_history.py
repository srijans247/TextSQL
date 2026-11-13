
import uuid

from services.chat_history_service import (
    save_chat,
    get_all_chats,
    get_chat,
    delete_chat
)

chat_id = str(uuid.uuid4())

sample_messages = [
    {
        "role": "user",
        "content": "Show all employees"
    },
    {
        "role": "assistant",
        "type": "result",
        "content": "Your query was executed successfully!",
        "sql": "SELECT * FROM employees",
        "data": {
            "columns": ["employee_id", "employee_name"],
            "rows": [
                {
                    "employee_id": 1,
                    "employee_name": "Rahul Sharma"
                }
            ],
            "row_count": 1,
            "status": "success"
        }
    }
]

print("\nTEST 1: Save chat")

saved_id = save_chat(
    chat_id,
    "Show all employees",
    sample_messages
)

print("Saved chat:", saved_id)


print("\nTEST 2: Retrieve one chat")

chat = get_chat(chat_id)

print("Chat title:", chat["title"])
print("Messages:", chat["messages"])


print("\nTEST 3: Retrieve all chats")

chats = get_all_chats()

print("Total saved chats:", len(chats))


print("\nTEST 4: Delete chat")

deleted = delete_chat(chat_id)

print("Chat deleted:", deleted)


print("\nAll chat history tests completed!")
