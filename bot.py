import asyncio
import logging
import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from web_checker import fetch_single_nomor_async

# ==============================================================================
# KONFIGURASI BOT
# ==============================================================================
BOT_TOKEN = "8702246699:AAHbVnZqmrlH4Eku29gzArtEZR05YjbTD5E"

DAFTAR_NOMOR_XL = []
MINTA_NOMOR = 1

logging.basicConfig(level=logging.INFO)


# ==============================================================================
# HANDLER COMMAND & MENU
# ==============================================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton(
                "📝 Cek Kuota Massal", callback_data="cek_massal"
            )
        ],
        [
            InlineKeyboardButton(
                "➕ Tambah Nomor", callback_data="tambah_nomor"
            ),
            InlineKeyboardButton(
                "📋 List Nomor", callback_data="list_nomor"
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    pesan = (
        "🤖 **Bot Pemantau Kuota XL/AXIS**\n\n"
        f"Jumlah Nomor Dipantau: **{len(DAFTAR_NOMOR_XL)} Nomor**\n\n"
        "Fitur Pengecekan:\n"
        "1. Filter 5 Paket Bonus (WA, FB, IG, YT, TikTok) **< 0.5 GB**\n"
        "2. Deteksi Nomor **Tanpa Paket Xtra Combo**"
    )

    if update.message:
        await update.message.reply_text(
            pesan, parse_mode="Markdown", reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            pesan, parse_mode="Markdown", reply_markup=reply_markup
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "cek_massal":
        if not DAFTAR_NOMOR_XL:
            await query.edit_message_text(
                "❌ Belum ada nomor tersimpan. Silakan tambah nomor terlebih dahulu."
            )
            return

        total_nomor = len(DAFTAR_NOMOR_XL)
        results = []

        # Menggunakan aiohttp standard
        async with aiohttp.ClientSession() as session:
            for idx, nomor in enumerate(DAFTAR_NOMOR_XL, 1):
                try:
                    await query.edit_message_text(
                        f"⏳ **Memproses Pengecekan ({idx}/{total_nomor})...**\n\n"
                        f"📱 Sedang mengecek: `{nomor}`",
                        parse_mode="Markdown",
                    )
                except Exception:
                    pass

                res = await fetch_single_nomor_async(session, nomor)
                results.append(res)
                await asyncio.sleep(0.5)

        pesan_hasil = "📝 **List 1 (Sisa Kuota 5 App < 0.5 GB)**\n\n"
        ada_paket_kritis = False

        for res in results:
            if res["status"] == "SUCCESS":
                list_kritis = res["paket_kritis"]
                if list_kritis:
                    ada_paket_kritis = True
                    nomor_display = res["nomor"]
                    if nomor_display.startswith("0"):
                        nomor_display = "62" + nomor_display[1:]

                    pesan_hasil += f"• **{nomor_display}** detail kuota:\n"
                    for pkt in list_kritis:
                        pesan_hasil += (
                            f" - {pkt['sisa_gb']:.2f}GB | {pkt['nama_paket']}\n"
                        )
                    pesan_hasil += "\n"
            else:
                pesan_hasil += f"• **{res['nomor']}**: ❌ {res['pesan']}\n\n"

        if not ada_paket_kritis:
            pesan_hasil += "✅ _Semua paket bonus > 0.5 GB / Aman._\n\n"

        pesan_hasil += "-----------------------------------\n\n"

        pesan_hasil += "🚫 **List 2 (Tanpa Paket Xtra Combo)**\n\n"
        tanpa_xtra_combo = []

        for res in results:
            if res["status"] == "SUCCESS" and not res.get(
                "punya_xtra_combo", False
            ):
                nomor_display = res["nomor"]
                if nomor_display.startswith("0"):
                    nomor_display = "62" + nomor_display[1:]
                tanpa_xtra_combo.append(nomor_display)

        if tanpa_xtra_combo:
            for no in tanpa_xtra_combo:
                pesan_hasil += f"• `{no}` (Tidak ada Xtra Combo)\n"
        else:
            pesan_hasil += "✅ _Semua nomor memiliki paket Xtra Combo._"

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔄 Cek Ulang", callback_data="cek_massal"
                )
            ],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_utama")],
        ]
        await query.edit_message_text(
            pesan_hasil,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif query.data == "list_nomor":
        if not DAFTAR_NOMOR_XL:
            pesan = "📋 **Daftar Nomor Dipantau:**\n\n_Belum ada nomor tersimpan._"
        else:
            pesan = "📋 **Daftar Nomor Dipantau:**\n\n"
            for idx, no in enumerate(DAFTAR_NOMOR_XL, 1):
                pesan += f"{idx}. `{no}`\n"

        keyboard = [
            [
                InlineKeyboardButton(
                    "➕ Tambah Nomor", callback_data="tambah_nomor"
                )
            ],
            [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_utama")],
        ]
        await query.edit_message_text(
            pesan,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ==============================================================================
# HANDLER INPUT NOMOR MASSAL
# ==============================================================================
async def mulai_tambah(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📱 **Input Nomor XL/AXIS (Massal)**\n\n"
        "Kirim nomor-nomor yang ingin ditambahkan **dipisahkan dengan tanda koma ( , )**.\n\n"
        "Contoh:\n"
        "`087735470478, 087735470466, 087747987646`",
        parse_mode="Markdown",
    )
    return MINTA_NOMOR


async def simpan_nomor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teks_input = update.message.text.strip()
    list_raw_nomor = teks_input.split(",")

    nomor_berhasil = []
    nomor_duplikat = []
    nomor_gagal = []

    for item in list_raw_nomor:
        nomor = item.strip()
        if nomor.isdigit() and nomor.startswith("08"):
            if nomor not in DAFTAR_NOMOR_XL:
                DAFTAR_NOMOR_XL.append(nomor)
                nomor_berhasil.append(nomor)
            else:
                nomor_duplikat.append(nomor)
        elif nomor:
            nomor_gagal.append(nomor)

    pesan_laporan = "📋 **Hasil Penambahan Nomor:**\n\n"

    if nomor_berhasil:
        pesan_laporan += f"✅ **Berhasil Ditambahkan ({len(nomor_berhasil)}):**\n"
        pesan_laporan += (
            ", ".join([f"`{no}`" for no in nomor_berhasil]) + "\n\n"
        )

    if nomor_duplikat:
        pesan_laporan += f"ℹ️ **Sudah Ada ({len(nomor_duplikat)}):**\n"
        pesan_laporan += (
            ", ".join([f"`{no}`" for no in nomor_duplikat]) + "\n\n"
        )

    if nomor_gagal:
        pesan_laporan += f"❌ **Format Tidak Valid ({len(nomor_gagal)}):**\n"
        pesan_laporan += f"_Pesan: {', '.join(nomor_gagal)}_\n\n"

    pesan_laporan += f"Total nomor tersimpan: **{len(DAFTAR_NOMOR_XL)} Nomor**."

    keyboard = [
        [
            InlineKeyboardButton(
                "📝 Cek Kuota Massal", callback_data="cek_massal"
            )
        ],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu_utama")],
    ]

    await update.message.reply_text(
        pesan_laporan,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ConversationHandler.END


# ==============================================================================
# MAIN FUNCTION
# ==============================================================================
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(mulai_tambah, pattern="^tambah_nomor$")
        ],
        states={
            MINTA_NOMOR: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, simpan_nomor
                )
            ]
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^menu_utama$"))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("🚀 Bot Pemantau Kuota & Xtra Combo running...")
    app.run_polling()
    
