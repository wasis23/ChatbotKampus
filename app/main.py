import os
import sys
import argparse
from dotenv import load_dotenv

# Memuat berkas konfigurasi .env di level teratas
load_dotenv()

from app.utils import (
    print_header, 
    print_info, 
    print_success, 
    print_error, 
    print_warning, 
    BOLD, 
    RESET, 
    CYAN, 
    GREEN, 
    YELLOW,
    WHITE
)

print_info("Sistem sedang memuat pustaka AI (PyTorch/Transformers). Mohon tunggu beberapa saat...")
from app.rag_service import RAGService

def run_cli_chatbot():
    """Menjalankan Chatbot Akademik berbasis CLI Interaktif."""
    print_header("SISTEM CHATBOT AKADEMIK MAHASISWA - UNIVERSITAS KARYA BANGSA")
    print_info("Sedang menginisialisasi modul RAG & Model Embedding...")
    print_info("Silakan tunggu sebaya (Proses ini memakan waktu beberapa detik)...")
    
    try:
        # Inisialisasi Service RAG
        rag = RAGService()
        print_success("Inisialisasi berhasil! Chatbot siap melayani pertanyaan Anda.")
    except Exception as e:
        print_error(f"Gagal memuat modul sistem: {str(e)}")
        print_warning("Pastikan Anda sudah menginstal dependensi dan mengonfigurasi berkas .env")
        sys.exit(1)
        
    print_info("Ketik 'menu' untuk melihat daftar perintah bantuan.")
    print_info("Ketik 'keluar' atau 'exit' untuk mengakhiri sesi chat.")
    
    while True:
        try:
            print(f"\n{WHITE}{'-'*70}{RESET}")
            user_input = input(f"{BOLD}{CYAN}Mahasiswa >> {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            print_info("Keluar dari program secara aman. Sampai jumpa!")
            break
            
        if not user_input:
            continue
            
        # Pengecekan Perintah Administratif Lokal
        user_input_lower = user_input.lower()
        if user_input_lower in ["exit", "keluar", "quit", "q"]:
            print_info("Terima kasih telah menggunakan layanan Chatbot Akademik Universitas Karya Bangsa!")
            break
            
        if user_input_lower == "menu":
            show_cli_menu()
            continue
            
        if user_input_lower == "index":
            try:
                res = rag.index_documents()
                if res["status"] == "success":
                    print_success(res["message"])
                else:
                    print_error(res["message"])
            except Exception as e:
                print_error(f"Gagal menjalankan proses indexing: {str(e)}")
            continue
            
        # Jalankan RAG/Intent Query
        print(f"{YELLOW}Chatbot sedang mengetik...{RESET}", end="\r")
        try:
            result = rag.query(user_input)
            # Bersihkan baris pengetikan
            print(" " * 50, end="\r")
            
            # Tampilkan Jawaban Chatbot
            print(f"{GREEN}{BOLD}AI Chatbot:{RESET} {result['answer']}")
            
            # A. Jika respons berupa standard RAG query, tampilkan sumber dokumen pendukung
            if result.get("type") == "rag_query" and result.get("sources"):
                print(f"\n{CYAN}{BOLD}[Rujukan Dokumen Resmi]:{RESET}")
                for src in result["sources"]:
                    print(f" • File: {src['filename']} (Halaman: {src['page']}, Kategori: {src['category']}, Kemiripan: {src['confidence']:.1f}%)")
                    
            # B. Jika respons berupa permintaan file (document request)
            elif result.get("type") == "document_request" and result.get("status") == "found":
                print(f"\n{YELLOW}{BOLD}[Akses Unduhan Berkas Lokal]:{RESET}")
                print(f" • Jalur Lokal: {result['path']}")
                print(f" • Unduh via Web Server: http://localhost:{os.getenv('API_PORT', '8000')}/download/{result['filename']}")
                
        except Exception as e:
            # Bersihkan baris pengetikan
            print(" " * 50, end="\r")
            print_error(f"Terjadi kegagalan pemrosesan pertanyaan: {str(e)}")

def show_cli_menu():
    """Menampilkan bantuan daftar menu CLI."""
    print_header("DAFTAR PERINTAH CHATBOT")
    print(" 1. Ketik pertanyaan akademik secara langsung.")
    print("    Contoh: 'Apa saja syarat sidang skripsi?' atau 'Berapa UKT Golongan III prodi SI?'")
    print(" 2. Ketik permintaan file dokumen secara langsung.")
    print("    Contoh: 'Tolong kirim kalender akademik' atau 'unduh SOP Cuti'")
    print(" 3. Ketik 'index' untuk melakukan kompilasi & pembaruan database vektor.")
    print(" 4. Ketik 'menu' untuk menampilkan bantuan instruksi ini kembali.")
    print(" 5. Ketik 'keluar' atau 'exit' untuk menutup sesi chatbot.")
    print(f"{CYAN}{'='*70}{RESET}")

def start_api_server():
    """Memulai API Web Server berbasis FastAPI untuk integrasi website."""
    print_info("Menginisialisasi Server Web FastAPI...")
    import uvicorn
    from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response, Request, Depends
    from fastapi.responses import FileResponse, RedirectResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
    from typing import Dict, Optional
    from app.database import init_db, get_all_settings, update_setting, log_chat, get_chat_history, get_dashboard_stats, get_chat_history_for_session, delete_session
    
    # Inisialisasi Database
    init_db()
    
    app = FastAPI(
        title="API Chatbot Akademik RAG",
        description="Layanan backend REST API untuk chatbot pelayanan mahasiswa berbasis RAG & LLM.",
        version="1.0.0"
    )
    
    # Konfigurasi Cross-Origin Resource Sharing (CORS) agar bisa diakses oleh website frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Konfigurasi Direktori Statis untuk Widget Bubble Chat
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    app.mount("/widget", StaticFiles(directory=static_dir), name="widget")
    
    # Inisialisasi malas (lazy loading) layanan RAG untuk mencegah crash saat startup
    # jika Kunci API belum diisi di file .env
    rag_service = None
    
    def get_rag():
        nonlocal rag_service
        if rag_service is None:
            rag_service = RAGService()
        return rag_service

    class QueryRequest(BaseModel):
        message: str
        session_id: Optional[str] = None

    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "service": "Chatbot Akademik RAG API",
            "version": "1.0.0",
            "author": "LuckyMan"
        }

    @app.get("/login")
    def serve_login():
        """Menyajikan halaman UI Login."""
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "login.html")
        return FileResponse(file_path)

    @app.post("/api/login")
    def process_login(response: Response, username: str = Form(...), password: str = Form(...)):
        """Validasi login admin."""
        valid_user = os.getenv("ADMIN_USERNAME", "admin")
        valid_pass = os.getenv("ADMIN_PASSWORD", "admin")
        
        if username == valid_user and password == valid_pass:
            response.set_cookie(key="isa_admin_token", value="authenticated", httponly=True, max_age=86400)
            return {"status": "success"}
        else:
            raise HTTPException(status_code=401, detail="Username atau password salah")

    @app.get("/api/logout")
    def process_logout(response: Response):
        """Keluar dari sesi admin."""
        response.delete_cookie("isa_admin_token")
        return RedirectResponse(url="/login")

    @app.get("/admin")
    def serve_admin(request: Request):
        """Menyajikan halaman UI Admin Panel dengan proteksi cookie."""
        if request.cookies.get("isa_admin_token") != "authenticated":
            return RedirectResponse(url="/login")
            
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "admin.html")
        return FileResponse(file_path)

    @app.get("/demo")
    def serve_demo():
        """Menyajikan halaman UI Simulasi Widget Chatbot."""
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_widget.html")
        return FileResponse(file_path)

    @app.post("/query")
    def process_query(req: QueryRequest):
        """Endpoint utama untuk memproses obrolan dari website frontend."""
        try:
            service = get_rag()
            # Gunakan session ID dari frontend atau buat baru jika kosong
            if req.session_id:
                session_id = req.session_id
            else:
                import uuid
                session_id = f"#S-{str(uuid.uuid4())[:4].upper()}"
            
            # 1. Cek Guardrail Filter Kata Kasar
            blocked_words_str = get_all_settings().get('blocked_words', '')
            if blocked_words_str:
                blocked_words = [w.strip().lower() for w in blocked_words_str.split(',') if w.strip()]
                msg_lower = req.message.lower()
                for word in blocked_words:
                    if word in msg_lower:
                        fallback = get_all_settings().get('fallback_response', "Pesan ditolak.")
                        guard_response = f"Pesan ditolak karena mengandung kata terlarang/tidak pantas: '{word}'."
                        log_chat(session_id, req.message, guard_response, "Diblokir")
                        return {"answer": fallback, "sources": []}
            
            # 2. Tarik riwayat percakapan sebelumnya untuk memori kontekstual (Fase 3)
            chat_history = get_chat_history_for_session(session_id, limit=4)
            
            result = service.query(req.message, chat_history=chat_history)
            
            # Simpan log chat
            log_chat(session_id, req.message, result.get("answer", ""))
            
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal memproses query: {str(e)}")

    @app.post("/index")
    def trigger_indexing():
        """Endpoint untuk memaksa kompilasi database vektor dari PDF baru."""
        try:
            service = get_rag()
            result = service.index_documents()
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal melakukan indexing dokumen: {str(e)}")

    @app.get("/documents")
    def get_documents_list():
        """Endpoint untuk mendapatkan daftar seluruh berkas PDF dan MD akademik."""
        try:
            service = get_rag()
            files_info = []
            for f in os.listdir(service.documents_dir):
                if f.endswith(".pdf") or f.endswith(".md"):
                    filepath = os.path.join(service.documents_dir, f)
                    stats = os.stat(filepath)
                    
                    size_bytes = stats.st_size
                    if size_bytes < 1024 * 1024:
                        size_str = f"{round(size_bytes / 1024, 2)} KB"
                    else:
                        size_str = f"{round(size_bytes / (1024 * 1024), 2)} MB"
                        
                    files_info.append({
                        "filename": f,
                        "size_formatted": size_str,
                        "modified_at": stats.st_mtime
                    })
            return {
                "documents": files_info, 
                "count": len(files_info),
                "database_chunks": service.retrieval_service.get_collection_size()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal mengambil daftar dokumen: {str(e)}")

    @app.get("/download/{filename}")
    def download_file(filename: str):
        """Endpoint untuk mengunduh berkas akademik resmi secara langsung."""
        try:
            service = get_rag()
            file_path = os.path.join(service.documents_dir, filename)
            # Validasi keamanan untuk mencegah traversal direktori
            if not os.path.exists(file_path) or not (filename.endswith(".pdf") or filename.endswith(".md")):
                raise HTTPException(status_code=404, detail="Berkas dokumen tidak ditemukan di server.")
            
            media_type = "text/markdown" if filename.endswith(".md") else "application/pdf"
            
            return FileResponse(
                path=file_path, 
                filename=filename, 
                media_type=media_type
            )
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal mengunduh berkas: {str(e)}")

    @app.post("/upload")
    async def upload_document(file: UploadFile = File(...)):
        """Endpoint untuk mengunggah dokumen PDF atau MD baru ke Knowledge Base."""
        try:
            service = get_rag()
            if not (file.filename.endswith(".pdf") or file.filename.endswith(".md")):
                raise HTTPException(status_code=400, detail="Hanya file PDF dan MD yang diperbolehkan.")
            
            file_path = os.path.join(service.documents_dir, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            
            return {"status": "success", "filename": file.filename, "message": "File berhasil diunggah."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal mengunggah file: {str(e)}")

    @app.delete("/documents/{filename}")
    def delete_document(filename: str):
        """Endpoint untuk menghapus dokumen PDF atau MD dari Knowledge Base."""
        try:
            service = get_rag()
            file_path = os.path.join(service.documents_dir, filename)
            if not os.path.exists(file_path) or not (filename.endswith(".pdf") or filename.endswith(".md")):
                raise HTTPException(status_code=404, detail="Berkas tidak ditemukan.")
            
            os.remove(file_path)
            return {"status": "success", "message": f"{filename} berhasil dihapus."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal menghapus file: {str(e)}")

    @app.get("/api/settings")
    def get_settings():
        """Mengambil seluruh pengaturan admin."""
        return get_all_settings()

    @app.post("/api/settings")
    def save_settings(settings: Dict[str, str]):
        """Menyimpan pengaturan admin yang diupdate."""
        for key, value in settings.items():
            update_setting(key, value)
        return {"status": "success"}
        
    @app.get("/api/chat_history")
    def get_chats():
        """Mengambil riwayat percakapan."""
        return get_chat_history(50)

    @app.delete("/api/chats/{session_id}")
    def remove_session(session_id: str):
        """Menghapus seluruh percakapan berdasarkan session ID."""
        try:
            delete_session(session_id)
            return {"status": "success", "message": f"Sesi {session_id} berhasil dihapus"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal menghapus sesi: {str(e)}")

    @app.get("/api/dashboard_stats")
    def dashboard_stats():
        """Mengambil data agregat untuk dashboard (Fase 3)."""
        return get_dashboard_stats()

    # Jalankan server web
    port = int(os.getenv("API_PORT", 8000))
    print_success(f"Server API FastAPI berjalan di: http://localhost:{port}")
    print_info("Tekan CTRL+C untuk mematikan server.")
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Konfigurasi Parser Argumen Command Line
    parser = argparse.ArgumentParser(description="Program Pelayanan Chatbot RAG Kampus.")
    parser.add_argument(
        "--server", 
        action="store_true", 
        help="Jalankan dalam mode Web API Server FastAPI."
    )
    parser.add_argument(
        "--index", 
        action="store_true", 
        help="Jalankan proses indeks dokumen PDF langsung lalu keluar."
    )
    args = parser.parse_args()
    
    # Jalankan sesuai argumen yang dipilih
    if args.index:
        rag = RAGService()
        rag.index_documents()
    elif args.server:
        start_api_server()
    else:
        # CLI Mode (Default)
        run_cli_chatbot()
