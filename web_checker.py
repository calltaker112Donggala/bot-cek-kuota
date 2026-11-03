import asyncio
import aiohttp
import re

async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    target_url = f"https://murakata.22web.org/cek-kuota.php?i={nomor}"
    
    # Masukkan API Key dari scraperapi.com milik Anda
    SCRAPER_API_KEY = "API_KEY_ANDA_DISINI"
    
    # render=true digunakan agar JavaScript di web dimuat penuh oleh ScraperAPI
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true"
    
    try:
        async with session.get(scraper_url, timeout=35) as resp:
            if resp.status == 200:
                html_raw = await resp.text()
                
                # Menghapus tag script, style, dan HTML tag agar tersisa teks bersihnya saja
                clean_text = re.sub(r'<script.*?>.*?</script>', '', html_raw, flags=re.DOTALL | re.IGNORECASE)
                clean_text = re.sub(r'<style.*?>.*?</style>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
                clean_text = re.sub(r'<[^>]+>', '\n', clean_text)
                
                # Merapikan baris-baris kosong
                lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
                hasil_teks = "\n".join(lines)
                
                if not hasil_teks:
                    hasil_teks = "TEKS KOSONG"
                
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"\n[ISILAH DATA MURAKATA]\n{hasil_teks[:1500]}"
                }
            else:
                return {"nomor": nomor, "status": "ERROR", "pesan": f"HTTP Scraper Error: {resp.status}"}
    except asyncio.TimeoutError:
        return {"nomor": nomor, "status": "ERROR", "pesan": "Timeout saat menunggu ScraperAPI"}
    except Exception as e:
        return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal: {str(e)}"}
