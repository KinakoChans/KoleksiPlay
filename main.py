from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()

# Izinkan akses
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ambil kunci dari pengaturan Vercel yang sudah kamu isi
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("⚠️ Variabel OPENROUTER_API_KEY belum disetel di Vercel!")

# Daftar model urutan terbaik ke terendah
MODEL_LIST = [
    "google/gemma-4-31b-it:free",
    "minimax/minimax-m3:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-235b-a22b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "google/gemini-2.0-flash-exp:free",
    "z-ai/glm-4.5-air:free",
    "amazon/nova-2-lite-v1:free",
    "nousresearch/hermes-3-llama-3.1-405b:free"
]

# Tampilkan berkas statis
@app.get("/")
async def halaman_utama():
    return FileResponse("index.html")

@app.get("/style.css")
async def ambil_css():
    return FileResponse("style.css", media_type="text/css")

# Fungsi utama obrolan
@app.post("/api/chat")
async def proses_obrolan(request: Request):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="Konfigurasi API belum lengkap")

    data = await request.json()
    pesan = data.get("pesan", "").strip()
    if not pesan:
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong")

    riwayat = data.get("riwayat", [])
    indeks_awal = data.get("model_index", 0)
    nama_karakter = data.get("nama", "Lia")
    peran = data.get("peran", "pacar")
    sifat = data.get("sifat", "Ramah, lembut, suka bercanda, selalu perhatikan perasaanmu, bicara santai dan akrab")

    perintah_sistem = f"""Kamu adalah {nama_karakter}, seorang {peran}. Sifatmu: {sifat}.
PENTING: Jawab dengan gaya bicara alami, santai, akrab, pakai bahasa Indonesia sehari-hari. Jangan kaku, jangan terlalu panjang. Tetap konsisten watakmu. JANGAN PERNAH bilang kamu AI, program komputer, atau asisten."""

    for i in range(indeks_awal, len(MODEL_LIST)):
        model_terpilih = MODEL_LIST[i]
        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_terpilih,
                    "messages": [
                        {"role": "system", "content": perintah_sistem},
                        *riwayat,
                        {"role": "user", "content": pesan}
                    ],
                    "temperature": 0.85,
                    "max_tokens": 600
                },
                timeout=30
            )

            hasil_json = res.json()

            if res.status_code == 429 or (hasil_json.get("error") and 
               ("quota" in str(hasil_json["error"]).lower() or "exceeded" in str(hasil_json["error"]).lower())):
                continue

            if not res.ok:
                continue

            jawaban = hasil_json["choices"][0]["message"]["content"].strip()
            return {
                "jawaban": jawaban,
                "model_index": i,
                "nama_model": model_terpilih.split("/")[1].split(":")[0]
            }

        except Exception:
            continue

    return {
        "jawaban": "😅 Wah, semua batas pemakaian hari ini sudah habis. Coba lagi besok ya, nanti aku siap ngobrol lagi sama kamu! ❤️",
        "model_index": indeks_awal
    }
