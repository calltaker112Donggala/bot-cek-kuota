import asyncio
import aiohttp
import re

async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    # URL target persis seperti di Inspect Element Anda
    target_url = "https://murakata.22web.org/cek-kuota.php?i"
    
    # MASUKKAN API KEY SCRAPERAPI ANDA DI SINI
    SCRAPER_API_KEY = "3d7a277f88ff87325e9ea603b83a76c6"
    
    # URL ScraperAPI (Tanpa render=true agar POST tidak HTTP 400)
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}"
    
    # Membuat format multipart/form-data persis seperti browser asli
    data = aiohttp.FormData()
    data.add_field('action', 'check_quota')
    data.add_field('api_version', 'v1')
    data.add_field('number', nomor)
    
    try:
        # Kirim payload data ke ScraperAPI
        async with session.post(scraper_url, data=data, timeout=45) as resp:
            if resp.status == 200:
                html_raw = await resp.text()
                
                # Bersihkan tag HTML agar hasilnya mudah dibaca di Telegram
                clean_text = re.sub(r'<script.*?>.*?</script>', '', html_raw, flags=re.DOTALL | re.IGNORECASE)
                clean_text = re.sub(r'<style.*?>.*?</style>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
                clean_text = re.sub(r'<[^>]+>', '\n', clean_text)
                
                lines = [line.strip() for line in clean_text.splitlines() if line.strip()]
                hasil_teks = "\n".join(lines)
                
                if not hasil_teks:
                    hasil_teks = "TEKS KOSONG (Mungkin diblokir oleh anti-bot Murakata)"
                
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"\n[HASIL PAYLOAD MURAKATA]\n{hasil_teks[:1500]}"
                }
            else:
                return {"nomor": nomor, "status": "ERROR", "pesan": f"HTTP Error Scraper: {resp.status}"}
    except asyncio.TimeoutError:
        return {"nomor": nomor, "status": "ERROR", "pesan": "Timeout saat menunggu respons (POST)"}
    except Exception as e:
        return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal: {str(e)}"}
