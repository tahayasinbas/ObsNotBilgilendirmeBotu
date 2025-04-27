# OBS Not Bilgilendirme ve Telegram Botu

Bu proje, üniversitenizin OBS (Öğrenci Bilgi Sistemi) üzerinden notlarınızı otomatik olarak kontrol eden ve güncellemeleri size Telegram üzerinden bildiren bir bottur. Ayrıca, girişteki CAPTCHA doğrulamasını otomatik olarak çözer.

## Özellikler

- OBS'ye otomatik giriş yapar.
- CAPTCHA görselini işler ve otomatik olarak çözer.
- Notlarınızı çeker ve Telegram üzerinden /notlar komutuyla gösterir.
- Notlarda değişiklik olursa Telegram'dan otomatik bildirim gönderir.
- 5 dakikada bir notları kontrol eder (background task).

## Gereksinimler

- Python 3.8+
- ChromeDriver (Chrome sürümünüzle uyumlu)
- Tesseract OCR
- Telegram hesabı ve bot token'ı
- Aşağıdaki Python kütüphaneleri:
  - selenium
  - opencv-python
  - numpy
  - pytesseract
  - pillow
  - python-telegram-bot


## Kurulum

**Sistemi ilk kez çalıştırmak için aşağıdaki adımları sırasıyla uygulayın:**

### 1. Bilgiler.py Dosyasını Doldurun (Zorunlu İlk Adım)

`Bilgiler.py` dosyasındaki kullanıcı adı, şifre ve OBS URL'sini kendi bilgilerinizle doldurun:

```python
KullaniciAd = "kullanici_adiniz"
Sifre = "Sifreniz"
Url = "https://obs./../.edu.tr/"
```

### 2. NotBilgilendirmeBot.py'de ChromeDriver Yolunu Ayarlayın

- Bilgisayarınızda yüklü olan Chrome sürümüne uygun bir ChromeDriver indirin.
- ChromeDriver'ın dosya yolunu `NotBilgilendirmeBot.py` dosyasındaki `webdriver_service` değişkeni ile ayarlayın:

```python
webdriver_service = Service("C:\\Drivers\\chromedriver-win64\\chromedriver.exe")
```

### 3. Tesseract OCR Ayarı

- Bilgisayarınızda Tesseract OCR kurulu olmalıdır.
- Tesseract'ın kurulu olduğu dizini `resimonisle.py` dosyasındaki `TESSERACT_CMD_PATH` değişkeni ile ayarlayın.

### 4. TelegramBot.py'de TOKEN ve CHAT_ID Bilgilerini Girin

- [@BotFather](https://t.me/BotFather) ile bir bot oluşturun ve token alın.
- `TelegramBot.py` dosyasındaki `TOKEN` değişkenine kendi bot tokenınızı girin.
- `CHAT_ID` kısmına kendi Telegram kullanıcı ID'nizi girin (bunu almak için @userinfobot kullanabilirsiniz).

```python
TOKEN = "Telegram Bot Tokenunuz"
CHAT_ID = 12345678  # Kendi chat_id'niz
```

## Kullanım

### 1. Botu Başlatın

```bash
python TelegramBot.py
```

- Bot çalışmaya başlayacak ve Telegram üzerinden `/notlar` komutunu kullanarak notlarınızı görebileceksiniz.
- Notlarda değişiklik olursa otomatik olarak Telegram'dan bildirim alırsınız.

### 2. Manuel Test

Sadece OBS'den not çekmek için:

```bash
python NotBilgilendirmeBot.py
```

---

**Not:** `NotBilgilendirmeBot.py` ve `resimonisle.py` dosyalarını ayrı ayrı çalıştırarak test edebilirsiniz. Özellikle CAPTCHA çözümünü test etmek için `resimonisle.py` dosyasını doğrudan çalıştırabilirsiniz. Kendi OBS sisteminizdeki CAPTCHA formatı farklıysa, `resimonisle.py` içindeki kırpma koordinatlarını (NUM1_CROP_COORDS ve NUM2_CROP_COORDS) kendi görselinize uygun şekilde ayarlamanız gerekmektedir. Doğru çalışması için bu ayarları kendi CAPTCHA'nıza göre düzenleyin.

---

## Dosya Açıklamaları

- `NotBilgilendirmeBot.py`: OBS'ye giriş ve not çekme işlemlerini otomatikleştirir.
- `resimonisle.py`: CAPTCHA görselini işler ve çözer.
- `TelegramBot.py`: Telegram botunu çalıştırır ve notları iletir.
- `Bilgiler.py`: Kullanıcı adı, şifre ve OBS URL bilgilerini içerir.

