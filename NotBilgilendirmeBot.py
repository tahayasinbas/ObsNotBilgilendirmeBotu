from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import re
import os
from Bilgiler import KullaniciAd, Sifre

# WebDriver Manager için detaylı loglamayı açmak isterseniz aşağıdaki satırların yorumunu kaldırabilirsiniz.
# import logging
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('webdriver_manager').setLevel(logging.DEBUG)

class ObsNotBilgilendirmeBot:
    def __init__(self, Isim, Sifre):
        self.chrome_options = Options()
        self.chrome_options.binary_location = "/usr/bin/chromium" # Eğer Chromium kullanıyorsanız ve yolu belirtmek gerekirse

        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        
        try:
            print("DEBUG: ChromeDriver başlatılıyor (webdriver-manager)...")
            # chrome_type="chromium" parametresini Chromium kullanıyorsanız ekleyebilirsiniz.
            # driver_executable_path = ChromeDriverManager(chrome_type="chromium").install() 
            driver_executable_path = ChromeDriverManager().install() # Google Chrome için varsayılan
            print(f"DEBUG: webdriver-manager tarafından kullanılan ChromeDriver yolu: {driver_executable_path}")
            
            service = ChromeService(executable_path=driver_executable_path)
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            print("DEBUG: ChromeDriver başarıyla başlatıldı.")
        except Exception as e:
            print(f"ChromeDriver başlatılırken hata oluştu (webdriver-manager): {e}")
            print("Lütfen internet bağlantınızı, Chrome/Chromium tarayıcınızın kurulu ve güncel olduğundan")
            print("ve webdriver-manager kütüphanesinin güncel olduğundan emin olun.")
            raise 

        self.driver.implicitly_wait(10)
        self.Isim = Isim
        self.Sifre = Sifre
        self.actions = ActionChains(self.driver)
        self.DersBilgi = {} # Ders bilgilerini boş bir sözlük olarak başlat

    def scroll_to_bottom(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(1)

    def scroll_to_element(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            sleep(1)
        except Exception as e:
            print(f"Elemente kaydırma başarısız: {e}")

    def click_element_safely(self, element):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.visibility_of(element)
            )
            self.scroll_to_element(element)
            element.click()
        except Exception as e:
            print(f"Click with direct method failed: {e}, trying JS click.")
            try:
                self.driver.execute_script("arguments[0].click();", element)
            except Exception as e_js:
                print(f"Click with JS failed: {e_js}, trying ActionChains.")
                WebDriverWait(self.driver, 10).until(
                     EC.element_to_be_clickable(element)
                )
                self.actions.move_to_element(element).click().perform()

    def CaptchaResim(self):
        CaptchaElement = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "imgCaptchaImg"))
        )
        captcha_src = CaptchaElement.get_attribute("src")
        
        enhance_script = f"""
        arguments[0].style.display = 'none';
        var enhancedImg = document.createElement('img');
        enhancedImg.src = "{captcha_src}";
        enhancedImg.id = "enhancedCaptcha";
        enhancedImg.style.width = "300px"; 
        enhancedImg.style.border = "2px solid blue";
        enhancedImg.style.margin = "20px";
        arguments[0].parentNode.insertBefore(enhancedImg, arguments[0]);
        """
        self.driver.execute_script(enhance_script, CaptchaElement)
        sleep(1)
        
        enhanced_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "enhancedCaptcha"))
        )
        WebDriverWait(self.driver, 10).until(EC.visibility_of(enhanced_element))
        
        screenshot_path = os.path.join(os.getcwd(), "cropped_captcha.png") 
        try:
            enhanced_element.screenshot(screenshot_path)
            print(f"CAPTCHA ekran görüntüsü {screenshot_path} adresine kaydedildi.")
        except Exception as e:
            print(f"CAPTCHA ekran görüntüsü alınamadı: {e}")
            raise

        self.driver.execute_script("""
        var el = document.getElementById('enhancedCaptcha');
        if (el) el.remove();
        arguments[0].style.display = '';
        """, CaptchaElement)
    
    def ObsLogin(self):
        self.driver.get("https://obs.mu.edu.tr/") 
        
        OgrenciGirisHref = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[text() ='Öğrenci Girişi']"))
        )
        self.click_element_safely(OgrenciGirisHref)
        
        KullaniciAdInput = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@title = 'Kullanıcı Adı']"))
        )
        KullaniciAdInput.send_keys(self.Isim)
        
        SifreInput = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type = 'password']"))
        )
        SifreInput.send_keys(self.Sifre)
        
        self.CaptchaResim()
        
        os.system("python resimonisle.py") # Hata yönetimi için subprocess düşünülebilir

        try:
            with open("captcha_sonuc.txt", "r", encoding="utf-8") as f:
                captcha_sonuc = f.read().strip()
            if not captcha_sonuc:
                raise ValueError("CAPTCHA sonuç dosyası boş.")
        except FileNotFoundError:
            print("HATA: captcha_sonuc.txt dosyası bulunamadı. resimonisle.py doğru çalıştı mı?")
            raise
        except ValueError as ve:
            print(f"HATA: {ve}")
            raise

        ToplamInput = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@title = 'Sayıların Toplamını Giriniz']"))
        )
        ToplamInput.send_keys(captcha_sonuc)

        GirisBut = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,"//a[@id ='btnLogin']"))
        )
        self.click_element_safely(GirisBut)

    def MenulerIslemleri(self):
        try:
            MenuBut = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//i[@class = 'fal fa-map-marked-alt']/.."))
            )
            self.click_element_safely(MenuBut)
            
            NotMenuBut = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//p[text() ='Not Listesi']/.."))
            )
            self.click_element_safely(NotMenuBut)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.frame_to_be_available_and_switch_to_it((By.ID, "IFRAME1"))
                )
                print("iframe'e geçiş yapıldı")
            except Exception as e:
                print(f"iframe (IFRAME1) bulunamadı veya geçiş yapılamadı: {e}")
                self.DersBilgi["error"] = "Not listesi iframe'i bulunamadı." # Hata bilgisi ekle
                return 
            
            Tablolar = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//*[@id="grd_not_listesi"]/tbody/tr'))
            )
            
            if len(Tablolar) > 0:
                satir_baslangic = 1 if len(Tablolar) > 1 and Tablolar[0].find_elements(By.XPATH, "./th") else 0
                
                for i in range(satir_baslangic, len(Tablolar)):
                    Tablo = Tablolar[i]
                    TabloIcerikler = Tablo.find_elements(By.XPATH, "./td")
                    
                    if len(TabloIcerikler) < 8:
                        print(f"Satır {i+1}: Yeterli sütun yok ({len(TabloIcerikler)} adet), atlanıyor...")
                        continue
                        
                    DersAdi = TabloIcerikler[2].text.strip()
                    if not DersAdi :
                        print(f"Satır {i+1}: Ders adı boş, atlanıyor...")
                        continue
                    print(f"İşlenen ders: {DersAdi}")

                    NotHucresi = TabloIcerikler[4]
                    NotMetni = NotHucresi.text
                    
                    Vize = "Girilmedi"
                    Final = "Girilmedi"
                    Proje = "Girilmedi"
                    Odev = "Girilmedi" 
                    
                    vize_match = re.search(r'Vize\s*:\s*([\d\.]+)', NotMetni)
                    if vize_match: Vize = vize_match.group(1)
                        
                    final_match = re.search(r'Final\s*:\s*([\d\.]+)', NotMetni)
                    if final_match: Final = final_match.group(1)
                        
                    proje_match = re.search(r'Proje\s*:\s*([\d\.]+)', NotMetni)
                    if proje_match: Proje = proje_match.group(1)

                    odev_match = re.search(r'Ödev\s*:\s*([\d\.]+)', NotMetni)
                    if odev_match: Odev = odev_match.group(1)

                    Ortalama = TabloIcerikler[5].text.strip() or "Girilmedi"
                    HarfNotu = TabloIcerikler[6].text.strip() or "Girilmedi"
                    Durum = TabloIcerikler[7].text.strip() or "Girilmedi"

                    self.DersBilgi[DersAdi] = {
                        "Vize": Vize,
                        "Final": Final,
                        "Proje": Proje,
                        "Odev": Odev,
                        "Ortalama": Ortalama,
                        "HarfNotu": HarfNotu,
                        "Durum": Durum
                    }
            else:
                print("Not listesi tablosunda satır bulunamadı!")
                self.DersBilgi["info"] = "Not listesi tablosunda ders bulunamadı." # Bilgi mesajı
            
            self.driver.switch_to.default_content()
            
        except Exception as e:
            print(f"MenulerIslemleri sırasında hata: {e}")
            self.DersBilgi.setdefault("error", f"Menü işlemleri sırasında hata: {str(e)}")
            try:
                self.driver.switch_to.default_content() # Hata durumunda da iframe'den çıkmaya çalış
            except:
                pass

    def NotlariGoruntule(self):
        print("\n--- DERS NOTLARI (Konsol) ---")
        if not self.DersBilgi:
            print("Henüz ders bilgisi çekilmedi veya ders bulunamadı.")
            return
        if self.DersBilgi.get("error"):
            print(f"HATA: {self.DersBilgi['error']}")
            return
        if self.DersBilgi.get("info") and len(self.DersBilgi) == 1 : # Sadece info varsa
             print(f"BİLGİ: {self.DersBilgi['info']}")
             return

        processed_ders_count = 0
        for ders, bilgiler in self.DersBilgi.items():
            if ders in ["error", "info"]: # "error" veya "info" anahtarlarını atla
                continue

            print(f"\nDers: {ders}")
            print(f"  Vize: {bilgiler.get('Vize', 'Girilmedi')}")
            print(f"  Final: {bilgiler.get('Final', 'Girilmedi')}")
            if bilgiler.get('Proje') and bilgiler['Proje'] != "Girilmedi":
                print(f"  Proje: {bilgiler['Proje']}")
            if bilgiler.get('Odev') and bilgiler['Odev'] != "Girilmedi":
                print(f"  Ödev: {bilgiler['Odev']}")
            print(f"  Ortalama: {bilgiler.get('Ortalama', 'Girilmedi')}")
            print(f"  Harf Notu: {bilgiler.get('HarfNotu', 'Girilmedi')}")
            print(f"  Durum: {bilgiler.get('Durum', 'Girilmedi')}")
            processed_ders_count += 1
        
        if processed_ders_count == 0 and not self.DersBilgi.get("error") and not self.DersBilgi.get("info"):
            print("Gösterilecek ders notu bulunamadı.")

    def Calistir(self):
        try:
            self.DersBilgi = {} # Her çalıştırmada DersBilgi'yi sıfırla
            self.ObsLogin()
            # Login sonrası ana sayfada bir elementin varlığını bekleyerek sayfanın yüklendiğinden emin ol
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//i[@class = 'fal fa-map-marked-alt']/..")) # Menü butonu
            )
            
            GirisSonuclar = self.driver.find_elements(By.XPATH,"//span[@id = 'lblSonuclar']")
            
            if not GirisSonuclar or not GirisSonuclar[0].text.strip():
                print("Login başarılı, menü işlemleri başlıyor.")
                self.MenulerIslemleri()
                # self.DersBilgi'de "error" anahtarı yoksa ve boş değilse başarılı kabul et
                if not self.DersBilgi.get("error") and any(key not in ["info", "error"] for key in self.DersBilgi):
                    print("Notlar başarıyla çekildi.")
                elif self.DersBilgi.get("info"): # Eğer sadece info mesajı varsa (örn: tablo boş)
                    print(f"İşlem tamamlandı. Bilgi: {self.DersBilgi.get('info')}")
                # Eğer MenulerIslemleri'nde bir hata olduysa DersBilgi'de error olabilir, bu durum zaten yukarıda yakalanır.
            else:
                hata_mesaji = GirisSonuclar[0].text.strip()
                print(f"Login yapılamadı! OBS Hata Mesajı: {hata_mesaji}")
                self.DersBilgi = {"error": f"Login başarısız: {hata_mesaji}"}
                raise Exception(f"Login başarısız oldu: {hata_mesaji}")
        except Exception as e:
            print(f"Calistir sırasında genel bir hata oluştu: {e}")
            # Eğer DersBilgi zaten bir hata içeriyorsa üzerine yazma, yoksa hatayı ekle
            self.DersBilgi.setdefault("error", str(e)) 
            raise e 
        # self.driver.quit() çağrıları kaldırıldı. Sorumluluk çağıran fonksiyonda.

if __name__ == "__main__":
    print("ObsNotBilgilendirmeBot doğrudan çalıştırılıyor (test amaçlı)...")
    obs_bot_instance = None 
    try:
        obs_bot_instance = ObsNotBilgilendirmeBot(KullaniciAd, Sifre)
        obs_bot_instance.Calistir()
        obs_bot_instance.NotlariGoruntule() 
    except Exception as e:
        print(f"Ana test bloğunda hata: {e}")
        # obs_bot_instance.DersBilgi doluysa ve error içeriyorsa tekrar NotlariGoruntule çağrılabilir
        if obs_bot_instance and obs_bot_instance.DersBilgi and obs_bot_instance.DersBilgi.get("error"):
            print("Hata sonrası DersBilgi durumu:")
            obs_bot_instance.NotlariGoruntule()
    finally:
        try:
            if obs_bot_instance and hasattr(obs_bot_instance, 'driver') and obs_bot_instance.driver:
                obs_bot_instance.driver.quit()
                print("Test sonrası WebDriver kapatıldı.")
        except Exception as e:
            print(f"Test sonrası WebDriver kapatılırken hata: {e}")
