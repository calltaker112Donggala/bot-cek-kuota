import asyncio
import aiohttp

async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    # URL Asli yang ingin dituju
    target_url = f"https://murakata.22web.org/cek-kuota.php?i={nomor}"
    
    # GANTI 'API_KEY_ANDA_DISINI' DENGAN API KEY DARI SCRAPERAPI.COM
    SCRAPER_API_KEY = "3d7a277f88ff87325e9ea603b83a76c6"
    
    # URL Endpoint milik ScraperAPI
    # Parameter render=true menyuruh server mereka menggunakan Headless Browser untuk mengeksekusi JavaScript
    scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={target_url}&render=true"
    
    try:
        # Perbesar timeout karena proses render browser asli butuh waktu
        async with session.get(scraper_url, timeout=30) as resp:
            if resp.status == 200:
                teks_mentah = await resp.text()
                
                # Membersihkan tag HTML agar mudah dibaca saat pengujian
                teks_bersih = teks_mentah.replace("<br>", "\n").replace("</br>", "\n")
                
                if not teks_bersih.strip():
                    teks_bersih = "HALAMAN KOSONG"
                    
                # Kita kirim hasil mentah ini ke Telegram dulu untuk melihat isinya
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"\n[TEKS ASLI MURAKATA VIA SCRAPER]\n{teks_bersih[:900]}"
                }
            else:
                return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal HTTP: {resp.status}"}
    except asyncio.TimeoutError:
        return {"nomor": nomor, "status": "ERROR", "pesan": "ScraperAPI lambat merespons (Timeout)"}
    except Exception as e:
        return {"nomor": nomor, "status": "ERROR", "pesan": f"Gagal terkoneksi: {str(e)}"}
