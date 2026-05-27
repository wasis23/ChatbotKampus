import os
import sys
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Pastikan folder app dapat diimpor
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.rag_service import RAGService
from app.utils import print_header, print_success, print_info, print_warning, BOLD, RESET, CYAN, GREEN, YELLOW

def test_semantic_search():
    print_header("UJI COBA PENCARIAN SEMANTIK - CHROMADB")
    
    try:
        rag = RAGService()
        print_success("Berhasil memuat database vektor!")
    except Exception as e:
        print_error(f"Gagal memuat RAGService: {str(e)}")
        sys.exit(1)
        
    queries = [
        # Pertanyaan untuk Teks Naratif
        "Apa saja syarat sidang skripsi?",
        "Berapa SKS minimum kelulusan sarjana?",
        # Pertanyaan untuk Tabel Preprocessed (UKT)
        "Berapa biaya UKT Golongan 3 untuk Teknik Informatika?",
        # Pertanyaan untuk Tabel Preprocessed (Jadwal)
        "Siapa dosen pengampu mata kuliah Kecerdasan Buatan dan di ruang mana?"
    ]
    
    for idx, query in enumerate(queries, 1):
        print(f"\n{BOLD}{YELLOW}Kueri Uji #{idx}:{RESET} \"{query}\"")
        print(f"{CYAN}{'-'*70}{RESET}")
        
        # Lakukan pencarian semantik (Top-k = 3 untuk verifikasi)
        results = rag.retrieval_service.search_similar(query, k=3)
        
        if not results:
            print_warning("Tidak ada dokumen relevan yang ditemukan. Pastikan database sudah terindeks.")
            continue
            
        for c_idx, res in enumerate(results, 1):
            source = res['metadata'].get('source', 'Tidak diketahui')
            page = res['metadata'].get('page', '-')
            confidence = res.get('confidence', 0.0)
            
            print(f" {BOLD}[Hasil {c_idx}]{RESET} Sumber: {source} | Hal: {page} | Confidence: {confidence:.2f}%")
            # Cetak potongan teks dengan indentasi
            content_indented = "\n".join([f"    {line}" for line in res['content'].split('\n')[:5]])
            print(f"{content_indented}")
            if len(res['content'].split('\n')) > 5:
                print("    ...")
            print()
            
if __name__ == "__main__":
    test_semantic_search()
