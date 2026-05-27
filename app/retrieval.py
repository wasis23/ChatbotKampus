import os
from typing import List, Dict, Any
from app.utils import print_info, print_warning

# Dukungan Impor Dinamis untuk Kompatibilitas Versi LangChain
try:
    from langchain_community.vectorstores import Chroma
except ImportError:
    try:
        from langchain.vectorstores import Chroma
    except ImportError:
        Chroma = None

class RetrievalService:
    def __init__(self, persist_directory: str, embedding_model: Any):
        """
        Menginisialisasi layanan pencarian database vektor (ChromaDB).
        Menggunakan metrik kemiripan Cosine secara eksplisit.
        """
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.collection_name = "chatbot_akademik_rag"
        self.vector_store = None
        
        if Chroma is None:
            print_warning("Pustaka 'langchain-community' (Chroma) tidak terdeteksi.")
            return
            
        try:
            # Menginisialisasi Chroma dengan HNSW ruang kosinus (Cosine Similarity)
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_model,
                persist_directory=self.persist_directory,
                collection_metadata={"hnsw:space": "cosine"} # Menetapkan metrik ke Cosine
            )
        except Exception as e:
            print_warning(f"Gagal memuat database vektor ChromaDB: {str(e)}")

    def search_similar(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        Melakukan pencarian kemiripan semantik (semantic search) dan menghitung 
        nilai Confidence Score secara matematis berdasarkan jarak kosinus (Cosine Distance).
        """
        results = []
        if self.vector_store is None:
            print_warning("Vector store belum diinisialisasi.")
            return results
            
        try:
            # Menggunakan similarity_search_with_score untuk mendapatkan dokumen beserta jaraknya (distance)
            # Semakin kecil distance, semakin mirip dokumennya (dalam metrik cosine)
            docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
            
            for doc, distance in docs_with_scores:
                # KONVERSI MATEMATIS JARAK KOSINUS KE PERSENTASE CONFIDENCE
                # Jarak Kosinus (Cosine Distance) berkisar dari 0 (sangat mirip) hingga 2 (berlawanan)
                # Kemiripan Kosinus (Cosine Similarity) = 1.0 - Cosine Distance
                # Kami mengubahnya menjadi persentase keyakinan (0% - 100%)
                cosine_similarity = 1.0 - float(distance)
                
                # Normalisasi agar berada di rentang 0% - 100%
                confidence = cosine_similarity * 100.0
                confidence = max(0.0, min(100.0, confidence))
                
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "confidence": confidence
                })
                
        except Exception as e:
            print_warning(f"Kesalahan saat melakukan pencarian kemiripan semantik: {str(e)}")
            
        return results

    def get_collection_size(self) -> int:
        """Mengembalikan total jumlah chunk vektor yang tersimpan dalam database."""
        if self.vector_store is None:
            return 0
        try:
            # Mengakses collection Chroma asli secara internal
            collection = self.vector_store._collection
            if collection:
                return collection.count()
        except Exception:
            pass
        return 0

    def delete_collection(self) -> bool:
        """Menghapus koleksi vektor lama untuk memfasilitasi re-indexing yang bersih."""
        if self.vector_store is None:
            return False
        try:
            self.vector_store.delete_collection()
            print_info("Koleksi database vektor lama berhasil dibersihkan.")
            return True
        except Exception as e:
            print_warning(f"Gagal menghapus koleksi vektor: {str(e)}")
            return False
