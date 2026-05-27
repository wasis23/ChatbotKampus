from typing import List, Dict, Any
from app.utils import print_info

# Dukungan Impor Dinamis untuk Kompatibilitas Versi LangChain
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        # Kelas Fallback jika pustaka LangChain bermasalah / belum terinstal
        class RecursiveCharacterTextSplitter:
            def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100, separators: List[str] = None):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap
                
            def split_text(self, text: str) -> List[str]:
                """Sistem pemisah karakter sederhana berbasis sliding window sebagai cadangan."""
                chunks = []
                if not text:
                    return chunks
                    
                start = 0
                text_len = len(text)
                
                while start < text_len:
                    end = min(start + self.chunk_size, text_len)
                    
                    # Mencoba memotong pada spasi agar kata tidak terpotong di tengah jika memungkinkan
                    if end < text_len:
                        # Cari spasi terdekat ke belakang (maksimal 20 karakter)
                        last_space = text.rfind(" ", end - 20, end)
                        if last_space != -1:
                            end = last_space
                            
                    chunks.append(text[start:end].strip())
                    
                    # Hitung posisi start berikutnya dikurangi overlap
                    start = end - self.chunk_overlap
                    if start >= end: # Mencegah perulangan tak terbatas jika overlap terlalu besar
                        start = end
                        
                return [c for c in chunks if c]

def split_documents(documents: List[Dict[str, Any]], chunk_size: int = 500, chunk_overlap: int = 100) -> List[Dict[str, Any]]:
    """
    Memecah dokumen-dokumen akademik menjadi potongan chunk yang lebih kecil dengan overlap.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = []
    
    for doc in documents:
        text = doc["content"]
        meta = doc["metadata"]
        
        split_texts = splitter.split_text(text)
        
        for idx, chunk_text in enumerate(split_texts):
            # Salin metadata asli dan tambahkan indeks chunk untuk pelacakan yudisium/thesis
            chunk_meta = meta.copy()
            chunk_meta["chunk_index"] = idx
            
            chunks.append({
                "content": chunk_text,
                "metadata": chunk_meta
            })
            
    return chunks
