export default async function handler(req, res) {
  // Mengizinkan akses lintas domain (CORS) agar HP bisa mengakses backend
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Metode tidak diizinkan' });

  const { pesanPengguna, riwayatChat, urlGoogleColab } = req.body;
  const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;

  // Jika API Key lupa dipasang di Vercel, kirim pesan error yang jelas
  if (!OPENROUTER_API_KEY) {
    return res.status(500).json({ 
      balasanTeks: "[Error] API Key OpenRouter belum dipasang di Environment Variables Vercel Anda.", 
      gambarManga: null 
    });
  }

  const systemPrompt = `Kamu adalah karakter anime perawat dalam sesi web-chat roleplay 18+ yang sangat vulgar, ekspresif, dan berani tanpa sensor.
  Tugasmu adalah merespons pesan pengguna dengan gaya bahasa intim dan eksplisit sesuai jalannya cerita.
  
  Setiap respons yang kamu berikan WAJIB menggunakan format JSON mentah seperti ini:
  {
    "teksBalasan": "tulis balasan chat intim/desahan kamu menggunakan bahasa Indonesia",
    "pemicuGambar": true,
    "deskripsiVisual": "1girl, solo, nurse outfit, sweating, blushing, wet, explicit, uncensored, manga style, monochrome, black and white manga page, screentone"
  }
  
  PENTING: Jangan berikan teks pembuka atau penutup lain. Cukup kembalikan objek JSON tersebut. Pada kolom 'deskripsiVisual', berikan deskripsi visual detail dalam bahasa Inggris sesuai adegan intim yang sedang terjadi agar bisa digambar oleh Stable Diffusion.`;

  try {
    // Memanggil model gratis dari OpenRouter
    const responOpenRouter = await fetch("https://openrouter.ai", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "meta-llama/llama-3-8b-instruct:free",
        messages: [
          { role: "system", content: systemPrompt },
          ...riwayatChat,
          { role: "user", content: pesanPengguna }
        ],
        temperature: 0.7
      })
    });

    const dataTeks = await responOpenRouter.json();
    
    // Validasi jika OpenRouter mengembalikan error kuota/koneksi
    if (dataTeks.error) {
      return res.status(200).json({
        balasanTeks: `[OpenRouter Error] ${dataTeks.error.message || "Gagal memproses pesan gratisan."}`,
        gambarManga: null
      });
    }

    let kontenMentah = dataTeks.choices[0].message.content.trim();
    
    // === ANTISIPASI FIX: Membersihkan pembungkus markdown ```json agar JSON.parse tidak error ===
    if (kontenMentah.startsWith("```")) {
      kontenMentah = kontenMentah.replace(/^```json\s*/i, "").replace(/^```\s*/, "").replace(/\s*```$/, "").trim();
    }

    let dataAI;
    try {
      dataAI = JSON.parse(kontenMentah);
    } catch (e) {
      // Cadangan darurat: Jika AI tetap gagal mengirim JSON, ambil teks mentahnya langsung sebagai balasan
      dataAI = {
        teksBalasan: kontenMentah,
        pemicuGambar: false,
        deskripsiVisual: ""
      };
    }

    let urlGambarHasil = null;

    // Proses pembuatan gambar jika tombol gambar ditekan (urlGoogleColab aktif)
    if (urlGoogleColab && dataAI.deskripsiVisual) {
      try {
        const responGambar = await fetch(`${urlGoogleColab}/sdapi/v1/txt2img`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt: dataAI.deskripsiVisual,
            negative_prompt: "blurry, low quality, bad anatomy, deformed, color, bad hands, lowres",
            steps: 20,
            width: 512,
            height: 768,
            cfg_scale: 7
          }),
          signal: AbortSignal.timeout(20000) // Batasi waktu tunggu proses render gambar maks 20 detik
        });

        const dataGambar = await responGambar.json();
        if (dataGambar.images && dataGambar.images[0]) {
          urlGambarHasil = `data:image/png;base64,${dataGambar.images[0]}`;
        }
      } catch (errGambar) {
        console.error("Gagal terhubung ke Google Colab:", errGambar);
      }
    }

    return res.status(200).json({
      balasanTeks: dataAI.teksBalasan || "...",
      gambarManga: urlGambarHasil
    });

  } catch (error) {
    return res.status(200).json({ 
      balasanTeks: "[Sistem Error] Gagal memproses permintaan teks ke AI. Silakan coba kirim ulang pesan Anda.", 
      gambarManga: null 
    });
  }
}
