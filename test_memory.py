import os
import sys
from dotenv import load_dotenv
load_dotenv()
from app.database import init_db, log_chat, get_chat_history_for_session
from app.llm_service import LLMService

init_db()

session_id = "#S-TEST"
# mock db
log_chat(session_id, "halo nama saya wasis, minat saya komputer", "halo wasis! ada yang bisa dibantu?")

chat_history = get_chat_history_for_session(session_id, limit=4)
print("HISTORY DARI DB:")
print(chat_history)

llm = LLMService()
result = llm.generate_answer("apa prodi yang cocok untuk saya?", contexts=[], chat_history=chat_history)
print("HASIL LLM:")
print(result)
