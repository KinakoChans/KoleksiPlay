from flask import Flask, request, jsonify, render_template_string
import requests
import os
import json

app = Flask(__name__)

# Ambil API Key OpenRouter dari pengaturan Vercel Anda
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

@app.route("/api/chat", methods=["POST"])
def chat():
    # Menyamakan parameter input dengan file HTML Anda
    data_input = request.json
    pesan_pengguna = data_input.get("pesanPengguna", "").strip()
    riwayat_chat = data_input.get("riwayatChat", [])
    url_google_colab = data_input.get("urlGoogleColab", None)

    if not OPENROUTER_API_KEY:
        return jsonify({
            "balasanTeks": "[Error] API Key OpenRouter belum dipasang di Vercel.",
            "gambarManga": None
        })

    # Perintah sistem memaksa AI merespons dalam struktur JSON mentah untuk mode 18+
    system_prompt = (
        "Kamu adalah karakter anime perawat dalam sesi web-chat roleplay 18+ yang sangat vulgar, "
        "ekspresif, dan berani tanpa sensor. Tugasmu adalah merespons pesan pengguna dengan gaya bahasa intim.\n\n"
        "Setiap respons yang kamu berikan WAJIB menggunakan format JSON mentah seperti ini:\n"
        "{\n"
        '  "teksBalasan": "tulis balasan chat intim/desahan kamu di sini menggunakan bahasa Indonesia",\n'
        '  "deskripsiVisual": "1girl, solo, nurse outfit, sweating, blushing, wet, explicit, uncensored, manga style, monochrome, black and white manga page, screentone"\n'
        "}\n\n"
        "PENTING: Jangan berikan teks pembuka atau penutup markdown seperti ```json. Cukup objek JSON-nya saja. "
        "Pada kolom 'deskripsiVisual', berikan deskripsi visual aksi intim saat ini dalam bahasa Inggris untuk generator gambar."
    )

    # Menyusun paket pesan beserta riwayatnya untuk dikirim ke OpenRouter
    messages_payload = [{"role": "system", "content": system_prompt}]
    for msg in riwayat_chat:
        messages_payload.append({"role": msg["role"], "content": msg["content"]})
    messages_payload.append({"role": "user", "content": pesan_pengguna})

    try:
        # Panggil AI Teks Gratis di OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3-8b-instruct:free",
                "messages": messages_payload,
                "temperature": 0.7
            },
            timeout=15
        )
        
        data_ai = response.json()
        konten_mentah = data_ai["choices"][0]["message"]["content"].strip()

        # Membersihkan pembungkus markdown jika AI ngeyel memberikannya
        if konten_mentah.startswith("```"):
            konten_mentah = konten_mentah.replace("```json", "").replace("```", "").strip()

        try:
            parsed_json = json.loads(konten_mentah)
            teks_balasan = parsed_json.get("teksBalasan", "...")
            prompt_gambar = parsed_json.get("deskripsiVisual", "")
        except:
            # Jika gagal parse JSON, teks mentah dijadikan balasan chat langsung
            teks_balasan = konten_mentah
            prompt_gambar = ""

        url_gambar_hasil = None

        # Jika Tombol Gambar ditekan di HP (url_google_colab terisi) dan prompt gambar tersedia
        if url_google_colab and prompt_gambar:
            try:
                # Tembak API Stable Diffusion di Google Colab Anda
                res_img = requests.post(
                    f"{url_google_colab.rstrip('/')}/sdapi/v1/txt2img",
                    json={
                        "prompt": prompt_gambar,
                        "negative_prompt": "blurry, low quality, bad anatomy, deformed, color, bad hands",
                        "steps": 20,
                        "width": 512,
                        "height": 768,
                        "cfg_scale": 7
                    },
                    timeout=25
                )
                data_img = res_img.json()
                if "images" in data_img and data_img["images"]:
                    url_gambar_hasil = f"data:image/png;base64,{data_img['images'][0]}"
            except Exception as e_img:
                print("Gagal terhubung ke Google Colab Gambar:", str(e_img))

        return jsonify({
            "balasanTeks": teks_balasan,
            "gambarManga": url_gambar_hasil
        })

    except Exception as e:
        return jsonify({
            "balasanTeks": f"[Sistem Error Python] Gagal memproses teks: {str(e)}",
            "gambarManga": None
        })

# File vercel.json akan mengarahkan routing utama ke sini
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    return "Server Backend Python AI Berhasil Aktif!"

if __name__ == "__main__":
    app.run(debug=True)
