# ChatbotKampus (ISA - Indonusa Smart Assistance) 🤖🎓

ISA (Indonusa Smart Assistance) adalah sistem chatbot cerdas berbasis **RAG (Retrieval-Augmented Generation)** dan **LLM (Large Language Model)** yang dirancang khusus untuk melayani kebutuhan informasi akademik, penerimaan mahasiswa baru (PMB), dan layanan kemahasiswaan di Politeknik Indonusa Surakarta.

## ✨ Fitur Utama
* **🧠 Context-Aware AI (RAG System)**: Menjawab pertanyaan berdasarkan dokumen resmi kampus yang ada di database (Knowledge Base) untuk meminimalisir halusinasi AI.
* **🌐 Embeddable Chat Widget**: Chatbot dapat diintegrasikan dengan mudah ke website kampus mana saja hanya dengan menambahkan script HTML/JS singkat.
* **🗂️ Knowledge Base Management**: Dilengkapi dengan halaman Admin untuk mengelola, menambah, dan menghapus dokumen referensi yang menjadi "otak" chatbot.
* **🔐 Admin Authentication**: Halaman panel admin diamankan dengan sistem otentikasi login.
* **💾 Conversational Memory**: Chatbot mampu mengingat konteks percakapan sebelumnya untuk memberikan pengalaman interaksi layaknya manusia.

## 🔄 Alur Sistem (System Architecture)
1. **Knowledge Ingestion**: Admin mengunggah dokumen (PDF/Teks) melalui panel Admin. Sistem akan memecah dokumen (Chunking) dan mengubahnya menjadi vektor (Embedding) untuk disimpan di Vector Database.
2. **User Query**: Pengguna/calon mahasiswa mengirimkan pertanyaan melalui Chat Widget di website.
3. **Retrieval**: Sistem mencari potongan informasi paling relevan dari VectorDB berdasarkan pertanyaan pengguna.
4. **Generation**: Sistem merangkai prompt (gabungan pertanyaan pengguna + konteks dokumen relevan) lalu mengirimkannya ke mesin LLM (OpenAI API).
5. **Response**: LLM menyajikan jawaban yang akurat, informatif, dan terstruktur kembali ke layar chat pengguna.

## 🛠️ Teknologi yang Digunakan
* **Backend**: Python (dengan framework API pendukung)
* **LLM / AI Engine**: OpenAI API
* **Vector Database**: VectorDB / Chroma
* **Frontend**: Vanilla HTML, CSS, JavaScript (untuk Widget dan Admin Panel)

## 🚀 Cara Instalasi & Menjalankan Project (Sisi Server)

### 1. Persiapan
Pastikan Anda memiliki Python 3.8+ terinstal.

### 2. Clone Repositori
```bash
git clone https://github.com/wasis23/ChatbotKampus.git
cd ChatbotKampus
```

### 3. Setup Virtual Environment
```bash
python -m venv venv

# Aktifkan di Windows:
venv\Scripts\activate
# Aktifkan di Linux/Mac:
source venv/bin/activate

# Install semua library yang dibutuhkan
pip install -r requirements.txt
```

### 4. Konfigurasi Environment (PENTING!)
Buat sebuah file baru bernama `.env` (tanpa nama depan, hanya ekstensi `.env`) di folder utama project, lalu isi dengan kunci API Anda:
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxx
```
*(Catatan: Jangan pernah membagikan atau meng-upload file `.env` ini)*

### 5. Menjalankan Server Aplikasi
Jalankan script utama Python atau file batch yang disediakan:
```bash
python app/main.py
# atau
run_server.bat
```
Aplikasi backend sudah aktif. Anda bisa mengakses halaman Admin Panel atau Test Widget melalui URL lokal yang disediakan di terminal (misal: `http://localhost:8000`).

---

## 📦 Cara Memasang Chatbot ke Website Lain (Frontend Integration)
Jika backend di atas sudah di-hosting dan berjalan di sebuah server online, Anda dapat memunculkan Chatbot ini di website berbasis HTML/PHP/WordPress manapun tanpa perlu clone project lagi.

Cukup salin dan tempel (copy-paste) kode pemanggil berikut di dalam HTML website target (tepat sebelum penutup `</body>`):
```html
<!-- Import CSS Chatbot -->
<link rel="stylesheet" href="https://domain-server-anda.com/static/isa-widget.css">

<!-- Import JS Chatbot -->
<script src="https://domain-server-anda.com/static/isa-widget.js"></script>
```
*(Ganti `https://domain-server-anda.com` dengan alamat IP atau Domain tempat Anda meng-hosting aplikasi Python ini).*

---
*Dikembangkan untuk mempermudah layanan informasi sivitas akademika Politeknik Indonusa Surakarta.*
