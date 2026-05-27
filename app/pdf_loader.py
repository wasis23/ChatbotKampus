import os
import re
import pdfplumber
from typing import List, Dict, Any
from app.table_processor import process_tables_in_page
from app.utils import print_info, print_warning

def clean_extracted_text(text: str) -> str:
    """
    Membersihkan teks hasil ekstraksi dari karakter aneh,
    menghilangkan spasi ganda, dan merapikan perpindahan baris.
    """
    if not text:
        return ""
    
    # 1. Bersihkan karakter kontrol non-printable kecuali newline dan tab
    text = re.sub(r'[^\x20-\x7E\n\t]', '', text)
    
    # 2. Rapikan spasi berlebih
    text = re.sub(r'[ \t]+', ' ', text)
    
    # 3. Hilangkan baris-baris kosong yang berturut-turut lebih dari dua kali
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def load_pdf_documents(documents_dir: str) -> List[Dict[str, Any]]:
    """
    Membaca semua file PDF di direktori documents_dir, melakukan ekstraksi teks 
    dan tabel secara hibrida, lalu mengembalikan daftar dokumen terstruktur.
    """
    documents = []
    
    if not os.path.exists(documents_dir):
        print_warning(f"Direktori dokumen '{documents_dir}' tidak ditemukan. Membuat folder baru...")
        os.makedirs(documents_dir, exist_ok=True)
        return documents
        
    pdf_files = [f for f in os.listdir(documents_dir) if f.endswith(".pdf")]
    
    if not pdf_files:
        print_warning(f"Tidak ada berkas PDF ditemukan di folder '{documents_dir}'.")
        return documents
        
    for filename in pdf_files:
        pdf_path = os.path.join(documents_dir, filename)
        # Bentuk nama kategori yang ramah dari nama file (misal "pedoman_skripsi.pdf" -> "Pedoman Skripsi")
        category = filename.replace(".pdf", "").replace("_", " ").title()
        
        print_info(f"Mengekstrak berkas PDF: {filename}...")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_idx, page in enumerate(pdf.pages, 1):
                    # A. Ekstraksi Tabel & Konversi ke Narasi
                    tables = page.extract_tables()
                    table_narrative = ""
                    if tables:
                        table_narrative = process_tables_in_page(tables, filename)
                    
                    # B. Ekstraksi Teks Halaman Standard
                    page_text = page.extract_text() or ""
                    
                    # C. Penggabungan Teks & Tabel
                    full_content = page_text
                    if table_narrative:
                        # Sisipkan hasil narasi tabel di bagian akhir konten halaman
                        full_content += "\n\n" + table_narrative
                        
                    cleaned_content = clean_extracted_text(full_content)
                    
                    if cleaned_content:
                        documents.append({
                            "content": cleaned_content,
                            "metadata": {
                                "source": filename,
                                "category": category,
                                "page": page_idx
                            }
                        })
                        
        except Exception as e:
            print_warning(f"Terjadi kesalahan saat membaca {filename} (Halaman {page_idx if 'page_idx' in locals() else 'awal'}): {str(e)}")
            continue
            
    print_info(f"Selesai! Berhasil memuat total {len(documents)} halaman dari {len(pdf_files)} berkas PDF.")
    return documents
