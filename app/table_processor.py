import re
from typing import List, Dict, Any, Optional

def clean_cell_text(text: Any) -> str:
    """Membersihkan whitespace dan karakter baris baru di dalam sel tabel."""
    if text is None:
        return ""
    text_str = str(text).replace("\n", " ").strip()
    return re.sub(r'\s+', ' ', text_str)

def process_tables_in_page(tables: List[List[List[Any]]], doc_name: str) -> str:
    """
    Mengubah daftar tabel yang dideteksi pada halaman PDF menjadi kalimat naratif deskriptif (Table-to-Text).
    """
    if not tables:
        return ""
        
    narrative_results = []
    
    for table_idx, table in enumerate(tables, 1):
        if not table or len(table) < 2:
            continue
            
        # 1. Bersihkan dan ekstrasi header kolom (baris pertama)
        headers = [clean_cell_text(h) for h in table[0]]
        # Jika ada header kosong, beri nama default
        headers = [h if h else f"Kolom_{i+1}" for i, h in enumerate(headers)]
        
        rows = table[1:]
        table_narratives = []
        
        for r_idx, row in enumerate(rows):
            # Bersihkan isi setiap sel pada baris berjalan
            cells = [clean_cell_text(c) for c in row]
            
            # Sesuaikan panjang sel dengan panjang header jika tidak sama
            if len(cells) < len(headers):
                cells += [""] * (len(headers) - len(cells))
            elif len(cells) > len(headers):
                cells = cells[:len(headers)]
                
            # Buat kamus pemetaan (Header -> Nilai Sel)
            row_dict = dict(zip(headers, cells))
            
            # Cek kecocokan pola tabel secara semantis untuk membuat kalimat yang sangat natural
            
            # A. Pola Jadwal Kuliah (Hari, Jam/Waktu, Mata Kuliah)
            has_hari = any(re.search(r'\bhari\b', k.lower()) for k in row_dict.keys())
            has_matkul = any(re.search(r'\bmata\s*kuliah\b|\bmatkul\b', k.lower()) for k in row_dict.keys())
            has_jam = any(re.search(r'\bjam\b|\bwaktu\b', k.lower()) for k in row_dict.keys())
            
            # B. Pola UKT (Golongan, Tarif/UKT, Program Studi)
            has_prodi = any(re.search(r'\bprogram\s*studi\b|\bprodi\b|\bjurusan\b', k.lower()) for k in row_dict.keys())
            has_ukt = any(re.search(r'\bukt\b|\bgolongan\s*i\b|\btarif\b', k.lower()) for k in row_dict.keys())
            
            if has_hari and has_matkul:
                # Ambil nilai secara dinamis dari kunci yang cocok
                hari_val = next((v for k, v in row_dict.items() if re.search(r'\bhari\b', k.lower())), "")
                matkul_val = next((v for k, v in row_dict.items() if re.search(r'\bmata\s*kuliah\b|\bmatkul\b', k.lower())), "")
                jam_val = next((v for k, v in row_dict.items() if re.search(r'\bjam\b|\bwaktu\b', k.lower())), "")
                ruang_val = next((v for k, v in row_dict.items() if re.search(r'\bruang\b|\bruangan\b|\bkelas\b', k.lower())), "")
                dosen_val = next((v for k, v in row_dict.items() if re.search(r'\bdosen\b|\bpengajar\b', k.lower())), "")
                
                sentence = f"Berdasarkan jadwal perkuliahan, mata kuliah {matkul_val}"
                if dosen_val:
                    sentence += f" yang diampu oleh {dosen_val}"
                if hari_val:
                    sentence += f" dijadwalkan pada hari {hari_val}"
                if jam_val:
                    sentence += f" pukul {jam_val}"
                if ruang_val:
                    sentence += f" bertempat di {ruang_val}"
                sentence += "."
                table_narratives.append(sentence)
                
            elif has_prodi and has_ukt:
                prodi_val = next((v for k, v in row_dict.items() if re.search(r'\bprogram\s*studi\b|\bprodi\b|\bjurusan\b', k.lower())), "")
                
                # Mengumpulkan rincian golongan UKT
                ukt_details = []
                for header, cell in row_dict.items():
                    if header != prodi_val and any(g in header.lower() for g in ["golongan", "gol", "ukt"]):
                        ukt_details.append(f"{header} sebesar {cell}")
                
                sentence = f"Berdasarkan informasi tarif biaya kuliah (UKT) untuk Program Studi {prodi_val}: "
                if ukt_details:
                    sentence += ", ".join(ukt_details) + "."
                else:
                    # Fallback jika tidak ada deteksi kolom spesifik golongan
                    parts = [f"{k}: {v}" for k, v in row_dict.items() if v]
                    sentence += ", ".join(parts) + "."
                table_narratives.append(sentence)
                
            else:
                # C. Pola Umum (General Table-to-Text Fallback)
                # Menyusun kalimat umum dari sel yang tidak kosong
                parts = []
                for header, cell in row_dict.items():
                    if cell and cell.lower() != "nan" and cell != "-":
                        parts.append(f"{header} adalah '{cell}'")
                
                if parts:
                    sentence = f"Data tabel {doc_name} baris ke-{r_idx+1}: " + ", ".join(parts) + "."
                    table_narratives.append(sentence)
                    
        if table_narratives:
            narrative_results.append(
                f"[Tabel Preprocessing Ke-{table_idx} dari {doc_name}]\n" + 
                "\n".join(table_narratives)
            )
            
    return "\n\n".join(narrative_results)
