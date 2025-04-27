from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from NotBilgilendirmeBot import ObsNotBilgilendirmeBot
from Bilgiler import KullaniciAd, Sifre
import asyncio
import concurrent.futures
import copy
import json

TOKEN = "Telegram Bot Tokenunuz"
PREVIOUS_DERS_BILGILERI_FILE = "previous_ders_bilgileri.json"
CHAT_ID = 12345678  # Kendi chat_id'niz

background_task = None

def load_previous_ders_bilgileri():
    try:
        with open(PREVIOUS_DERS_BILGILERI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_previous_ders_bilgileri(data):
    try:
        with open(PREVIOUS_DERS_BILGILERI_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Önceki notlar dosyasına yazılamadı: {e}")

previous_ders_bilgileri = load_previous_ders_bilgileri()  # Önceki notlar dosyadan okunacak

def get_notlar(max_retries=3):
    attempt = 0
    while attempt < max_retries:
        try:
            bot = ObsNotBilgilendirmeBot(KullaniciAd, Sifre)
            bot.Calistir()
            return bot.DersBilgi, None
        except Exception as e:
            attempt += 1
            print(f"Deneme {attempt}/{max_retries} başarısız: {e}")
            if attempt == max_retries:
                return None, str(e)
        finally:
            try:
                bot.driver.quit()
            except:
                pass

async def notlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Notlar kontrol ediliyor... Lütfen bekleyin...")
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            ders_bilgileri, error = await asyncio.get_event_loop().run_in_executor(
                executor, get_notlar
            )
        
        if error:
            await update.message.reply_text(f"⚠️ Hata oluştu: {error}")
            return
            
        mesaj = format_ders_bilgileri(ders_bilgileri)
        await update.message.reply_text(mesaj)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Hata oluştu: {e}")

def format_ders_bilgileri(ders_bilgileri):
    mesaj = "--- DERS NOTLARI ---\n"
    for ders, bilgiler in ders_bilgileri.items():
        if ders == "DersAdi":
            continue
        mesaj += f"\n📘 Ders: {ders}\n"
        mesaj += f"📝 Vize: {bilgiler.get('Vize', 'Girilmedi')}\n"
        mesaj += f"📝 Final: {bilgiler.get('Final', 'Girilmedi')}\n"
        if 'Proje' in bilgiler and bilgiler['Proje'] != "Girilmedi":
            mesaj += f"🛠️ Proje: {bilgiler['Proje']}\n"
        mesaj += f"📊 Ortalama: {bilgiler.get('Ortalama', 'Girilmedi')}\n"
        mesaj += f"🎓 Harf Notu: {bilgiler.get('HarfNotu', 'Girilmedi')}\n"
        mesaj += f"📌 Durum: {bilgiler.get('Durum', 'Girilmedi')}\n"
    return mesaj

async def background_not_kontrol(app, chat_id):
    global previous_ders_bilgileri
    await app.bot.send_message(chat_id=chat_id, text="✅ Not kontrol sistemi başlatıldı.")

    while True:
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                ders_bilgileri, error = await asyncio.get_event_loop().run_in_executor(
                    executor, get_notlar
                )
            if error:
                print(f"Hata oluştu (background kontrol): {error}")
                await app.bot.send_message(chat_id=chat_id, text=f"⚠️ Hata oluştu: {error}")
            else:
                if previous_ders_bilgileri is None:
                    previous_ders_bilgileri = copy.deepcopy(ders_bilgileri)
                    save_previous_ders_bilgileri(previous_ders_bilgileri)
                elif ders_bilgileri != previous_ders_bilgileri:
                    await app.bot.send_message(chat_id=chat_id, text="🆕 Yeni bir not güncellemesi tespit edildi!")
                    mesaj = format_ders_bilgileri(ders_bilgileri)
                    await app.bot.send_message(chat_id=chat_id, text=mesaj)
                    previous_ders_bilgileri = copy.deepcopy(ders_bilgileri)
                    save_previous_ders_bilgileri(previous_ders_bilgileri)
        except Exception as e:
            print(f"Background task hatası: {e}")
            await app.bot.send_message(chat_id=chat_id, text=f"⚠️ Background task hatası: {e}")
        await asyncio.sleep(300)  # 5 dakika

def start_background_task(app, chat_id):
    global background_task
    if background_task is None or background_task.done():
        background_task = asyncio.create_task(background_not_kontrol(app, chat_id))

def stop_background_task():
    global background_task
    if background_task and not background_task.done():
        background_task.cancel()

async def post_init(app):
    # Arka plan task'ı başlat
    asyncio.create_task(background_not_kontrol(app, CHAT_ID))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("notlar", notlar))
    print("Bot çalışıyor... Telegram üzerinden /notlar yazabilirsin.")

    async def main():
        asyncio.create_task(background_not_kontrol(app, CHAT_ID))
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()  # Sonsuza kadar bekler, bot kapanmaz

    asyncio.run(main())