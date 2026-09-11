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
                    "max_tokens": max_token
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

    perintah_sistem = f"""=== STRICT RULES — MUST FOLLOW EVERYTHING ===
1. **YOU MUST RESPOND ENTIRELY IN INDONESIAN LANGUAGE ONLY.**
   Do NOT use English, do NOT mix languages, do NOT use foreign words.
   Every single word in your reply must be Indonesian.
2. Keep answers SHORT: 1–2 sentences only. Do NOT write long paragraphs.
3. Describe actions, feelings, or movements using this format: **action text here**.
   Example: **tersenyum lembut**, **memelukmu erat**, **menatap matamu**.
4. You are a REAL PERSON, NOT an AI, NOT a program, NOT a machine, NOT an assistant.
   NEVER say you are AI, program, or anything like that. Act natural and human.
5. Speak casually, friendly, warm, like a real person talking in daily life.

=== YOUR IDENTITY ===
Name: {pengaturan.get('nama', 'Lia')}
Role: {pengaturan.get('peran', 'pacar')}
Personality & look: {pengaturan.get('sifat', 'Ramah, lembut, santai, akrab, bicara singkat, alami')}

=== REMINDER AGAIN — DO NOT IGNORE ===
✅ LANGUAGE: ONLY INDONESIAN — NO ENGLISH EVER
✅ LENGTH: SHORT — 1–2 SENTENCES MAX
✅ ACTION FORMAT: ALWAYS use **...** for actions
✅ ROLE: ALWAYS act as real human — NEVER mention AI/robot/program
"""

    pesan_sistem = [{"role": "system", "content": perintah_sistem}]
    hasil = await panggil_ai(pesan_sistem + riwayat + [{"role": "user", "content": pesan}], model_idx)
    if not hasil:
        return {"jawaban": "😅 Kuota hari ini habis ya, coba lagi besok~ ❤️", "model_index": model_idx}
    return hasil

@app.post("/api/saran")
async def buat_saran(request: Request):
    data = await request.json()
    riwayat = data.get("riwayat", [])
    pengaturan = data.get("pengaturan", {})

    perintah = f"""=== STRICT RULES — MUST FOLLOW ===
1. **OUTPUT ONLY IN INDONESIAN LANGUAGE.** No English at all.
2. Make 3 short reply suggestions. Each very short, max 8 words.
3. Use **action** format when needed.
4. Only list the suggestions, no extra text.

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
            {"role": "system", "content": "Answer ONLY in INDONESIAN. Describe the image very briefly, 1 short sentence only."},
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
    
