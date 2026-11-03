import asyncio
import aiohttp
import re

async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    # Menggabungkan seluruh payload form langsung ke dalam URL target (GET Query)
    # Cara ini memungkinkan kita memakai render=true di ScraperAPI tanpa error 400
    target_url = f"https://murakata.22web.org/cek-kuota.php?action=check_quota&api_version=v1&number={nomor}&i={nomor}"
    
    # MASUKKAN API KEY SCRAPERAPI ANDA DI SINI
    SCRAPER_API_KEY = "3d7a277f88ff87325e9ea603b83a76c6"
    
    # Menggunakan render=true agar browser asli ScraperAPI mengeksekusi Javascript-nya
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true"
    
    try:
        # Menggunakan session.get dengan waktu tunggu (timeout) yang aman
        async with session.get(scraper_url, timeout=50) as resp:
            if resp.status == 200:
                html_raw = await resp.text()
                
                # Membersihkan tag script, style, dan elemen HTML agar bersih dibaca di Telegram
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
                    "pesan": f"\n[HASIL AKHIR MURAKATA]\n{hasil_teks[:1500]}"
                }
            else:
                return {"nomor": nomor, "status": "ERROR", "pesan": f"HTTP Error Scraper: {resp.status}"}
    except asyncio.TimeoutError:
        return {"nomor": nomor, "status": "ERROR", "pesan": "Timeout saat menunggu ScraperAPI (Render Browser)"}
    except Exception as e:
        return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal: {str(e)}"}
