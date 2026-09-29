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

                if isinstance(data, dict) and data.get("status") == False:
                    return {
                        "nomor": nomor,
                        "status": "ERROR",
                        "pesan": data.get("message", "Gagal mengambil data KMSP")
                    }

                hasil_asli = data.get("data", {}).get("hasil", "")
                
                # Pembersihan tag HTML dan ubah jadi huruf kecil semua
                hasil_text = hasil_asli.lower().replace("<br>", "\n").replace("</br>", "\n")

                paket_kritis = []
                punya_xtra_combo = False

                if "xtra combo" in hasil_text:
                    punya_xtra_combo = True

                # Memecah teks utuh KMSP menjadi blok per paket (pemisah: kata "quota:")
                blocks = re.split(r'quota:', hasil_text)
                
                for block in blocks:
                    lines = block.strip().split('\n')
                    if not lines:
                        continue
                    
                    # Baris pertama setelah pemotongan adalah Nama Paket
                    pkg_name = lines[0].strip()
                    
                    # Periksa apakah blok ini adalah paket 5 target kita
                    target_found = False
                    for target_pkg in EXACT_TARGET_PACKAGES:
                        if target_pkg in pkg_name:
                            target_found = True
                            break
                            
                    if target_found:
                        # Cari spesifik teks "sisa kuota: X GB/MB" di dalam blok ini saja
                        match = re.search(r"sisa kuota:\s*([\d\.]+)(?:\s*(gb|mb|kb))?", block)
                        if match:
                            sisa_val = match.group(1)
                            sisa_unit = match.group(2)
                            
                            # Jika sisa kuota = 0, KMSP tidak menuliskan 'GB/MB'. Kita setelan default ke MB.
                            if sisa_unit:
                                sisa_str = f"{sisa_val} {sisa_unit.upper()}"
                            else:
                                sisa_str = f"{sisa_val} MB"
                                
                            sisa_mb = parse_mb_from_text(sisa_str)
                            
                            # Jika sisa kuota di bawah ambang batas (500 MB)
                            if sisa_mb < AMBANG_BATAS_MB:
                                sisa_gb = sisa_mb / 1024.0
                                paket_kritis.append({
                                    "nama_paket": pkg_name.title(),
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
