import asyncio
import aiohttp

async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    # Ganti URL ini dengan link persis saat Anda membuka menu cek kuota di web mereka
    url = "https://akrab.axiestore.com/" 
    
    # Kita coba tebak parameternya (biasanya 'nomor', 'msisdn', atau 'no')
    params = {"nomor": nomor} 
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    try:
        async with session.get(url, params=params, headers=headers, timeout=20) as resp:
            teks_mentah = await resp.text()
            
            # Bersihkan sedikit tag HTML agar tidak berantakan di Telegram
            teks_bersih = teks_mentah.replace("<br>", "\n").replace("</br>", "\n").replace("<br/>", "\n")
            
            if not teks_bersih.strip():
                teks_bersih = "HALAMAN KOSONG"
                
            # Kita paksa tampil di Telegram
            return {
                "nomor": nomor,
                "status": "ERROR",
                "pesan": f"\n[TEKS ASLI AXIESTORE]\nStatus HTTP: {resp.status}\n\n{teks_bersih[:800]}"
            }
    except asyncio.TimeoutError:
        return {"nomor": nomor, "status": "ERROR", "pesan": "Website lambat merespons (Timeout)"}
    except Exception as e:
        return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal terkoneksi: {str(e)}"}
