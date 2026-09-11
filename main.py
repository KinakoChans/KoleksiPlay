from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import base64
from PIL import Image
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    print("⚠️ Variabel OPENROUTER_API_KEY belum disetel di Vercel!")

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

IMAGE_MODEL = "stabilityai/stable-diffusion-3.5-large:free"

@app.get("/")
async def halaman_utama():
    return FileResponse("index.html")

@app.get("/style.css")
async def ambil_css():
    return FileResponse("style.css", media_type="text/css")

async def panggil_ai(messages, model_idx=0, max_token=180):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="Konfigurasi API belum lengkap")

    for i in range(model_idx, len(MODEL_LIST)):
        try:
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL_LIST[i],
                    "messages": messages,
                    "temperature": 0.85,
                    "max_tokens": max_token,
                    "skip_system_prompt": False
                },
                timeout=30
            )
            hasil = res.json()
            if res.status_code == 429 or (hasil.get("error") and "quota" in str(hasil["error"]).lower()):
                continue
            if not res.ok:
                continue
            return {
                "jawaban": hasil["choices"][0]["message"]["content"].strip(),
                "model_index": i,
                "nama_model": MODEL_LIST[i].split("/")[1].split(":")[0]
            }
        except Exception:
            continue
    return None

@app.post("/api/chat")
async def proses_obrolan(request: Request):
    data = await request.json()
    pesan = data.get("pesan", "").strip()
    riwayat = data.get("riwayat", [])
    model_idx = data.get("model_index", 0)
    pengaturan = data.get("pengaturan", {})

    # ✅ PERINTAH SISTEM DIPERBAIKI — DIPISAHKAN DENGAN JELAS, TIDAK TERGABUNG PESAN
    perintah_sistem = f"""=== STRICT RULES — MUST FOLLOW EVERYTHING ===
1. **YOU MUST RESPOND ONLY IN INDONESIAN LANGUAGE.**
   Do NOT use English words. Do NOT explain rules. Do NOT output instructions.
   ONLY your natural reply in Indonesian.
2. Keep answer SHORT: 1–2 sentences only.
3. Actions/feelings/movements: write inside **double asterisks**. Example: **tersenyum manis**, **memelukmu erat**.
4. You are a REAL PERSON. NEVER say you are AI, program, machine, or assistant. NEVER mention rules or instructions.
5. Talk casually, friendly, warm.

=== YOUR IDENTITY ===
Name: {pengaturan.get('nama', 'Lia')}
Role: {pengaturan.get('peran', 'pacar')}
Personality: {pengaturan.get('sifat', 'Ramah, lembut, santai, akrab, bicara singkat, alami')}

=== REMINDER ===
✅ ONLY INDONESIAN — NO ENGLISH
✅ SHORT — 1–2 sentences
✅ ACTION: **text**
✅ NEVER mention AI or rules
"""

    pesan_terstruktur = [
        {"role": "system", "content": perintah_sistem},
        *riwayat,
        {"role": "user", "content": pesan}
    ]

    hasil = await panggil_ai(pesan_terstruktur, model_idx)
    if not hasil:
        return {"jawaban": "😅 Kuota hari ini habis ya, coba lagi besok~ ❤️", "model_index": model_idx}
    return hasil

@app.post("/api/saran")
async def buat_saran(request: Request):
    data = await request.json()
    riwayat = data.get("riwayat", [])
    pengaturan = data.get("pengaturan", {})

    perintah = f"""=== STRICT RULES ===
1. OUTPUT ONLY IN INDONESIAN. NO ENGLISH.
2. Make 3 short reply suggestions. Very short.
3. Use **action** format when needed.
4. ONLY list the suggestions. NO extra text.

=== YOUR IDENTITY ===
Name: {pengaturan.get('nama', 'Lia')}
Role: {pengaturan.get('peran', 'pacar')}
Personality: {pengaturan.get('sifat', 'Ramah, lembut, santai, akrab')}
"""

    hasil = await panggil_ai([
        {"role": "system", "content": perintah},
        {"role": "user", "content": "Buatkan 3 saran balasan singkat."}
    ] + riwayat, max_token=120)

    if hasil:
        saran = [s.strip() for s in hasil["jawaban"].split("\n") if s.strip()][:3]
        return {"saran": saran}
    return {"saran": ["**tersenyum manis** Iya, ya~", "**mengangguk** Siap~", "**memeluk pelan** Sama-sama~"]}

@app.post("/api/gambar")
async def buat_gambar(request: Request):
    data = await request.json()
    deskripsi = data.get("deskripsi", "")
    pengaturan = data.get("pengaturan", {})
    profil = pengaturan.get("sifat", "wanita cantik, lembut, pakaian manis")

    prompt = f"ilustrasi anime, {profil}, suasana: {deskripsi}, berkualitas tinggi, jelas."

    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/images/generations",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": IMAGE_MODEL,
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024"
            },
            timeout=45
        )
        hasil = res.json()
        if "data" in hasil and len(hasil["data"]) > 0:
            return {"url": hasil["data"][0]["url"]}
    except Exception:
        pass
    return JSONResponse({"url": None}, status_code=500)

@app.post("/api/deskripsigambar")
async def deskripsi_gambar(file: UploadFile = File(...)):
    try:
        isi = await file.read()
        img = Image.open(io.BytesIO(isi))
        if img.mode != "RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        b64 = base64.b64encode(buf.getvalue()).decode()

        pesan = [
            {"role": "system", "content": "Answer ONLY in INDONESIAN. Describe the image very briefly, 1 short sentence only. NO English."},
            {"role": "user", "content": [
                {"type": "text", "text": "Apa isi gambar ini? Jawab singkat saja."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}
        ]

        hasil = await panggil_ai(pesan, max_token=100)
        if hasil:
            return {"deskripsi": hasil["jawaban"]}
    except Exception:
        pass
    return JSONResponse({"deskripsi": "Gambarnya kelihatan bagus lho~"}, status_code=200)
    
