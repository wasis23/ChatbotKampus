import os
import sys

def check_reportlab():
    try:
        import reportlab
    except ImportError:
        print("[EROR] Pustaka 'reportlab' belum terinstal.")
        print("Silakan jalankan perintah berikut terlebih dahulu:")
        print("  pip install reportlab")
        sys.exit(1)

check_reportlab()

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_pdf(filename, title, content_list, is_table=False, table_data=None):
    os.makedirs("documents", exist_ok=True)
    filepath = os.path.join("documents", filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=15
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#0D9488'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#374151'),
        spaceAfter=8
    )
    
    story = []
    
    # Add Title
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))
    
    # Add Content Elements
    for item in content_list:
        text_type, text_content = item
        if text_type == 'h1':
            story.append(Paragraph(text_content, h1_style))
        elif text_type == 'p':
            story.append(Paragraph(text_content, body_style))
        elif text_type == 'spacer':
            story.append(Spacer(1, text_content))
            
    # Add Table if requested
    if is_table and table_data:
        # Build Flowable Table
        formatted_table_data = []
        for r_idx, row in enumerate(table_data):
            formatted_row = []
            for c_idx, cell in enumerate(row):
                # Header vs Body styling
                if r_idx == 0:
                    formatted_row.append(Paragraph(f"<b>{cell}</b>", ParagraphStyle('TH', parent=body_style, textColor=colors.white, fontName='Helvetica-Bold')))
                else:
                    formatted_row.append(Paragraph(cell, body_style))
            formatted_table_data.append(formatted_row)
            
        t = Table(formatted_table_data, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('BOTTOMPADDING', (0,1), (-1,-1), 5),
            ('TOPPADDING', (0,1), (-1,-1), 5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#F8FAFC'), colors.white])
        ]))
        story.append(t)
        
    doc.build(story)
    print(f"[SUKSES] Berhasil membuat dokumen: {filepath}")

def generate_all():
    print("Memulai pembuatan dokumen akademik sampel...")
    
    # 1. Pedoman Akademik
    pedoman_content = [
        ('h1', 'BAB I: ATURAN UMUM AKADEMIK'),
        ('p', 'Setiap mahasiswa aktif Universitas Karya Bangsa wajib mendaftarkan diri secara administratif pada awal semester. Beban studi yang dapat diambil oleh mahasiswa berkisar antara 12 hingga 24 SKS per semester, disesuaikan dengan Indeks Prestasi Kumulatif (IPK) yang diperoleh pada semester sebelumnya.'),
        ('p', 'Untuk menyelesaikan program sarjana (S1), seorang mahasiswa diwajibkan menyelesaikan beban studi minimal sebanyak 144 SKS, termasuk di dalamnya skripsi/tugas akhir dan mata kuliah wajib nasional/universitas.'),
        ('h1', 'BAB II: PREDIKAT KELULUSAN (YUDISIUM)'),
        ('p', 'Predikat kelulusan yudisium program sarjana Universitas Karya Bangsa ditetapkan sebagai berikut:'),
        ('p', '1. IPK 3.51 - 4.00: Lulus dengan Predikat Pujian (Cum Laude), dengan ketentuan masa studi tidak melebihi 4 tahun (8 semester) dan tidak memiliki nilai mata kuliah di bawah C.'),
        ('p', '2. IPK 3.01 - 3.50: Lulus dengan Predikat Sangat Memuaskan.'),
        ('p', '3. IPK 2.76 - 3.00: Lulus dengan Predikat Memuaskan.'),
        ('p', 'Setiap lulusan berhak menerima Ijazah, Transkrip Akademik, dan Surat Keterangan Pendamping Ijazah (SKPI) setelah dinyatakan lulus yudisium.')
    ]
    create_pdf('pedoman_akademik.pdf', 'BUKU PEDOMAN AKADEMIK MAHASISWA', pedoman_content)
    
    # 2. Kalender Akademik
    kalender_content = [
        ('h1', 'KALENDER AKADEMIK SEMESTER GENAP 2025/2026'),
        ('p', 'Berikut adalah kalender akademik resmi untuk Semester Genap Tahun Ajaran 2025/2026 bagi seluruh program sarjana (S1):'),
        ('p', '• Registrasi Administrasi & Pembayaran UKT: 2 - 13 Februari 2026'),
        ('p', '• Pengisian Kartu Rencana Studi (KRS): 16 - 20 Februari 2026'),
        ('p', '• Awal Perkuliahan Semester Genap: 2 Maret 2026'),
        ('p', '• Ujian Tengah Semester (UTS): 6 - 17 April 2026'),
        ('p', '• Ujian Akhir Semester (UAS): 15 - 26 Juni 2026'),
        ('p', '• Pelaksanaan Yudisium Akhir Semester: 10 Juli 2026'),
        ('p', '• Libur Semester Genap: 29 Juni - 28 Agustus 2026'),
        ('p', 'Mahasiswa diwajibkan memperhatikan tanggal-tanggal penting di atas. Keterlambatan registrasi atau pengisian KRS dapat berakibat pada status non-aktif pada semester berjalan.')
    ]
    create_pdf('kalender_akademik.pdf', 'KALENDER AKADEMIK KAMPUS', kalender_content)
    
    # 3. Jadwal Kuliah (Tabel)
    jadwal_content = [
        ('h1', 'JADWAL KULIAH PRODI S1 TEKNIK INFORMATIKA'),
        ('p', 'Jadwal pelaksanaan kuliah tatap muka dan praktikum Program Studi S1 Teknik Informatika untuk Semester Ganjil/Genap disajikan dalam tabel di bawah ini. Kelas perkuliahan menggunakan zona waktu Barat (WIB).'),
        ('spacer', 10)
    ]
    jadwal_table = [
        ['Hari', 'Mata Kuliah', 'Jam', 'Ruang', 'Dosen'],
        ['Senin', 'Basis Data', '08.00 - 10.30', 'Lab Komputer 2', 'Dr. Hermawan'],
        ['Selasa', 'Pemrograman Web', '10.45 - 13.15', 'Ruang 401', 'Prof. Budi'],
        ['Rabu', 'Kecerdasan Buatan', '13.30 - 16.00', 'Ruang 302', 'Dr. Kartika'],
        ['Kamis', 'Grafika Komputer', '08.00 - 10.30', 'Lab Komputer 1', 'Ir. Diana, M.T.']
    ]
    create_pdf('jadwal_kuliah.pdf', 'JADWAL PERKULIAHAN KAMPUS', jadwal_content, is_table=True, table_data=jadwal_table)
    
    # 4. Informasi UKT (Tabel)
    ukt_content = [
        ('h1', 'TARIF UANG KULIAH TUNGGAL (UKT) PROGRAM SARJANA (S1)'),
        ('p', 'Uang Kuliah Tunggal (UKT) wajib dibayarkan oleh mahasiswa aktif di setiap awal semester berjalan. Besaran tarif UKT disesuaikan dengan golongan kemampuan ekonomi mahasiswa berdasarkan keputusan universitas.'),
        ('spacer', 10)
    ]
    ukt_table = [
        ['Program Studi', 'Golongan I', 'Golongan II', 'Golongan III', 'Golongan IV'],
        ['Teknik Informatika', 'Rp 500.000', 'Rp 2.500.000', 'Rp 4.500.000', 'Rp 6.000.000'],
        ['Sistem Informasi', 'Rp 500.000', 'Rp 2.200.000', 'Rp 4.000.000', 'Rp 5.500.000'],
        ['Teknik Elektro', 'Rp 500.000', 'Rp 2.400.000', 'Rp 4.200.000', 'Rp 5.800.000']
    ]
    create_pdf('informasi_ukt.pdf', 'INFORMASI BIAYA KULIAH (UKT)', ukt_content, is_table=True, table_data=ukt_table)
    
    # 5. Pedoman Skripsi
    skripsi_content = [
        ('h1', 'PERSYARATAN AKADEMIK PENGAJUAN SKRIPSI'),
        ('p', 'Setiap mahasiswa Universitas Karya Bangsa wajib memenuhi syarat-syarat berikut untuk mengajukan judul skripsi atau Tugas Akhir:'),
        ('p', '1. Telah menyelesaikan minimal 144 SKS beban mata kuliah.'),
        ('p', '2. Memiliki Indeks Prestasi Kumulatif (IPK) minimal sebesar 2.00.'),
        ('p', '3. Tidak memiliki tunggakan biaya Uang Kuliah Tunggal (UKT) di semester berjalan.'),
        ('p', '4. Lulus seluruh mata kuliah wajib universitas dan prodi dengan nilai minimal C (tidak boleh ada nilai D atau E pada mata kuliah wajib).'),
        ('h1', 'ALUR DAN TAHAPAN PENYUSUNAN SKRIPSI'),
        ('p', 'Mahasiswa yang memenuhi syarat mengajukan proposal penelitian kepada Ketua Program Studi. Setelah proposal disetujui, Ketua Prodi menunjuk dua dosen pembimbing (Dosen Pembimbing I dan Dosen Pembimbing II) untuk mengarahkan proses penyusunan skripsi.'),
        ('p', 'Proses pembimbingan wajib dilakukan minimal sebanyak 8 kali pertemuan yang tercatat dalam kartu bimbingan. Setelah draf skripsi disetujui oleh kedua pembimbing, mahasiswa berhak mendaftarkan diri untuk mengikuti Sidang Tugas Akhir/Skripsi.')
    ]
    create_pdf('pedoman_skripsi.pdf', 'PEDOMAN SKRIPSI DAN TUGAS AKHIR', skripsi_content)
    
    # 6. SOP Administrasi
    sop_content = [
        ('h1', 'STANDAR OPERASIONAL PROSEDUR (SOP) CUTI AKADEMIK'),
        ('p', 'Cuti akademik adalah hak mahasiswa untuk dibebaskan dari kegiatan akademik selama maksimal 2 semester berturut-turut. Prosedurnya adalah:'),
        ('p', '1. Mahasiswa mengajukan surat permohonan cuti kepada Dekan Fakultas, dilampiri alasan pendukung yang sah (masalah kesehatan, pekerjaan, dll.).'),
        ('p', '2. Pengajuan cuti harus dilakukan paling lambat minggu ke-4 perkuliahan sejak semester baru dimulai.'),
        ('p', '3. Mahasiswa harus bebas dari segala tunggakan keuangan (UKT) semester sebelumnya dan membayar biaya administrasi cuti sebesar Rp 250.000.'),
        ('h1', 'SOP PENDAFTARAN SIDANG SKRIPSI'),
        ('p', 'Untuk mendaftar sidang skripsi, mahasiswa menyerahkan berkas ke bagian administrasi fakultas paling lambat 7 hari sebelum tanggal pelaksanaan sidang. Berkas pendaftaran meliputi naskah skripsi yang ditandatangani pembimbing, transkrip nilai, bukti pembayaran UKT, dan sertifikat TOEFL/keahlian pendukung.')
    ]
    create_pdf('sop_administrasi.pdf', 'SOP ADMINISTRASI KAMPUS', sop_content)
    
    print("\nSemua dokumen uji berhasil dibuat!")

if __name__ == "__main__":
    generate_all()
