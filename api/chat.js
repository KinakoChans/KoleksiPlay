// api/chat.js
export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const { pesan, riwayat, model_index = 0, pengaturan } = req.body;

  // ✅ DAFTAR MODEL GRATIS DARI OPENROUTER — DIURUT DARI TERBAIK KE PALING DASAR
  const DAFTAR_MODEL = [
    // 🔹 KUALITAS TERTINGGI — COBA DULU
    "mistralai/mistral-7b-instruct:free",
    "meta-llama/llama-3-8b-instruct:free",
    "huggingfaceh4/zephyr-7b-beta:free",
    // 🔹 MENENGAH — JIKA DI ATAS HABIS
    "nousresearch/nous-hermes-2-mistral-7b-dpo:free",
    "openchat/openchat-7b:free",
    // 🔹 CADANGAN TERAKHIR — PALING DASAR TAPI MASIH BISA
    "gpt-3.5-turbo-instruct", // ganti dengan model gratis lain kalau perlu
    "mistralai/mistral-7b-v0.1:free"
  ];

  const API_KEY = process.env.OPENROUTER_API_KEY; // Simpan di pengaturan Vercel
  const BASE_URL = "https://openrouter.ai/api/v1/chat/completions";

  let percobaanKe = model_index;
  let hasil = null;
  let errorPesan = "";

  // ✅ LOOP: COBA SATU PER SATU MODEL SAMPAI BERHASIL / HABIS SEMUA
  while (percobaanKe < DAFTAR_MODEL.length) {
    const modelSekarang = DAFTAR_MODEL[percobaanKe];

    try {
      const respons = await fetch(BASE_URL, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${API_KEY}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://oleksi-play.vercel.app/", // Ganti dengan URL kamu
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

      // ✅ CEK: KUOTA HABIS / BATAS / GAGAL → LANGSUNG GANTI MODEL
      if (data.error) {
        const msg = data.error.message || "";
        if (msg.includes("quota") || msg.includes("limit") || msg.includes("exceeded") || msg.includes("insufficient")) {
          // Kuota habis → lanjut ke model berikutnya
          percobaanKe++;
          continue;
        } else {
          errorPesan = msg;
          break;
        }
      }

      // ✅ BERHASIL! KEMBALIKAN HASIL + POSISI MODEL YANG AKTIF
      if (data.choices && data.choices[0]) {
        hasil = {
          jawaban: data.choices[0].message.content.trim(),
          model_index: percobaanKe // Ingat posisi ini untuk pesan selanjutnya
        };
        break;
      }

    } catch (err) {
      // Kalau ada kesalahan jaringan atau lain-lain → coba model berikutnya
      percobaanKe++;
      errorPesan = err.message;
    }
  }

  // ✅ TIDAK ADA MODEL YANG BERHASIL → KASIH PESAN
  if (!hasil) {
    return res.status(200).json({
      jawaban: "😔 Maaf ya, semua model AI hari ini sudah habis kuotanya. Coba lagi besok ya~ ❤️",
      model_index: 0 // Kembali ke awal besok
    });
  }

  return res.status(200).json(hasil);
}

