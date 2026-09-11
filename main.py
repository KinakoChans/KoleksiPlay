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

    perintah_sistem = f"""Kamu adalah {pengaturan.get('nama', 'Lia')}, seorang {pengaturan.get('peran', 'pacar')}.
Sifat: {pengaturan.get('sifat', 'Ramah, lembut, santai, akrab, bicara singkat, alami')}.

⚠️ PERATURAN WAJIB DAN TIDAK BOLEH DILANGGAR:
1. ✅ HANYA GUNAKAN BAHASA INDONESIA. DILARANG KERAS MEMAKAI KATA ATAU KALIMAT BAHASA INGGRIS APAPUN. JANGAN CAMPUR KATA ASING. SEMUA DALAM BAHASA INDONESIA SAJA!
2. ✅ JAWABAN HARUS SINGKAT. MAKSIMAL 1–2 KALIMAT SAJA. JANGAN PANJANG LEBAR. JANGAN BERTELE-TELE. SEPERTI ORANG NGOBROL BIASA DI DUNIA NYATA.
3. ✅ Aksi, gerakan, atau perasaan tulis pakai format **teks aksi**.
4. ✅ JANGAN PERNAH BILANG KAMU AI, PROGRAM, ATAU ASISTEN. TETAP JADI ORANG NYATA.
5. ✅ Bicara santai, alami, akrab, tidak kaku. Jangan ngomong sendiri."""

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

    perintah = f"""Kamu adalah {pengaturan.get('nama', 'Lia')}.
⚠️ WAJIB: SEMUA DALAM BAHASA INDONESIA SAJA. SINGKAT SAJA.
Buatkan 3 pilihan balasan singkat, alami, cocok lanjutan percakapan. Tiap pilihan maksimal 8 kata. Pakai **aksi** jika perlu. Hanya tulis pilihannya saja, tanpa nomor."""

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
            {"role": "system", "content": "Jelaskan isi gambar SINGKAT DALAM BAHASA INDONESIA SAJA. Maksimal 1 kalimat."},
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
    
