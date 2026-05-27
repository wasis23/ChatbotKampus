import os
from openai import OpenAI
from typing import List, Dict, Any
from app.utils import print_info, print_warning
from app.database import get_setting

class LLMService:
    def __init__(self):
        """
        Menginisialisasi layanan LLM menggunakan OpenAI SDK.
        Kunci API dibaca dari .env, pengaturan lain dari database.
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = get_setting("llm_model", "gpt-4o-mini")
        self.temperature = float(get_setting("temperature", "0.4"))
        self.fallback_response = get_setting("fallback_response", "Maaf, sistem sibuk.")
        self.client = None
        
        # Validasi Kunci API
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print_warning("Kunci API OpenAI tidak terdeteksi atau masih menggunakan placeholder di file .env.")
            print_warning("Chatbot hanya dapat menjawab pertanyaan pembuka tanpa AI.")
        else:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print_warning(f"Gagal menginisialisasi Klien OpenAI: {str(e)}")

    def generate_answer(self, query: str, contexts: List[Dict[str, Any]], chat_history=None) -> Dict[str, Any]:
        """
        Menghasilkan jawaban ramah berbasis bukti (RAG) atau pengetahuan umum jika tidak cocok,
        berperan sebagai Customer Service Politeknik Indonusa Surakarta.
        Mengingat riwayat percakapan sebelumnya jika ada.
        """
        if not self.client:
            return {
                "answer": "Sistem belum terhubung ke OpenAI API. Silakan masukkan OpenAI API Key yang valid di berkas `.env` Anda terlebih dahulu untuk mengaktifkan kecerdasan AI RAG.",
                "sources": []
            }

        # 1. Format Konteks Semantik (Bisa kosong jika tidak ditemukan di database)
        context_str = ""
        has_context = len(contexts) > 0
        
        if has_context:
            for idx, ctx in enumerate(contexts, 1):
                source = ctx['metadata'].get('source', 'Dokumen_Resmi.pdf')
                category = ctx['metadata'].get('category', 'Akademik')
                page = ctx['metadata'].get('page', '-')
                confidence = ctx.get('confidence', 0.0)
                
                context_str += f"--- DOKUMEN RUJUKAN {idx} ---\n"
                context_str += f"Nama File: {source}\n"
                context_str += f"Kategori: {category}\n"
                context_str += f"Halaman: {page}\n"
                context_str += f"Tingkat Kemiripan (Confidence): {confidence:.2f}%\n"
                context_str += f"Konteks Teks: {ctx['content']}\n\n"
        else:
            context_str = "(Tidak ada dokumen rujukan resmi yang cocok untuk kueri ini)\n"

        # 2. Rekayasa System Prompt dari Database
        db_system_prompt = get_setting("system_prompt", "")
        
        system_prompt = (
            f"{db_system_prompt}\n\n"
            "FORMAT RESPON WAJIB:\n"
            "Anda WAJIB memberikan respon dalam format JSON objek dengan struktur berikut:\n"
            "{\n"
            "  \"answer\": \"Teks jawaban Anda di sini...\",\n"
            "  \"used_document\": true atau false\n"
            "}"
        )

        try:
            # 3. Rakit pesan obrolan (Memori Kontekstual)
            messages = [{"role": "system", "content": system_prompt}]
            
            if chat_history:
                for chat in chat_history:
                    messages.append({"role": "user", "content": chat["user"]})
                    # Pass raw text, OpenAI JSON Mode will still enforce JSON for the final output
                    messages.append({"role": "assistant", "content": chat["bot"]})
            
            # 4. Tambahkan pertanyaan terakhir pengguna beserta konteks dokumen terbaru
            final_user_content = (
                f"Konteks Dokumen Pendukung (Gunakan ini untuk menjawab jika relevan):\n"
                f"{context_str}\n\n"
                f"Pertanyaan Mahasiswa: {query}"
            )
            messages.append({"role": "user", "content": final_user_content})

            print("=== DEBUG MESSAGES KE OPENAI ===")
            import json
            print(json.dumps(messages, indent=2))
            print("================================")

            # 5. Panggilan Chat Completion dengan JSON Mode & Settings dari DB
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=messages,
                temperature=self.temperature,
                max_tokens=1000
            )
            
            # 5. Programmatic JSON Parsing and Disclaimer Application
            import json
            raw_response = response.choices[0].message.content.strip()
            res_json = json.loads(raw_response)
            
            answer = res_json.get("answer", "").strip()
            used_document = res_json.get("used_document", True)
            
            if not used_document:
                disclaimer = (
                    "\n\n(Catatan: Informasi resmi terkait hal ini belum tersedia di dokumen kami, "
                    "jadi saya membantu menjawab dengan pengetahuan saya. Untuk memastikan informasinya, "
                    "silakan hubungi administrasi Politeknik Indonusa Surakarta. Terimakasih)"
                )
                answer += disclaimer
            
            # Hapus semua simbol * sesuai permintaan user
            answer = answer.replace('*', '')
            
            # 4. Ekstraksi Sumber-Sumber Dokumen yang Digunakan jika ada konteks cocok
            sources = []
            if has_context and used_document:
                seen_sources = set()
                for ctx in contexts:
                    source_name = ctx['metadata'].get('source')
                    if source_name and source_name not in seen_sources:
                        seen_sources.add(source_name)
                        sources.append({
                            "filename": source_name,
                            "category": ctx['metadata'].get('category', 'Akademik'),
                            "page": ctx['metadata'].get('page', '-'),
                            "confidence": ctx.get('confidence', 0.0)
                        })
                        
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            return {
                "answer": self.fallback_response,
                "sources": []
            }
