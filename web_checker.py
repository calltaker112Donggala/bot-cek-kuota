import asyncio
import aiohttp

async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    # Mengarah ke web Murakata
    url = "https://murakata.22web.org/cek-kuota.php"
    
    # Parameter i=nomor sesuai dengan URL yang Anda berikan
    params = {"i": nomor}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    try:
        async with session.get(url, params=params, headers=headers, timeout=20) as resp:
            if resp.status == 200:
                # Ambil seluruh teks HTML dari website
                teks_mentah = await resp.text()
                
                # Bersihkan sedikit tag HTML sederhana agar mudah dibaca di Telegram
                teks_bersih = teks_mentah.replace("<br>", "\n").replace("</br>", "\n").replace("<br/>", "\n")
                
                if not teks_bersih.strip():
                    teks_bersih = "HALAMAN KOSONG"
                    
                # KITA PAKSA ERROR AGAR TEKS MENTAHNYA TAMPIL DI TELEGRAM
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"\n[TEKS ASLI MURAKATA]\n{teks_bersih[:900]}"
                }
            else:
                return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal HTTP: {resp.status}"}
    except asyncio.TimeoutError:
        return {"nomor": nomor, "status": "ERROR", "pesan": "Website Murakata lambat merespons (Timeout)"}
    except Exception as e:
        return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal terkoneksi: {str(e)}"}
