import asyncio
import json
import re
import aiohttp

EXACT_TARGET_PACKAGES = [
    "bonus kuota whatsapp",
    "bonus kuota facebook",
    "bonus kuota instagram",
    "bonus kuota youtube",
    "bonus kuota tiktok",
]

AMBANG_BATAS_MB = 500.0


def parse_mb_from_text(text_kuota: str) -> float:
    text = str(text_kuota).strip().upper()
    if text == "0" or not text:
        return 0.0

    match = re.search(r"([\d\.]+)\s*(GB|MB|KB)?", text)
    if not match:
        return 0.0

    val = float(match.group(1))
    unit = match.group(2) if match.group(2) else "MB"

    if unit == "GB":
        return val * 1024.0
    elif unit == "KB":
        return val / 1024.0
    return val


async def fetch_single_nomor_async(session: aiohttp.ClientSession, nomor: str):
    url = "https://apigw.kmsp-store.com/sidompul/v4/cek_kuota"
    params = {
        "msisdn": nomor,
        "isJSON": "true"
    }

    headers = {
        "Authorization": "Basic c2lkb21wdWxhcGk6YXBpZ3drbXNw",
        "X-API-Key": "60ef29aa-a648-4668-90ae-20951ef90c55",
        "X-App-Version": "4.0.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }

    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with session.get(url, params=params, headers=headers, timeout=timeout) as resp:
            if resp.status == 200:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    data = json.loads(await resp.text())

                # Jika status API dari KMSP false
                if isinstance(data, dict) and data.get("status") == False:
                    return {
                        "nomor": nomor,
                        "status": "ERROR",
                        "pesan": data.get("message", "Gagal mengambil data dari KMSP")
                    }

                # ==============================================================
                # MENAMPILKAN FULL TEKS KMSP KE LOG RAILWAY
                # ==============================================================
                hasil_asli = data.get("data", {}).get("hasil", "")
                print(f"\n=== FULL DATA KMSP {nomor} ===")
                # Bersihkan tag html agar mudah dibaca di log
                print(hasil_asli.replace("<br>", "\n").replace("</br>", "\n"))
                print("================================\n")

                paket_kritis = []
                punya_xtra_combo = False

                hasil_text = hasil_asli.lower().replace("<br>", "\n").replace("</br>", "\n")

                if "xtra combo" in hasil_text:
                    punya_xtra_combo = True

                for target_pkg in EXACT_TARGET_PACKAGES:
                    if target_pkg in hasil_text:
                        idx = hasil_text.find(target_pkg)
                        chunk = hasil_text[idx : idx + 120]
                        match = re.search(r"(\d+(?:\.\d+)?)\s*(gb|mb|kb)", chunk)
                        if match:
                            sisa_str = match.group(0).upper()
                            sisa_mb = parse_mb_from_text(sisa_str)
                            
                            if sisa_mb < AMBANG_BATAS_MB:
                                sisa_gb = sisa_mb / 1024.0
                                paket_kritis.append({
                                    "nama_paket": target_pkg.title(),
                                    "sisa_mb": sisa_mb,
                                    "sisa_gb": sisa_gb,
                                    "sisa_str": sisa_str,
                                })

                return {
                    "nomor": nomor,
                    "status": "SUCCESS",
                    "paket_kritis": paket_kritis,
                    "punya_xtra_combo": punya_xtra_combo,
                }
            
            else:
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"HTTP {resp.status} (Masalah server KMSP)"
                }

    except asyncio.TimeoutError:
        return {
            "nomor": nomor,
            "status": "ERROR",
            "pesan": "Timeout (Server KMSP sedang lambat)",
        }
    except Exception as e:
        return {
            "nomor": nomor,
            "status": "ERROR",
            "pesan": f"Gagal terkoneksi: {str(e)}",
        }
