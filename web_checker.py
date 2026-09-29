import asyncio
import json
import re
import aiohttp

EXACT_TARGET_PACKAGES = [
    "bonus kuota whatsapp 10gb",
    "bonus kuota facebook 10gb",
    "bonus kuota instagram 1gb",
    "bonus kuota instagram 10gb",
    "bonus kuota youtube 10gb",
    "bonus kuota tiktok 10gb",
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
    # Endpoint KMSP Store terbaru
    url = "https://apigw.kmsp-store.com/sidompul/v4/cek_kuota"
    params = {
        "msisdn": nomor,
        "isJSON": "true"
    }

    # Header KMSP sesuai dengan skrip PHP yang Anda dapatkan
    headers = {
        "Authorization": "Basic c2lkb21wdWxhcGk6YXBpZ3drbXNw",
        "X-API-Key": "60ef29aa-a648-4668-90ae-20951ef90c55",
        "X-App-Version": "4.0.0",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    timeout = aiohttp.ClientTimeout(total=15)

    try:
        async with session.get(url, params=params, headers=headers, timeout=timeout) as resp:
            if resp.status == 200:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    text_resp = await resp.text()
                    data = json.loads(text_resp)
                
                # Menampilkan log response di Railway untuk memantau struktur JSON
                print(f"Data API {nomor}: {str(data)[:150]}...")

                # Jika KMSP mengembalikan error di dalam JSON-nya
                if isinstance(data, dict) and data.get("status") == False:
                    return {
                        "nomor": nomor,
                        "status": "ERROR",
                        "pesan": data.get("message", "Gagal dari server KMSP")
                    }

                paket_kritis = []
                punya_xtra_combo = False

                # Karena KMSP juga mengambil dari Sidompul, strukturnya kemungkinan sama persis
                quotas_groups = (
                    data.get("data", {})
                    .get("data_sp", {})
                    .get("quotas", {})
                    .get("value", [])
                )

                for group in quotas_groups:
                    for item in group:
                        pkg_info = item.get("packages", {})
                        pkg_name = str(pkg_info.get("name", "")).strip()
                        pkg_name_lower = pkg_name.lower()

                        if "xtra combo" in pkg_name_lower:
                            punya_xtra_combo = True

                        benefits = item.get("benefits", [])

                        for b in benefits:
                            remaining_str = str(b.get("remaining", "0"))

                            if any(target in pkg_name_lower for target in EXACT_TARGET_PACKAGES):
                                sisa_mb = parse_mb_from_text(remaining_str)

                                if sisa_mb < AMBANG_BATAS_MB:
                                    sisa_gb = sisa_mb / 1024.0
                                    paket_kritis.append(
                                        {
                                            "nama_paket": pkg_name,
                                            "sisa_mb": sisa_mb,
                                            "sisa_gb": sisa_gb,
                                            "sisa_str": remaining_str,
                                        }
                                    )

                return {
                    "nomor": nomor,
                    "status": "SUCCESS",
                    "paket_kritis": paket_kritis,
                    "punya_xtra_combo": punya_xtra_combo,
                }
            elif resp.status == 401 or resp.status == 403:
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"HTTP {resp.status} (API Key KMSP Kadaluarsa / Ditolak)"
                }
            else:
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"HTTP {resp.status}"
                }

    except asyncio.TimeoutError:
        return {
            "nomor": nomor,
            "status": "ERROR",
            "pesan": "Timeout (Server KMSP lambat)",
        }
    except Exception as e:
        return {
            "nomor": nomor,
            "status": "ERROR",
            "pesan": f"Gagal terkoneksi: {str(e)}",
        }
