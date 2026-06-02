import os
from typing import Dict, Any, List, Optional
from app.pdf_loader import load_documents
from app.chunking import split_documents
from app.embedding import get_embedding_model
from app.retrieval import RetrievalService
from app.llm_service import LLMService
from app.utils import print_info, print_success, print_error, print_warning

def detect_document_request(query: str, documents_dir: str) -> Optional[Dict[str, Any]]:
    """
    Mendeteksi secara cerdas (intent detection) apakah pengguna meminta untuk mengunduh 
    atau dikirimkan dokumen fisik PDF resmi, lalu mencocokkannya secara fuzzy dengan berkas lokal.
    """
    query_lower = query.lower()
    
    # 1. Definisikan kata kunci pemicu permintaan berkas
    triggers = ["kirim", "download", "minta", "dapatkan", "file", "dokumen", "pdf", "unduh", "buku", "pedoman", "sop", "jadwal", "kalender"]
    
    # Cek kecocokan pemicu dasar
    is_request = any(t in query_lower for t in triggers)
    if not is_request:
        return None
        
    if not os.path.exists(documents_dir):
        return None
        
    files = [f for f in os.listdir(documents_dir) if f.endswith(".pdf") or f.endswith(".md")]
    if not files:
        return None
        
    # 2. Algoritma Pencocokan Cerdas (Fuzzy Overlap Matcher)
    best_match = None
    highest_score = 0.0
    
    for filename in files:
        # Normalisasi nama berkas ("pedoman_skripsi.pdf" -> "pedoman skripsi")
        clean_name = filename.lower().replace(".pdf", "").replace(".md", "").replace("_", " ").replace("-", " ")
        
        # Pola A: Kecocokan Persis (Sub-string)
        if clean_name in query_lower:
            return {
                "filename": filename,
                "path": os.path.abspath(os.path.join(documents_dir, filename)),
                "status": "found"
            }
            
        # Pola B: Bobot Kecocokan Kosakata (Token Intersection Ratio)
        words_query = set(query_lower.split())
        words_file = set(clean_name.split())
        
        # Hilangkan stopwords kecil
        stopwords = {"saya", "tolong", "ingin", "minta", "kirim", "file", "dokumen", "dong", "sih", "pdf"}
        words_query = words_query - stopwords
        words_file = words_file - stopwords
        
        intersection = words_query.intersection(words_file)
        if intersection and len(words_file) > 0:
            score = len(intersection) / len(words_file)
            if score > highest_score:
                highest_score = score
                best_match = filename
                
    # Threshold kemiripan kata kunci (40% kecocokan kosakata yang bersih)
    if best_match and highest_score >= 0.4:
        return {
            "filename": best_match,
            "path": os.path.abspath(os.path.join(documents_dir, best_match)),
            "status": "found"
        }
        
    # 3. Intersepsi Permintaan Berkas Tapi Berkas Tidak Ditemukan
    # Memberikan daftar berkas akademik yang tersedia secara interaktif
    unduh_keywords = ["kirim", "download", "minta", "dapatkan", "unduh", "file"]
    if any(k in query_lower for k in unduh_keywords):
        return {
            "filename": None,
            "status": "not_found",
            "available_files": files
        }
        
    return None

class RAGService:
    def __init__(self):
        """
        Menginisialisasi seluruh jalur RAG (PDF Loader, Chunker, Embeddings, ChromaDB, dan LLM).
        """
        self.documents_dir = os.path.abspath("documents")
        self.vectordb_dir = os.path.abspath("vectordb")
        
        # Pastikan direktori folder lokal ada
        os.makedirs(self.documents_dir, exist_ok=True)
        os.makedirs(self.vectordb_dir, exist_ok=True)
        
        # Memuat model embedding & inisialisasi pencarian ChromaDB
        self.embedding_model = get_embedding_model()
        self.retrieval_service = RetrievalService(self.vectordb_dir, self.embedding_model)
        
        # Memuat layanan LLM
        self.llm_service = LLMService()

    def index_documents(self) -> Dict[str, Any]:
        """
        Menjalankan full pipeline pemrosesan dokumen:
        PDF Loading -> Table Preprocessing -> Chunking -> Vector Storage.
        """
        print_info("Memulai pemrosesan pipeline dokumen (Indexing)...")
        
        # 1. Ekstraksi PDF & Preprocessing Tabel
        documents = load_documents(self.documents_dir)
        if not documents:
            self.retrieval_service.delete_collection()
            return {
                "status": "success",
                "message": f"Folder dokumen kosong. Database vektor telah dibersihkan.",
                "document_count": 0,
                "chunk_count": 0
            }
            
        # 2. Pemecahan Dokumen Menjadi Chunk Semantis
        chunks = split_documents(documents, chunk_size=500, chunk_overlap=100)
        print_info(f"Dokumen dipecah secara rekursif menjadi {len(chunks)} chunk.")
        
        # 3. Pembersihan Koleksi Database Vektor Lama
        self.retrieval_service.delete_collection()
        
        # Inisialisasi ulang ChromaDB baru untuk koleksi bersih
        self.retrieval_service = RetrievalService(self.vectordb_dir, self.embedding_model)
        
        # 4. Ingest Vektor ke Database Vektor
        texts = [c["content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        
        print_info(f"Memasukkan {len(chunks)} vektor ke ChromaDB...")
        try:
            self.retrieval_service.vector_store.add_texts(
                texts=texts,
                metadatas=metadatas,
                ids=ids
            )
            # Simpan secara permanen ke disk
            self.retrieval_service.vector_store.persist()
            print_success("Database vektor berhasil diperbarui!")
            
            return {
                "status": "success",
                "message": f"Berhasil mengindeks {len(documents)} halaman dokumen akademik menjadi {len(chunks)} chunk di database vektor.",
                "document_count": len(documents),
                "chunk_count": len(chunks)
            }
        except Exception as e:
            error_msg = f"Gagal menyimpan data ke database vektor: {str(e)}"
            print_error(error_msg)
            return {
                "status": "error",
                "message": error_msg
            }

    def query(self, user_query: str, chat_history=None) -> Dict[str, Any]:
        """
        Fungsi utama interaksi mahasiswa.
        Menggabungkan Deteksi Permintaan File, Pencarian Kemiripan Semantik, dan Jawaban AI LLM.
        Mendukung riwayat percakapan (chat_history) untuk konteks yang lebih natural.
        """
        # A. DETEKSI INTENT PERMINTAAN DOKUMEN
        doc_request = detect_document_request(user_query, self.documents_dir)
        
        if doc_request:
            if doc_request["status"] == "found":
                filename = doc_request["filename"]
                return {
                    "type": "document_request",
                    "status": "found",
                    "filename": filename,
                    "path": doc_request["path"],
                    "answer": f"Dokumen resmi **{filename}** berhasil ditemukan di server akademik.",
                    "sources": []
                }
            elif doc_request["status"] == "not_found":
                available_list = "\n".join([f" - {f}" for f in doc_request["available_files"]])
                return {
                    "type": "document_request",
                    "status": "not_found",
                    "answer": (
                        "Maaf, berkas akademik yang Anda minta tidak ditemukan.\n"
                        "Berikut adalah berkas PDF resmi kampus yang tersedia dan dapat Anda minta:\n"
                        f"{available_list}"
                    ),
                    "sources": []
                }

        # B. ALUR RAG STANDAR (Pencarian Semantik & LLM)
        # 1. Cari top-K chunk yang paling mirip semantiknya
        from app.database import get_setting
        top_k = int(get_setting("top_k", "4"))
        retrieved_chunks = self.retrieval_service.search_similar(user_query, k=top_k)
        
        # Validasi database kosong
        if self.retrieval_service.get_collection_size() == 0:
            return {
                "type": "rag_query",
                "answer": (
                    "Halo Kak! Selamat datang di layanan informasi Politeknik Indonusa Surakarta.\n\n"
                    "Mohon maaf sekali ya Kak, saat ini database informasi kampus di server kami masih kosong. "
                    "Sebagai langkah awal, silakan jalankan perintah 'index' terlebih dahulu di terminal "
                    "agar saya bisa memproses berkas PDF akademik dan membantu menjawab pertanyaan Kakak dengan maksimal ya!"
                ),
                "sources": []
            }
            
        # 2. Panggil LLM dengan Konteks yang relevan
        llm_response = self.llm_service.generate_answer(user_query, retrieved_chunks, chat_history=chat_history)
        
        return {
            "type": "rag_query",
            "answer": llm_response["answer"],
            "sources": llm_response["sources"],
            "retrieved_chunks": retrieved_chunks
        }
