import os
from typing import List
from app.utils import print_info, print_warning

# Impor Dinamis untuk Penanganan Kesalahan Ketergantungan
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings  # type: ignore
except ImportError:
    try:
        from langchain.embeddings import HuggingFaceEmbeddings  # type: ignore
    except ImportError:
        # Pengecualian jika paket langchain-community tidak terinstal
        HuggingFaceEmbeddings = None

if HuggingFaceEmbeddings is not None:
    class E5HuggingFaceEmbeddings:
        """Wrapper berbasis Composition untuk menghindari Linter Error pada Teks Editor"""
        def __init__(self, **kwargs):
            self._model = HuggingFaceEmbeddings(**kwargs)
            
        def embed_documents(self, texts: List[str]) -> List[List[float]]:
            prefixed_texts = [f"passage: {text}" for text in texts]
            return self._model.embed_documents(prefixed_texts)
            
        def embed_query(self, text: str) -> List[float]:
            prefixed_text = f"query: {text}"
            return self._model.embed_query(prefixed_text)
else:
    E5HuggingFaceEmbeddings = None

def get_embedding_model():
    """
    Menginisialisasi dan mengembalikan model embedding Sentence Transformers.
    Membaca nama model secara dinamis dari file .env (default: intfloat/multilingual-e5-small).
    """
    model_name = os.getenv(
        "EMBEDDING_MODEL_NAME", 
        "intfloat/multilingual-e5-small"
    )
    
    if E5HuggingFaceEmbeddings is None:
        print_warning("Pustaka 'langchain-community' tidak terdeteksi untuk HuggingFaceEmbeddings.")
        print_warning("Sistem akan berjalan dengan model tiruan atau silakan instal dependensi dengan: pip install langchain-community sentence-transformers")
        # Fallback dummy class untuk menghindari crash aplikasi saat pengujian awal
        class DummyEmbeddings:
            def embed_documents(self, texts):
                # Kembalikan vektor nol untuk tes tiruan
                return [[0.0] * 384 for _ in texts]
            def embed_query(self, text):
                return [0.0] * 384
        return DummyEmbeddings()
        
    print_info(f"Memuat model embedding E5: {model_name}...")
    try:
        # Inisialisasi model (mengunduh otomatis jika belum ada di lokal, kemudian berjalan offline)
        embeddings = E5HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},  # Jalankan di CPU untuk kompatibilitas universal
            encode_kwargs={'normalize_embeddings': True}  # Normalisasi kosinus
        )
        print_info("Model embedding berhasil dimuat!")
        return embeddings
    except Exception as e:
        print_warning(f"Gagal memuat model embedding {model_name}: {str(e)}")
        print_warning("Menggunakan model alternatif lokal...")
        # Jika gagal (misal koneksi internet bermasalah), coba gunakan versi yang lebih kecil
        try:
            fallback_model = "intfloat/multilingual-e5-small"
            print_info(f"Mencoba memuat model alternatif: {fallback_model}...")
            embeddings = E5HuggingFaceEmbeddings(
                model_name=fallback_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print_info("Model alternatif berhasil dimuat!")
            return embeddings
        except Exception as ex:
            print_warning(f"Gagal memuat model alternatif: {str(ex)}")
            raise ex
