from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageFilter, ImageOps
import cv2
import numpy as np
from time import sleep
import re
import os
from Bilgiler import KullaniciAd,Sifre,Url

DersBilgi = {"DersAdi":{"FinalNot":"","Vize":"","HarfNotu":"","Durum":"","Ortalama":"" }}
Liste = []
# Chrome driver yolu kontrol edilmeli ve gerekirse değiştirilmeli
webdriver_service = Service("C:\Drivers\chromedriver-win64\chromedriver-win64\chromedriver.exe")

class ObsNotBilgilendirmeBot:
    def __init__(self, Isim, Sifre):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        self.chrome_options.add_argument("--start-maximized")  # Pencereyi maksimize et
        self.driver = webdriver.Chrome(service=webdriver_service, options=self.chrome_options)
        self.driver.implicitly_wait(10)  # Daha uzun bekleme süresi
        self.Isim = Isim
        self.Sifre = Sifre
        self.actions = ActionChains(self.driver)
        self.DersBilgi = {"DersAdi":{"FinalNot":"","Vize":"","HarfNotu":"","Durum":"","Ortalama":"" }}

    def scroll_to_bottom(self):
        """Sayfanın en altına kaydırır"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(1)
    def scroll_to_element(self, element):
        """Belirtilen elemente kaydırır"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            sleep(1)
        except Exception as e:
            print(f"Elemente kaydırma başarısız: {e}")
    def click_element_safely(self, element):
        """Elemente güvenli şekilde tıklar"""
        try:
            # Önce elementin görünür olmasını bekle
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of(element)
            )
            
            # Elemente scroll yap
            self.scroll_to_element(element)
            
            # ActionChains yerine direkt element click ile dene
            element.click()
        except Exception as e:
            print(f"Click with direct method failed: {e}")
            try:
                # JavaScript ile tıklama dene
                self.driver.execute_script("arguments[0].click();", element)
            except Exception as e:
                print(f"Click with JS failed: {e}")
                # Son çare olarak ActionChains kullan
                self.actions.move_to_element(element).click().perform()

 



    def CaptchaResim(self):
        # CAPTCHA elementini bul
        CaptchaElement = self.driver.find_element(By.ID, "imgCaptchaImg")
        
        # CAPTCHA'nın src URL'sini al
        captcha_src = CaptchaElement.get_attribute("src")
        
        # JavaScript ile sayfaya geçici bir büyütülmüş görüntü ekle
        enhance_script = f"""
        // Mevcut görüntüyü gizle
        arguments[0].style.display = 'none';
        
        // Yeni, büyütülmüş görüntü oluştur
        var enhancedImg = document.createElement('img');
        enhancedImg.src = "{captcha_src}";
        enhancedImg.id = "enhancedCaptcha";
        enhancedImg.style.width = "300px"; // Genişliği ayarla
        enhancedImg.style.border = "2px solid blue";
        enhancedImg.style.margin = "20px";
        
        // Yeni görüntüyü eskisinin yanına ekle
        arguments[0].parentNode.insertBefore(enhancedImg, arguments[0]);
        """
        
        self.driver.execute_script(enhance_script, CaptchaElement)
        sleep(2)
        
        # Büyütülmüş görüntüyü bul ve ekran görüntüsünü al
        enhanced_element = self.driver.find_element(By.ID, "enhancedCaptcha")
        enhanced_element.screenshot("cropped_captcha.png")
        
        # Temizlik: Eklenen elementi kaldır ve orijinali geri göster
        self.driver.execute_script("""
        document.getElementById('enhancedCaptcha').remove();
        arguments[0].style.display = '';
        """, CaptchaElement)
    
    
    




    def ObsLogin(self,Okul_Url):
        self.driver.get(Okul_Url)
        OgrenciGirisHref = self.driver.find_element(By.XPATH, "//a[text() ='Öğrenci Girişi']")
        self.click_element_safely(OgrenciGirisHref)
        sleep(3)
        
        KullaniciAdInput = self.driver.find_element(By.XPATH, "//input[@title = 'Kullanıcı Adı']")
        KullaniciAdInput.send_keys(self.Isim)
        sleep(2)
        
        SifreInput = self.driver.find_element(By.XPATH, "//input[@type = 'password']")
        SifreInput.send_keys(self.Sifre)
        sleep(2)
        
        # CAPTCHA resmini yakala
        self.CaptchaResim()
        # CAPTCHA çözümü için resimonisle.py çalıştır
        os.system("python resimonisle.py")

        # Sonuç dosyasından CAPTCHA sonucunu al
        with open("captcha_sonuc.txt", "r", encoding="utf-8") as f:
            captcha_sonuc = f.read().strip()
        
        ToplamInput = self.driver.find_element(By.XPATH, "//input[@title = 'Sayıların Toplamını Giriniz']")
        ToplamInput.send_keys(captcha_sonuc)
        sleep(1)

        GirisBut = self.driver.find_element(By.XPATH,"//a[@id ='btnLogin']")
        self.click_element_safely(GirisBut)
        sleep(3)

    def MenulerIslemleri(self):
        try:
            # Menü butonunu bul
            MenuBut = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//i[@class = 'fal fa-map-marked-alt']/.."))
            )
            self.click_element_safely(MenuBut)
            sleep(3)
            
            # Not listesi butonunu bul
            NotMenuBut = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//p[text() ='Not Listesi']/.."))
            )
            self.click_element_safely(NotMenuBut)
            sleep(3)
            
            # iframe'e geçiş
            try:
                iframe = self.driver.find_element(By.ID, "IFRAME1")
                self.driver.switch_to.frame(iframe)
                print("iframe'e geçiş yapıldı")
            except:
                print("iframe bulunamadı, devam ediliyor...")
            
            # Tablo satırlarını bul
            Tablolar = self.driver.find_elements(By.XPATH, '//*[@id="grd_not_listesi"]/tbody/tr')
            
            if len(Tablolar) > 0:
                # Başlık satırını atla
                if len(Tablolar) > 1:
                    satir_baslangic = 1  # İlk satır başlık olabilir
                else:
                    satir_baslangic = 0
                    
                # Her satırı işle
                for i in range(satir_baslangic, len(Tablolar)):
                    Tablo = Tablolar[i]
                    TabloIcerikler = Tablo.find_elements(By.XPATH, "./td")
                    
                    if len(TabloIcerikler) < 8:
                        print(f"Bu satırda yeterli sütun yok, atlanıyor...")
                        continue
                        
                    DersAdi = TabloIcerikler[2].text
                    print(f"İşlenen ders: {DersAdi}")

                    # Notları içeren hücreyi al
                    NotHucresi = TabloIcerikler[4]
                    
                    # Varsayılan değerler
                    Vize = "Girilmedi"
                    Final = "Girilmedi"
                    Proje = "Girilmedi"
                    
                    # Not metnini al
                    NotMetni = NotHucresi.text
                    
                    # Vize notunu ara
                    vize_match = re.search(r'Vize\s*:\s*(\d+)', NotMetni)
                    if vize_match:
                        Vize = vize_match.group(1)
                        
                    # Final notunu ara
                    final_match = re.search(r'Final\s*:\s*(\d+)', NotMetni)
                    if final_match:
                        Final = final_match.group(1)
                        
                    # Proje notunu ara (eğer varsa)
                    proje_match = re.search(r'Proje\s*:\s*(\d+)', NotMetni)
                    if proje_match:
                        Proje = proje_match.group(1)

                    Ortalama = TabloIcerikler[5].text.strip() or "Girilmedi"
                    HarfNotu = TabloIcerikler[6].text.strip() or "Girilmedi"
                    Durum = TabloIcerikler[7].text.strip() or "Girilmedi"

                    # Sözlükte dersi yoksa ekle
                    if DersAdi not in self.DersBilgi:
                        self.DersBilgi[DersAdi] = {}

                    self.DersBilgi[DersAdi]["Vize"] = Vize
                    self.DersBilgi[DersAdi]["Final"] = Final
                    self.DersBilgi[DersAdi]["Proje"] = Proje
                    self.DersBilgi[DersAdi]["Ortalama"] = Ortalama
                    self.DersBilgi[DersAdi]["HarfNotu"] = HarfNotu
                    self.DersBilgi[DersAdi]["Durum"] = Durum
            else:
                print("Tablo satırları bulunamadı!")
                
            # Ana frame'e geri dön
            self.driver.switch_to.default_content()
            
        except Exception as e:
            print(f"MenulerIslemleri sırasında hata: {e}")
            
    def NotlariGoruntule(self):
        print("\n--- DERS NOTLARI ---")
        for ders, bilgiler in self.DersBilgi.items():
            if ders == "DersAdi":  # Şablon dersi geç
                continue
            print(f"\nDers: {ders}")
            print(f"Vize: {bilgiler.get('Vize', 'Girilmedi')}")
            print(f"Final: {bilgiler.get('Final', 'Girilmedi')}")
            if 'Proje' in bilgiler and bilgiler['Proje'] != "Girilmedi":
                print(f"Proje: {bilgiler['Proje']}")
            print(f"Ortalama: {bilgiler.get('Ortalama', 'Girilmedi')}")
            print(f"Harf Notu: {bilgiler.get('HarfNotu', 'Girilmedi')}")
            print(f"Durum: {bilgiler.get('Durum', 'Girilmedi')}")

    def Calistir(self):
        try:
            self.ObsLogin(Url)
            sleep(5)
            GirisSonuclar = self.driver.find_elements(By.XPATH,"//span[@id = 'lblSonuclar']")
            if not GirisSonuclar:  # Eğer boşsa (yani hata mesajı yoksa)
                self.MenulerIslemleri()
                self.NotlariGoruntule()
                self.driver.quit()
            else:
                print("Login yapılamadı! Bidaha deneniyor...")
                self.driver.quit()
                raise Exception("Login başarısız oldu.")
        except Exception as e:
            print(f"Hata oluştu: {e}")
            try:
                self.driver.quit()
            except:
                pass
            raise e 
                
           


if __name__ == "__main__":
    # Botu başlat
    ObsBot = ObsNotBilgilendirmeBot(KullaniciAd, Sifre)
    ObsBot.Calistir() 