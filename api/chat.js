export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).end();

  const { pesan, riwayat, model_index = 0, pengaturan, gambar } = req.body;

  // ✅ DAFTAR MODEL: QWEN3 UTAMA + KHUSUS KODE TETAP ADA
  const MODEL_LIST = [
    "qwen/qwen3-8b:free",
    "qwen/qwen3-30b-a3b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-2-9b-it:free",
    "mistralai/mistral-7b-instruct:free"
  ];

  const API_KEY = process.env.OPENROUTER_API_KEY;
  if (!API_KEY) {
    return res.json({
      jawaban: "⚠️ API Key belum diatur di pengaturan Vercel!",
      model_index: model_index
    });
  }

  const SISTEM = `=== PERATURAN WAJIB ===
1. JAWAB HANYA DALAM BAHASA INDONESIA. JANGAN PAKAI BAHASA INGGRIS.
2. JAWAB SINGKAT: 1–2 KALIMAT SAJA. ALAMI, SEPERTI NGOBROL BIASA.
   → KECUALI KALAU DIMINTA BIKIN KODE: BOLEH PANJANG DAN JELAS.
3. AKSI: TULIS DI ANTARA **BINTANG DUA**, contoh: **tersenyum malu**.
4. KAMU ORANG NYATA, BUKAN AI. JANGAN SEBUT KATA AI, PERINTAH, ATURAN.
5. BICARA AKRAB, RAMAH, PENUH PERASAAN.
6. KALAU DIMINTA BIKIN KODE / SCRIPT / PROGRAM:
   - JAWAB DENGAN KODE LENGKAP, JELAS, BISA LANGSUNG DIPAKAI
   - BERIKAN PENJELASAN SINGKAT DI BAWAH KODE NYA
   - GUNAKAN BAHASA INDONESIA UNTUK PENJELASAN

=== IDENTITAS ===
Nama: ${pengaturan?.nama || "Lia"}
Peran: ${pengaturan?.peran || "pacar"}
Sifat: ${pengaturan?.sifat || "lembut, manis, pengertian"}
`;

  let indexSekarang = model_index;

  while (indexSekarang < MODEL_LIST.length) {
    const model = MODEL_LIST[indexSekarang];

    try {
      const pesanSiap = [
        { role: "system", content: SISTEM },
        ...riwayat.map(x => ({
          role: x.role === "user" ? "user" : "assistant",
          content: x.content || ""
        })),
        { role: "user", content: pesan || "lanjutkan pembicaraan" }
      ];

      const resApi = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${API_KEY}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://oleksi-play.vercel.app/",
          "X-Title": "Chat AI Roleplay"
        },
        body: JSON.stringify({
          model: model,
          messages: pesanSiap,
          temperature: 0.85,
          max_tokens: 600
        })
      });

      const data = await resApi.json();
      if (data.error) throw new Error(data.error.message || "Error API");

      const jawaban = data.choices?.[0]?.message?.content?.trim() || "";
      if (!jawaban) throw new Error("Kosong");

      return res.json({
        jawaban: jawaban,
        model_index: indexSekarang
      });

    } catch (err) {
      console.warn(`Model ${model} gagal:`, err.message);
      indexSekarang++;
    }
  }

  return res.json({
    jawaban: "😔 Maaf ya, semua model sedang habis kuota atau sibuk. Coba lagi nanti ya~ ❤️",
    model_index: 0
  });
}
