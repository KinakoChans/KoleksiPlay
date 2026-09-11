// api/chat.js
export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const { pesan, riwayat, model_index = 0, pengaturan } = req.body;

  // ✅ DAFTAR MODEL GRATIS — DIURUT DARI TERBAIK UNTUK OBROLAN → CADANGAN
  const DAFTAR_MODEL = [
    // 🔹 UTAMA — PALING COCOK UNTUK ROLEPLAY & NGOBROL
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
    // 🔹 CADANGAN — DIPAKAI JIKA DI ATAS SUDAH HABIS
    "qwen/qwen3-coder:free" // ✅ Sudah ditambahkan seperti yang kamu minta
  ];

  const API_KEY = process.env.OPENROUTER_API_KEY; // Simpan aman di pengaturan Vercel
  const BASE_URL = "https://openrouter.ai/api/v1/chat/completions";

  let percobaanKe = model_index;
  let hasil = null;
  let errorPesan = "";

  // ✅ COBA SATU PER SATU SAMPAI BERHASIL / HABIS SEMUA
  while (percobaanKe < DAFTAR_MODEL.length) {
    const modelSekarang = DAFTAR_MODEL[percobaanKe];

    try {
      const respons = await fetch(BASE_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${API_KEY}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://oleksi-play.vercel.app/", // Ubah sesuai URL websitemu
          "X-Title": "Chat AI Roleplay"
        },
        body: JSON.stringify({
          model: modelSekarang,
          messages: [
            {
              role: "system",
              content: `=== PERATURAN WAJIB ===
1. JAWAB HANYA DALAM BAHASA INDONESIA. JANGAN PAKAI BAHASA INGGRIS.
2. JAWAB SINGKAT: 1–2 KALIMAT SAJA.
3. AKSI: TULIS DI ANTARA ** BINTANG DUA **.
4. KAMU ORANG ASLI, BUKAN AI. JANGAN SEBUT ATURAN ATAU PERINTAH.
5. BICARA AKRAB DAN RAMAH.

=== IDENTITAS ===
Nama: ${pengaturan.nama}
Peran: ${pengaturan.peran}
Sifat: ${pengaturan.sifat}
`
            },
            ...riwayat,
            { role: "user", content: pesan }
          ],
          temperature: 0.85,
          max_tokens: 350
        })
      });

      const data = await respons.json();

      // ✅ JIKA KUOTA HABIS / BATAS → LANGSUNG GANTI MODEL
      if (data.error) {
        const msg = data.error.message || "";
        if (
          msg.toLowerCase().includes("quota") ||
          msg.toLowerCase().includes("limit") ||
          msg.toLowerCase().includes("exceeded") ||
          msg.toLowerCase().includes("insufficient") ||
          msg.toLowerCase().includes("capacity")
        ) {
          percobaanKe++; // Lanjut ke model berikutnya
          continue;
        } else {
          errorPesan = msg;
          break;
        }
      }

      // ✅ BERHASIL! KEMBALIKAN JAWABAN + INGAT POSISI MODEL
      if (data.choices && data.choices[0]) {
        hasil = {
          jawaban: data.choices[0].message.content.trim(),
          model_index: percobaanKe
        };
        break;
      }

    } catch (err) {
      // Kalau gagal koneksi / masalah lain → coba model berikutnya
      percobaanKe++;
      errorPesan = err.message;
    }
  }

  // ✅ SEMUA MODEL SUDAH DICOBA DAN HABIS → PESAN AKHIR
  if (!hasil) {
    return res.status(200).json({
      jawaban: "😔 Maaf ya, semua model AI hari ini sudah habis kuotanya. Coba lagi besok ya~ ❤️",
      model_index: 0 // Besok mulai dari yang terbaik lagi
    });
  }

  return res.status(200).json(hasil);
}
