// api/saran.js
export default async function handler(req, res) {
    if (req.method !== 'POST') return res.status(405).end();
    return res.status(200).json({
        saran: [
            "**tersenyum manis** Iyaaa? Apa itu?",
            "Tentu saja~ Aku selalu siap dengerin kamu ❤️",
            "**menatap lembut** Kamu lucu banget deh~"
        ]
    });
}
