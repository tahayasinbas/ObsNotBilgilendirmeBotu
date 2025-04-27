import cv2
import numpy as np
import os
import pytesseract
import re
import operator

# Gerekirse Tesseract yolu
TESSERACT_CMD_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Lütfen kendi Tesseract kurulum yolunuzu buraya girin
if os.path.exists(TESSERACT_CMD_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD_PATH
else:
    print(f"Uyarı: Tesseract yolu bulunamadı: {TESSERACT_CMD_PATH}")

# SABİT KIRPMA KOORDİNATLARI - BU DEĞERLER CAPTCHA'NIZIN FORMATINA GÖRE BELİRLENMİŞTİR!
# (y_başlangıç, y_bitiş, x_başlangıç, x_bitiş)
# Sizin verdiğiniz değerlere göre:
# İlk sayı: y: 7'den 44'e, x: 0'dan 59'a -> (7, 45, 0, 60)
# İkinci sayı: y: 7'den 44'e, x: 87'den 129'a -> (7, 45, 87, 130)
NUM1_CROP_COORDS = (7, 45, 12, 53)
NUM2_CROP_COORDS = (7, 45, 87, 130)


def solve_captcha_fixed_crop_sum(image_path, binary_threshold=145, opening_kernel_size=(2, 2)):
    """
    Görseli işler, sabit koordinatlara göre sayıları kırpar, tanır ve toplar.
    Sadece toplama işlemi olduğunu ve sayıların sabit konumda olduğunu varsayar.
    """
    if not os.path.exists(image_path):
        return None, f"Hata: Görüntü bulunamadı: {image_path}"

    image = cv2.imread(image_path)
    if image is None:
        return None, f"Hata: Görüntü yüklenemedi veya dosya bozuk: {image_path}"

    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Global Eşikleme (Başlangıç noktamız)
        _, binary_img = cv2.threshold(gray, binary_threshold, 255, cv2.THRESH_BINARY_INV)

        # Morfolojik Opening
        kernel = np.ones(opening_kernel_size, np.uint8)
        processed_img = cv2.morphologyEx(binary_img, cv2.MORPH_OPEN, kernel)
        # Tesseract'a gidecek işlenmiş görselimiz hazır

        # İsteğe bağlı: İşlenmiş görseli kaydet (hata ayıklama için)
        # cv2.imwrite('processed_for_fixed_crop.png', processed_img)
        # print("Kaydedildi: processed_for_fixed_crop.png")

    except Exception as e:
        return None, f"Hata: Görsel ön işleme sırasında bir sorun oluştu: {e}"

    # --- Sayıları Sabit Koordinatlara Göre Kırp ve Tanı ---
    num1 = None
    num2 = None

    # Tesseract tek karakter (sadece rakam) konfigürasyonu
    # PSM 10: Tek karakter modu, 0-9 whitelist
    # Belirli bir bölgeyi tanıyacağımız için PSM 10 veya 13 de uygun olabilir.
    # Sadece rakamları istediğimiz için Whitelist çok önemli.
    digit_ocr_config = r'--psm 10 -c tessedit_char_whitelist=0123456789' # Tek karakter modu

    try:
        # Görsel boyutlarını al (kırpma sınırlarını kontrol etmek için)
        height, width = processed_img.shape[:2]

        # --- Birinci Sayıyı Kırp ve Tanı ---
        y1_s, y1_e, x1_s, x1_e = NUM1_CROP_COORDS

        # Kırpma sınırlarını kontrol et
        if y1_s < 0 or y1_e > height or x1_s < 0 or x1_e > width or y1_s >= y1_e or x1_s >= x1_e:
             return None, f"Hata: Birinci sayı için kırpma koordinatları görsel sınırlarının dışında veya geçersiz. Görsel boyutu: {height}x{width}, Kırpma: {NUM1_CROP_COORDS}"

        num1_img = processed_img[y1_s:y1_e, x1_s:x1_e]

        # İsteğe bağlı: Kırpılmış sayı görsellerini kaydet (hata ayıklama için)
        # cv2.imwrite('num1_cropped.png', num1_img)
        # print("Kaydedildi: num1_cropped.png")

        # Tesseract ile birinci sayıyı tanı
        from PIL import Image # PIL/Pillow Image formatı Tesseract için bazen daha iyi
        num1_img_pil = Image.fromarray(num1_img)

        num1_text = pytesseract.image_to_string(num1_img_pil, config=digit_ocr_config).strip()
        print(f"Tanınan 1. sayı (Ham): '{num1_text}'")

        # Tanınan metinden sadece rakamları al ve sayıya çevir
        cleaned_num1_text = re.sub(r'[^0-9]', '', num1_text)
        print(f"Temizlenmiş 1. sayı: '{cleaned_num1_text}'")

        if not cleaned_num1_text:
             return None, f"Hata: Birinci sayı bölgesinden rakam tanınamadı. Ham: '{num1_text}'"
        num1 = int(cleaned_num1_text)


        # --- İkinci Sayıyı Kırp ve Tanı ---
        y2_s, y2_e, x2_s, x2_e = NUM2_CROP_COORDS

        # Kırpma sınırlarını kontrol et
        if y2_s < 0 or y2_e > height or x2_s < 0 or x2_e > width or y2_s >= y2_e or x2_s >= x2_e:
             return None, f"Hata: İkinci sayı için kırpma koordinatları görsel sınırlarının dışında veya geçersiz. Görsel boyutu: {height}x{width}, Kırpma: {NUM2_CROP_COORDS}"

        num2_img = processed_img[y2_s:y2_e, x2_s:x2_e]

        # İsteğe bağlı: Kırpılmış sayı görsellerini kaydet
        # cv2.imwrite('num2_cropped.png', num2_img)
        # print("Kaydedildi: num2_cropped.png")

        # Tesseract ile ikinci sayıyı tanı
        num2_img_pil = Image.fromarray(num2_img)
        num2_text = pytesseract.image_to_string(num2_img_pil, config=digit_ocr_config).strip()
        print(f"Tanınan 2. sayı (Ham): '{num2_text}'")

        # Tanınan metinden sadece rakamları al ve sayıya çevir
        cleaned_num2_text = re.sub(r'[^0-9]', '', num2_text)
        print(f"Temizlenmiş 2. sayı: '{cleaned_num2_text}'")

        if not cleaned_num2_text:
             return None, f"Hata: İkinci sayı bölgesinden rakam tanınamadı. Ham: '{num2_text}'"
        num2 = int(cleaned_num2_text)

        # --- Sayıları Topla (Toplama varsayımı) ---
        result = num1 + num2
        print(f"Varsayılan işlem (Toplama): {num1} + {num2} = {result}")

        return result, "" # Sonuç ve boş hata mesajı

    except pytesseract.TesseractNotFoundError:
         return None, "Hata: Tesseract OCR motoru bulunamadı. Lütfen kurun veya yolunu ayarlayın."
    except ValueError:
        return None, f"Hata: Tanınan metin sayıya dönüştürülemedi. 1. sayı: '{num1_text}', 2. sayı: '{num2_text}'"
    except Exception as e:
        return None, f"Hata: Kırpma, tanıma veya hesaplama sırasında beklenmeyen bir sorun oluştu: {e}"


# Ana çalıştırma bloğu
if __name__ == "__main__":
    image_file = 'cropped_captcha.png' # Orijinal CAPTCHA görselinizi kullandığınızdan emin olun

    # Ön işleme parametreleri
    best_threshold = 145 # Sizin bulduğunuz değer
    best_opening_kernel = (2, 2) # Sizin bulduğunuz kernel boyutu

    # Sabit kırpma koordinatları fonksiyon içinde tanımlanmıştır (NUM1_CROP_COORDS, NUM2_CROP_COORDS)

    print(f"İşleniyor: {image_file} (Global Eşik={best_threshold}, Opening={best_opening_kernel}). Sabit kırpma uygulanıyor.")

    captcha_result, error_message = solve_captcha_fixed_crop_sum( # Fonksiyon adı
        image_file,
        binary_threshold=best_threshold,
        opening_kernel_size=best_opening_kernel
    )

    if error_message:
        print(error_message)
        final_result = -1
    elif captcha_result is not None:
        print(f"Nihai Çözüm: {captcha_result}")
        final_result = captcha_result
    else:
         print("Bilinmeyen bir hata oluştu veya sonuç None döndü.")
         final_result = -1

    try:
        with open("captcha_sonuc.txt", "w", encoding="utf-8") as f:
            f.write(str(final_result))
        print(f"Sonuç ({final_result}) captcha_sonuc.txt dosyasına kaydedildi.")
    except Exception as e:
        print(f"Hata: Sonuç dosyasına yazılamadı: {e}")