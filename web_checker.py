import asyncio
import json
import aiohttp

async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    url = "https://apigw.kmsp-store.com/sidompul/v4/cek_kuota"
    params = {"msisdn": nomor, "isJSON": "true"}
    headers = {
        "Authorization": "Basic c2lkb21wdWxhcGk6YXBpZ3drbXNw",
        "X-API-Key": "60ef29aa-a648-4668-90ae-20951ef90c55",
        "X-App-Version": "4.0.0"
    }
    
    try:
        async with session.get(url, params=params, headers=headers, timeout=15) as resp:
            if resp.status == 200:
                data = json.loads(await resp.text())
                
                # Ambil teks mentah dari KMSP
                hasil_asli = data.get("data", {}).get("hasil", "")
                teks_mentah = hasil_asli.replace("<br>", "\n").replace("</br>", "\n")
                
                if not teks_mentah.strip():
                    teks_mentah = "DATA KOSONG DARI API"
                    
                # KITA PAKSA ERROR AGAR TEKS MENTAHNYA TAMPIL DI TELEGRAM
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"\n[TEKS ASLI KMSP]\n{teks_mentah[:800]}"
                }
            else:
                return {"nomor": nomor, "status": "ERROR", "pesan": "Gagal HTTP"}
    except Exception as e:
        return {"nomor": nomor, "status": "ERROR", "pesan": str(e)}
