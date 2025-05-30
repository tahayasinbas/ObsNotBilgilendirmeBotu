from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from FirefoxNotBilgilendirme import ObsNotBilgilendirmeBot # Selenium botunuzun dosya adı
from Bilgiler import KullaniciAd, Sifre # Kullanıcı adı ve şifrenizin olduğu dosya
import asyncio
import concurrent.futures
import copy
import json
import os # PREVIOUS_DERS_BILGILERI_FILE için dosya yolu oluşturmada kullanılabilir

# --- YAPILANDIRMA ---
TOKEN = "1234567890:AAFYkPDZDqanXa1y-hTClq7OzM1S47SPkQw"
# Önceki notları kaydetmek için dosya adı (script ile aynı dizinde olacak)
PREVIOUS_DERS_BILGILERI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "previous_ders_bilgileri.json")
CHAT_ID = 1234567890 # KENDİ TELEGRAM CHAT ID'NİZİ GİRİN (bildirimler için)
# --- /YAPILANDIRMA ---

# Global değişkenler
previous_ders_bilgileri = None # Başlangıçta None, dosyadan yüklenecek

def load_previous_ders_bilgileri():
    """Önceki ders bilgilerini JSON dosyasından yükler."""
    try:
        with open(PREVIOUS_DERS_BILGILERI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"'{PREVIOUS_DERS_BILGILERI_FILE}' bulunamadı, ilk çalıştırma olabilir.")
        return None
    except json.JSONDecodeError:
        print(f"'{PREVIOUS_DERS_BILGILERI_FILE}' dosyasında format hatası var, sıfırlanıyor.")
        return None
    except Exception as e:
        print(f"Önceki ders bilgileri yüklenirken hata oluştu: {e}")
        return None

def save_previous_ders_bilgileri(data):
    """Ders bilgilerini JSON dosyasına kaydeder."""
    try:
        with open(PREVIOUS_DERS_BILGILERI_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4) # indent=4 ile daha okunaklı JSON
            print(f"Ders bilgileri '{PREVIOUS_DERS_BILGILERI_FILE}' dosyasına kaydedildi.")
    except Exception as e:
        print(f"Ders bilgileri dosyasına yazılamadı: {e}")

def get_notlar_sync(max_retries=3): # Fonksiyon adını sync olarak değiştirdim, çünkü blocking
    """Selenium botunu çalıştırır ve ders bilgilerini alır."""
    attempt = 0
    current_bot_instance = None
    while attempt < max_retries:
        try:
            print(f"Not alma denemesi {attempt + 1}/{max_retries}...")
            current_bot_instance = ObsNotBilgilendirmeBot(KullaniciAd, Sifre)
            current_bot_instance.Calistir() # Bu metod DersBilgi'yi doldurur veya hata fırlatır
            # DersBilgi'de error varsa, onu da döndürürüz.
            print(f"Notlar çekildi: {current_bot_instance.DersBilgi}")
            return current_bot_instance.DersBilgi, None # Başarılı: (ders_bilgileri, None)
        except Exception as e:
            attempt += 1
            print(f"Deneme {attempt}/{max_retries} başarısız: {e}")
            if current_bot_instance and hasattr(current_bot_instance, 'DersBilgi') and current_bot_instance.DersBilgi.get("error"):
                # Selenium botu kendi içinde bir hata yakalayıp DersBilgi'ye eklediyse
                error_detail = current_bot_instance.DersBilgi.get("error")
                if attempt == max_retries:
                    return None, f"Tüm denemeler başarısız. Son hata: {error_detail or str(e)}"
            elif attempt == max_retries:
                return None, f"Tüm denemeler başarısız. Son hata: {str(e)}"
        finally:
            if current_bot_instance and hasattr(current_bot_instance, 'driver') and current_bot_instance.driver:
                try:
                    current_bot_instance.driver.quit()
                    print("Selenium WebDriver kapatıldı.")
                except Exception as eq:
                    print(f"Selenium WebDriver kapatılırken hata: {eq}")
    return None, "Bilinmeyen bir hata oluştu (get_notlar_sync)." # Bu satıra normalde ulaşılmamalı

def format_ders_bilgileri(ders_bilgileri):
    """Alınan ders bilgilerini Telegram mesajı için formatlar."""
    # Case 1: ders_bilgileri None veya tamamen boş (veya beklenmedik bir tipte)
    if not ders_bilgileri or not isinstance(ders_bilgileri, dict):
        return "ℹ️ Henüz ders notu bilgisi alınamadı veya ders bulunamadı."

    # Case 2: Selenium scriptinden gelen doğrudan bir hata mesajı varsa
    if "error" in ders_bilgileri:
        return f"⚠️ Hata: {ders_bilgileri['error']}"

    # Case 3: Sadece bilgi mesajı varsa (örneğin, not tablosu boş)
    # ve başka ders verisi yoksa.
    actual_course_keys = [k for k in ders_bilgileri if k not in ["info", "error"]]
    if "info" in ders_bilgileri and not actual_course_keys:
        return f"ℹ️ Bilgi: {ders_bilgileri['info']}"
        
    mesaj_parts = ["--- DERS NOTLARI ---"]
    processed_ders_count = 0

    for ders, bilgiler in ders_bilgileri.items():
        if ders in ["error", "info"]:  # Meta anahtarları atla
            continue
        
        if not isinstance(bilgiler, dict): # Her dersin bilgisinin sözlük olması beklenir
            print(f"Uyarı: '{ders}' için not bilgileri beklenmedik formatta: {bilgiler}")
            continue

        part = f"\n📘 Ders: {ders}\n"
        part += f"📝 Vize: {bilgiler.get('Vize', 'Girilmedi')}\n"
        part += f"📝 Final: {bilgiler.get('Final', 'Girilmedi')}\n"
        
        proje_notu = bilgiler.get('Proje', 'Girilmedi')
        if proje_notu and proje_notu != "Girilmedi": # Sadece girilmişse göster
            part += f"🛠️ Proje: {proje_notu}\n"
            
        odev_notu = bilgiler.get('Odev', 'Girilmedi') # Selenium scripti 'Odev' sağlıyor olmalı
        if odev_notu and odev_notu != "Girilmedi": # Sadece girilmişse göster
            part += f"✍️ Ödev: {odev_notu}\n"
            
        part += f"📊 Ortalama: {bilgiler.get('Ortalama', 'Girilmedi')}\n"
        part += f"🎓 Harf Notu: {bilgiler.get('HarfNotu', 'Girilmedi')}\n"
        part += f"📌 Durum: {bilgiler.get('Durum', 'Girilmedi')}\n"
        mesaj_parts.append(part)
        processed_ders_count += 1
        
    if processed_ders_count == 0:
        # Bu durum, ders_bilgileri'nin boş olmadığı, 'error' veya 'info' anahtarı içermediği (ya da içerse bile başka anahtar olmadığı)
        # ancak hiçbir dersin işlenmediği anlamına gelir. Örn: ders_bilgileri = {"meta_veri": "değer"} gibi beklenmedik bir durum.
        # Ya da Selenium botu boş bir {} döndürdüyse ve ilk 'if not ders_bilgileri' koşulundan geçtiyse.
        return "ℹ️ Gösterilecek ders notu bulunamadı."
        
    return "".join(mesaj_parts)

async def notlar_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/notlar komutunu işler."""
    user_chat_id = update.message.chat_id
    await update.message.reply_text("🔄 Notlar kontrol ediliyor... Lütfen bekleyin...")
    
    try:
        # get_notlar_sync blocking olduğu için ThreadPoolExecutor ile çalıştır
        with concurrent.futures.ThreadPoolExecutor() as executor:
            ders_bilgileri, error = await asyncio.get_event_loop().run_in_executor(
                executor, get_notlar_sync
            )
        
        if error: # Eğer get_notlar_sync hata döndürdüyse
            await update.message.reply_text(f"⚠️ Hata oluştu: {error}")
            return
            
        mesaj = format_ders_bilgileri(ders_bilgileri)
        await update.message.reply_text(mesaj)
    except Exception as e:
        print(f"/notlar komutunda genel hata: {e}")
        await update.message.reply_text(f"⚠️ Beklenmedik bir hata oluştu: {e}")

async def background_not_kontrol(app_ref: ApplicationBuilder): # app yerine app_ref
    """Arka planda periyodik olarak notları kontrol eder ve değişiklik varsa bildirir."""
    global previous_ders_bilgileri # Globaldeki previous_ders_bilgileri'ni kullan

    # Bot ilk çalıştığında, eğer CHAT_ID ayarlıysa bir başlangıç mesajı gönder
    if CHAT_ID: # Sadece CHAT_ID tanımlıysa başlangıç mesajı gönder
      try:
        await app_ref.bot.send_message(chat_id=CHAT_ID, text="✅ Not kontrol sistemi arka planda başlatıldı. (Her 5 dakikada bir kontrol edilecektir)")
      except Exception as e:
        print(f"Başlangıç mesajı gönderilemedi (CHAT_ID: {CHAT_ID}): {e}")
    else:
        print("UYARI: Arka plan bildirimleri için CHAT_ID ayarlanmamış.")
        return # CHAT_ID yoksa bu fonksiyonun devam etmesinin anlamı yok

    while True:
        print("Arka plan not kontrolü başlıyor...")
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                current_ders_bilgileri, error = await asyncio.get_event_loop().run_in_executor(
                    executor, get_notlar_sync
                )
            
            if error:
                print(f"Hata oluştu (arka plan kontrol): {error}")
                await app_ref.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Notlar çekilirken hata oluştu (arka plan): {error}")
            elif current_ders_bilgileri: # Sadece geçerli veri varsa işlem yap
                if previous_ders_bilgileri is None: # İlk çalıştırma veya dosya yoksa
                    print("İlk defa notlar çekildi, kaydediliyor...")
                    previous_ders_bilgileri = copy.deepcopy(current_ders_bilgileri)
                    save_previous_ders_bilgileri(previous_ders_bilgileri)
                # Hem current_ders_bilgileri hem de previous_ders_bilgileri "error" anahtarı içermiyorsa karşılaştır.
                elif not current_ders_bilgileri.get("error") and not previous_ders_bilgileri.get("error") and \
                     current_ders_bilgileri != previous_ders_bilgileri:
                    print("Notlarda değişiklik tespit edildi!")
                    await app_ref.bot.send_message(chat_id=CHAT_ID, text="🔔 Notlarınızda güncelleme var!")
                    
                    # Değişiklikleri daha detaylı göstermek için (opsiyonel)
                    # diff_message = compare_grades(previous_ders_bilgileri, current_ders_bilgileri)
                    # await app_ref.bot.send_message(chat_id=CHAT_ID, text=diff_message)
                    
                    formatted_message = format_ders_bilgileri(current_ders_bilgileri)
                    await app_ref.bot.send_message(chat_id=CHAT_ID, text=formatted_message)
                    
                    previous_ders_bilgileri = copy.deepcopy(current_ders_bilgileri)
                    save_previous_ders_bilgileri(previous_ders_bilgileri)
                else:
                    print("Notlarda değişiklik yok veya bir önceki/şimdiki notta hata var.")
            else:
                print("Arka plan kontrolünde ders bilgisi alınamadı (None döndü).")

        except Exception as e:
            print(f"Arka plan görevinde beklenmedik hata: {e}")
            try: # Hata durumunda da mesaj göndermeye çalış
                await app_ref.bot.send_message(chat_id=CHAT_ID, text=f"⚠️ Arka plan not kontrolünde kritik bir hata oluştu: {e}")
            except Exception as send_err:
                print(f"Kritik hata mesajı gönderilemedi: {send_err}")
        
        await asyncio.sleep(300)  # 5 dakika (300 saniye) bekle

async def main():
    """Botu başlatır ve çalıştırır."""
    global previous_ders_bilgileri
    previous_ders_bilgileri = load_previous_ders_bilgileri() # Bot başlarken yükle

    # ApplicationBuilder ile botu oluştur
    # `Application` nesnesini `app_ref` olarak `background_not_kontrol`'e geçireceğiz.
    application = ApplicationBuilder().token(TOKEN).build()

    # Komutları ekle
    application.add_handler(CommandHandler("notlar", notlar_command_handler))
    
    print("Bot çalışıyor... Telegram üzerinden /notlar komutunu kullanabilirsiniz.")
    if not CHAT_ID:
        print("UYARI: Arka plan bildirimleri için CHAT_ID ayarlanmamış. Sadece /notlar komutu çalışacaktır.")

    # Arka plan görevini başlat (sadece CHAT_ID ayarlıysa mantıklı)
    if CHAT_ID:
      asyncio.create_task(background_not_kontrol(application)) # application'ı doğrudan ver
    
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True) # Bot çevrimdışı iken gelen mesajları atla
        print("Bot polling modunda başlatıldı. Kapatmak için Ctrl+C.")
        # Botun sonsuza kadar çalışmasını sağla (veya bir durdurma sinyali alana kadar)
        await asyncio.Event().wait() 
    except KeyboardInterrupt:
        print("Bot manuel olarak durduruluyor...")
    except Exception as e:
        print(f"Botun ana çalışma döngüsünde hata: {e}")
    finally:
        if hasattr(application, 'updater') and application.updater and application.updater.running:
            await application.updater.stop()
        if hasattr(application, 'running') and application.running: # Check if running before stopping
            await application.stop()
        await application.shutdown()
        print("Bot kapatıldı.")

if __name__ == "__main__":
    # CHAT_ID'nin ayarlı olup olmadığını kontrol et
    if not TOKEN == "1234567890:AAFYkPDZDqanXa1y-hTClq7OzM1S47SPkQw":
        print("HATA: Lütfen scriptteki TOKEN değişkenine Telegram Bot Token'ınızı girin.")
    elif CHAT_ID == 000000000: # CHAT_ID için varsayılan değer 0 ise veya placeholder ise
        print("UYARI: CHAT_ID ayarlanmamış. Arka plan bildirimleri çalışmayacak.")
        print("Sadece /notlar komutu kullanılabilir olacak.")
        # CHAT_ID olmadan da botun çalışmasına izin verilebilir, kullanıcı /notlar ile sorgu yapabilir.
        asyncio.run(main())
    else:
        asyncio.run(main())
