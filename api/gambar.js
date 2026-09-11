// api/gambar.js
export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(405).end();
    return res.status(200).json({ url: null, pesan: "Fitur bikin gambar sedang diperbaiki~" });
}

