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
    url = "https://kuota.store/index.php"
    params = {"action": "cek_kuota", "msisdn": nomor}

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://kuota.store/",
        "X-Requested-With": "XMLHttpRequest",
    }

    timeout = aiohttp.ClientTimeout(total=8)

    try:
        async with session.get(
            url, params=params, headers=headers, timeout=timeout
        ) as resp:
            if resp.status == 200:
                try:
                    data = await resp.json(content_type=None)
                except Exception:
                    text_resp = await resp.text()
                    data = json.loads(text_resp)

                if (
                    not isinstance(data, dict)
                    or data.get("status") != "success"
                ):
                    return {
                        "nomor": nomor,
                        "status": "ERROR",
                        "pesan": "Server web lambat / gagal merespons",
                    }

                paket_kritis = []
                punya_xtra_combo = False

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

                            if any(
                                target in pkg_name_lower
                                for target in EXACT_TARGET_PACKAGES
                            ):
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
            else:
                return {
                    "nomor": nomor,
                    "status": "ERROR",
                    "pesan": f"HTTP {resp.status}",
                }

    except asyncio.TimeoutError:
        return {
            "nomor": nomor,
            "status": "ERROR",
            "pesan": "Timeout (Server kuota.store lambat)",
        }
    except Exception as e:
        return {
            "nomor": nomor,
            "status": "ERROR",
            "pesan": f"Gagal terkoneksi: {str(e)}",
        }
