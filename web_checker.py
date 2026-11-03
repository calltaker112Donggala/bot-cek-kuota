import asyncio
import aiohttp
import re

async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    target_url = "https://murakata.22web.org/cek-kuota.php"
    
    # Masukkan API Key ScraperAPI Anda
    SCRAPER_API_KEY = "3d7a277f88ff87325e9ea603b83a76c6"
    
    # ScraperAPI URL
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true"
    
    # Parameter data formulir yang biasa dikirimkan saat tombol Cek diklik
    payload = {
        "nomor": nomor,
        "msisdn": nomor,
        "i": nomor,
        "api": "v1",
        "version": "v1"
    }
    
    try:
        # Mengirimkan POST request ke ScraperAPI
        async with session.post(scraper_url, data=payload, timeout=40) as resp:
            if resp.status == 200:
                html_raw = await resp.text()
                
                # Membersihkan tag script, style, dan tag HTML
                clean_text = re.sub(r'<script.*?>.*?</script>', '', html_raw, flags=re.DOTALL | re.IGNORECASE)
                clean_text = re.sub(r'<style.*?>.*?</style>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
                clean_text = re.sub(r'<[^>]+>', '\n', clean_text)
                
                lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
                hasil_teks = "\n".join(lines)
                
                if not hasil_teks:
                    hasil_teks = "TEKS KOSONG"
                
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"\n[HASIL POST MURAKATA]\n{hasil_teks[:1500]}"
                }
            else:
                return {"nomor": nomor, "status": "ERROR", "pesan": f"HTTP Error: {resp.status}"}
    except asyncio.TimeoutError:
        return {"nomor": nomor, "status": "ERROR", "pesan": "Timeout saat menunggu ScraperAPI (POST)"}
    except Exception as e:
        return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal: {str(e)}"}
