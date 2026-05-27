import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'isa_chatbot.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Tabel Pengaturan (Settings)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Tabel Riwayat Percakapan (Chat History)
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            user_message TEXT,
            bot_response TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed Default Settings jika kosong
    c.execute("SELECT count(*) FROM settings")
    if c.fetchone()[0] == 0:
        default_prompt = (
            "Anda adalah AI Customer Service resmi dari Politeknik Indonusa Surakarta. Tugas utama Anda adalah memberikan layanan informasi terbaik kepada mahasiswa dan calon mahasiswa secara ramah, sangat sopan, solutif, dan penuh kehangatan layaknya staf customer service profesional yang handal.\n\n"
            "Aturan:\n"
            "1. SAPAAN HANGAT & SOPAN: Selalu sapa pengguna dengan sebutan yang ramah.\n"
            "2. PRIORITAS DOKUMEN RUJUKAN: Periksa KONTEKS DOKUMEN RUJUKAN RESMI di bawah sebelum merespons.\n"
            "3. PENGECUALIAN PERCAKAPAN UMUM: Untuk obrolan biasa, jawab santai.\n"
            "4. STRUKTUR JAWABAN YANG RAPI: Sajikan dengan format numbering atau bullet points secara rapi jika memungkinkan."
        )
        defaults = [
            ('system_prompt', default_prompt),
            ('llm_model', 'gpt-4o-mini'),
            ('temperature', '0.4'),
            ('top_k', '4'),
            ('fallback_response', 'Mohon maaf, saat ini sistem sedang memproses terlalu banyak permintaan atau data tidak ditemukan. Silakan hubungi langsung bagian administrasi.'),
            ('blocked_words', 'bodoh,jelek,kasar,hacking,ignore all previous instructions'),
            ('prompt_injection_guard', '1')
        ]
        c.executemany("INSERT INTO settings (key, value) VALUES (?, ?)", defaults)
        
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return default

def update_setting(key, value):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_all_settings():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM settings")
    rows = c.fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

def log_chat(session_id, user_message, bot_response, status="Terjawab"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO chat_history (session_id, user_message, bot_response, status) VALUES (?, ?, ?, ?)",
        (session_id, user_message, bot_response, status)
    )
    conn.commit()
    conn.close()

def get_chat_history(limit=50):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM chat_history ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_chat_history_for_session(session_id, limit=4):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT user_message, bot_response FROM chat_history WHERE session_id=? ORDER BY created_at DESC LIMIT ?", 
        (session_id, limit)
    )
    rows = c.fetchall()
    conn.close()
    # Return in chronological order (oldest first)
    return [{"user": row['user_message'], "bot": row['bot_response']} for row in reversed(rows)]

def delete_session(session_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE session_id=?", (session_id,))
    conn.commit()
    conn.close()

def get_dashboard_stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Pertanyaan hari ini
    c.execute("SELECT count(*) FROM chat_history WHERE date(created_at) = date('now')")
    today_queries = c.fetchone()[0]
    
    # Pengguna aktif (Unique Sessions hari ini)
    c.execute("SELECT count(DISTINCT session_id) FROM chat_history WHERE date(created_at) = date('now')")
    active_users = c.fetchone()[0]
    
    # Token usage (approximate: 350 tokens per interaction)
    c.execute("SELECT count(*) FROM chat_history")
    total_queries = c.fetchone()[0]
    tokens_used = total_queries * 350
    cost_usd = (tokens_used / 1000) * 0.00015
    
    conn.close()
    return {
        "today_queries": today_queries,
        "active_users": active_users,
        "tokens_used": tokens_used,
        "cost_usd": cost_usd
    }
