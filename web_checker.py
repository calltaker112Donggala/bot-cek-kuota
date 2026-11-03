import asyncio
import aiohttp
import re

async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    # Mengarahkan langsung dengan parameter nomor HP pada URL GET
    target_url = f"https://murakata.22web.org/cek-kuota.php?i={nomor}"
    
    # Masukkan API Key ScraperAPI Anda
    SCRAPER_API_KEY = "3d7a277f88ff87325e9ea603b83a76c6"
    
    # URL ScraperAPI menggunakan GET + render=true
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    try:
        # Menggunakan session.get (bukan post)
        async with session.get(scraper_url, headers=headers, timeout=45) as resp:
            if resp.status == 200:
                html_raw = await resp.text()
                
                # Membersihkan tag script, style, dan elemen HTML
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
                    "pesan": f"\n[HASIL GET SCRAPER]\n{hasil_teks[:1500]}"
                }
            else:
                return {"nomor": nomor, "status": "ERROR", "pesan": f"HTTP Error Scraper: {resp.status}"}
    except asyncio.TimeoutError:
        return {"nomor": nomor, "status": "ERROR", "pesan": "Timeout saat menunggu ScraperAPI (GET)"}
    except Exception as e:
        return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal: {str(e)}"}
