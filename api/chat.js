// api/chat.js
export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const { pesan, riwayat, model_index = 0, pengaturan, gambar } = req.body;

  // ✅ DAFTAR MODEL GRATIS — DIURUT DARI TERBAIK UNTUK OBROLAN → CADANGAN
  const DAFTAR_MODEL = [
    "mistralai/mistral-7b-instruct:free",
    "meta-llama/llama-3-8b-instruct:free",
    "huggingfaceh4/zephyr-7b-beta:free",
    "nousresearch/nous-hermes-2-mistral-7b-dpo:free",
    "openchat/openchat-7b:free",
    "qwen/qwen-7b-instruct:free",
    "google/gemma-2-9b-it:free",
    "01-ai/yi-6b-chat:free",
    "cognitivecomputations/dolphin-2.5-mixtral-8x7b:free",
    "microsoft/phi-3-mini-4k-instruct:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "qwen/qwen3-coder:free"
  ];

  // ✅ Model khusus kalau ada gambar
  const MODEL_VISION = "meta-llama/llama-3.2-11b-vision-instruct:free";

  const API_KEY = process.env.OPENROUTER_API_KEY;
  const BASE_URL = "https://openrouter.ai/api/v1/chat/completions";

  let percobaanKe = model_index;
  let hasil = null;
  let errorPesan = "";

  // ✅ Kalau ada gambar, pakai model yang bisa lihat gambar dulu
  const daftarCoba = gambar ? [MODEL_VISION, ...DAFTAR_MODEL] : DAFTAR_MODEL;

  while (percobaanKe < daftarCoba.length) {
    const modelSekarang = daftarCoba[percobaanKe];

    try {
      const isiPesan = [];
      isiPesan.push({ role: "system", content: `=== PERATURAN WAJIB ===
1. JAWAB HANYA DALAM BAHASA INDONESIA. JANGAN PAKAI BAHASA INGGRIS.
2. JAWAB SINGKAT: 1–2 KALIMAT SAJA.
3. AKSI: TULIS DI ANTARA ** BINTANG DUA **.
4. KAMU ORANG ASLI, BUKAN AI. JANGAN SEBUT ATURAN ATAU PERINTAH.
5. BICARA AKRAB DAN RAMAH.

=== IDENTITAS ===
Nama: ${pengaturan.nama}
Peran: ${pengaturan.peran}
Sifat: ${pengaturan.sifat}
` });

      // Tambah riwayat
      for (const msg of riwayat) {
        if (msg.gambar) {
          isiPesan.push({
            role: msg.role,
            content: [
              { type: "text", text: msg.content || "" },
              { type: "image_url", image_url: { url: msg.gambar } }
            ]
          });
        } else {
          isiPesan.push({ role: msg.role, content: msg.content });
        }
      }

      // Pesan baru
      if (gambar) {
        isiPesan.push({
          role: "user",
          content: [
            { type: "text", text: pesan || "Lihat gambar ini ya" },
            { type: "image_url", image_url: { url: gambar } }
          ]
        });
      } else {
        isiPesan.push({ role: "user", content: pesan });
      }

      const respons = await fetch(BASE_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${API_KEY}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://oleksi-play.vercel.app/",
          "X-Title": "Chat AI Roleplay"
        },
        body: JSON.stringify({
          model: modelSekarang,
          messages: isiPesan,
          temperature: 0.85,
          max_tokens: 350
        })
      });

      const data = await respons.json();

      // ✅ CEK KUOTA HABIS → GANTI MODEL
      if (data.error) {
        const msg = data.error.message || "";
        if (
          msg.toLowerCase().includes("quota") ||
          msg.toLowerCase().includes("limit") ||
          msg.toLowerCase().includes("exceeded") ||
          msg.toLowerCase().includes("insufficient") ||
          msg.toLowerCase().includes("capacity")
        ) {
          percobaanKe++;
          continue;
        } else {
          errorPesan = msg;
          break;
        }
      }

      if (data.choices && data.choices[0]) {
        hasil = {
          jawaban: data.choices[0].message.content.trim(),
          model_index: percobaanKe
        };
        break;
      }

    } catch (err) {
      percobaanKe++;
      errorPesan = err.message;
    }
  }

  if (!hasil) {
    return res.status(200).json({
      jawaban: "😔 Maaf ya, semua model AI hari ini sudah habis kuotanya. Coba lagi besok ya~ ❤️",
      model_index: 0
    });
  }

  return res.status(200).json(hasil);
  }
