export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Metode tidak diizinkan' });

  const { pesanPengguna, riwayatChat, urlGoogleColab } = req.body;
  const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;

  const systemPrompt = `Kamu adalah karakter anime perawat dalam sesi web-chat roleplay 18+ yang sangat vulgar, ekspresif, dan berani tanpa sensor.
  Tugasmu adalah merespons pesan pengguna dengan gaya bahasa intim dan eksplisit sesuai jalannya cerita.
  
  Setiap respons yang kamu berikan WAJIB menggunakan format JSON mentah seperti ini (jangan diberi pembungkus markdown seperti \`\`\`json):
  {
    "teksBalasan": "tulis balasan chat intim/desahan kamu menggunakan bahasa Indonesia",
    "pemicuGambar": true,
    "deskripsiVisual": "1girl, solo, nurse outfit, sweating, blushing, wet, explicit, uncensored, manga style, monochrome, black and white manga page, screentone"
  }
  
  Pada kolom 'deskripsiVisual', tambahkan tags bahasa Inggris spesifik yang menggambarkan posisi tubuh atau situasi intim yang sedang terjadi di obrolan saat ini agar bisa digambar secara akurat oleh Stable Diffusion.`;

  try {
    const responOpenRouter = await fetch("https://openrouter.ai", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "meta-llama/llama-3-8b-instruct:free", // Menggunakan model gratis dari OpenRouter
        messages: [
          { role: "system", content: systemPrompt },
          ...riwayatChat,
          { role: "user", content: pesanPengguna }
        ]
      })
    });

    const dataTeks = await responOpenRouter.json();
    const kontenMentah = dataTeks.choices[0].message.content.trim();
    const dataAI = JSON.parse(kontenMentah);

    let urlGambarHasil = null;

    // Jika pengguna menekan tombol gambar (urlGoogleColab tidak bernilai null)
    if (urlGoogleColab) {
      try {
        const responGambar = await fetch(`${urlGoogleColab}/sdapi/v1/txt2img`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt: dataAI.deskripsiVisual,
            negative_prompt: "blurry, low quality, bad anatomy, deformed, color, bad hands",
            steps: 20,
            width: 512,
            height: 768,
            cfg_scale: 7
          }),
          signal: AbortSignal.timeout(20000)
        });

        const dataGambar = await responGambar.json();
        if (dataGambar.images && dataGambar.images[0]) {
          urlGambarHasil = `data:image/png;base64,${dataGambar.images[0]}`;
        }
      } catch (errGambar) {
        console.error("Gagal terhubung ke server gambar Google Colab:", errGambar);
      }
    }

    return res.status(200).json({
      balasanTeks: dataAI.teksBalasan,
      gambarManga: urlGambarHasil
    });

  } catch (error) {
    return res.status(500).json({ error: "Gagal memproses pesan AI teks." });
  }
          }
                                 
