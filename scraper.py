import json
import time
import re
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def stealth_scroll(driver, mesaj):
    print(f"{mesaj} - İnsan taklidi yapılarak rastgele hızlarda kaydırılıyor...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    hareketsiz_kalma = 0
    
    while True:
        # İnsan gibi rastgele piksellerde kaydır
        kaydirma_miktari = random.randint(600, 1400)
        driver.execute_script(f"window.scrollBy(0, {kaydirma_miktari});")
        
        # Sabit değil, küsuratlı rastgele sürelerde bekle (Sitenin bot korumasını aşmak için)
        bekleme_suresi = random.uniform(2.1, 4.8)
        time.sleep(bekleme_suresi)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            hareketsiz_kalma += 1
            # Sayfa inmiyorsa biraz daha uzun bekle ve tekrar dene
            time.sleep(random.uniform(3.0, 5.0))
            if hareketsiz_kalma >= 4:
                break
        else:
            hareketsiz_kalma = 0
            last_height = new_height

def videolari_ayikla(driver, filmler_sozlugu):
    elementler = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
    for element in elementler:
        try:
            link = element.get_attribute('href')
            if not link: continue
                
            temiz_url = link.split('?')[0]
            match = re.search(r'/video/(\d+)$', temiz_url) 
            
            if match:
                video_id = match.group(1)
                temiz_link = f"https://ok.ru/video/{video_id}"
                
                olasi_isimler = []
                if element.text: olasi_isimler.append(element.text.strip())
                if element.get_attribute('title'): olasi_isimler.append(element.get_attribute('title').strip())
                if element.get_attribute('aria-label'): olasi_isimler.append(element.get_attribute('aria-label').strip())
                
                resimler = element.find_elements(By.TAG_NAME, 'img')
                for resim in resimler:
                    alt_metin = resim.get_attribute('alt')
                    if alt_metin: olasi_isimler.append(alt_metin.strip())
                    
                if temiz_link not in filmler_sozlugu:
                    filmler_sozlugu[temiz_link] = []
                    
                filmler_sozlugu[temiz_link].extend(olasi_isimler)
        except Exception:
            continue

def ok_ru_filmleri_getir(profil_id):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-notifications')
    
    # Çok Önemli: Bot olduğumuzu gizleyen özel Chrome ayarları
    options.add_argument('--disable-blink-features=AutomationControlled') 
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Tarayıcının 'webdriver' değişkenini sil (Nihai bot gizleme taktiği)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    filmler_sozlugu = {}
    
    # --- 1. ADIM: ANA SAYFAYI TARA ---
    ana_url = f"https://ok.ru/profile/{profil_id}/video"
    print(f"Bağlanılıyor: {ana_url}")
    driver.get(ana_url)
    time.sleep(random.uniform(4.5, 6.5))
    
    stealth_scroll(driver, "Ana Sayfa")
    
    album_linkleri = []
    tum_linkler = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/c')]")
    for el in tum_linkler:
        try:
            href = el.get_attribute('href')
            if href:
                temiz_href = href.split('?')[0]
                if re.search(r'/video/c\d+$', temiz_href) and temiz_href not in album_linkleri:
                    album_linkleri.append(temiz_href)
        except:
            pass

    print(f"Toplam {len(album_linkleri)} albüm bulundu. Şimdi hepsi tek tek taranacak!")
    videolari_ayikla(driver, filmler_sozlugu)

    # --- 2. ADIM: ALBÜMLERİ TARA ---
    for i, album_url in enumerate(album_linkleri, 1):
        print(f"[{i}/{len(album_linkleri)}] Albüm taranıyor: {album_url}")
        driver.get(album_url)
        time.sleep(random.uniform(3.5, 5.5))
        
        stealth_scroll(driver, f"Albüm {i}")
        videolari_ayikla(driver, filmler_sozlugu)

    # --- 3. ADIM: KAYDET ---
    print("Tüm veriler toplandı, liste temizleniyor...")
    filmler = []
    
    for link, isimler in filmler_sozlugu.items():
        gecerli_isimler = []
        for isim in isimler:
            isim_kucuk = isim.lower()
            if len(isim) > 2 and not isim.replace(':', '').isdigit() and isim_kucuk not in ['view', 'views', 'görüntüleme', 'izlenme', 'izlenme sayısı']:
                gecerli_isimler.append(isim)
        
        if gecerli_isimler:
            en_iyi_isim = max(gecerli_isimler, key=len)
            en_iyi_isim = en_iyi_isim.replace('\n', ' - ') 
            filmler.append({"isim": en_iyi_isim, "link": link})
    
    print(f"MÜTHİŞ! Tüm tarama bitti. Toplam {len(filmler)} ADET FİLM bulundu. Dosyalara yazılıyor...")
    
    with open('filmler.json', 'w', encoding='utf-8') as f:
        json.dump(filmler, f, ensure_ascii=False, indent=4)

    with open('filmler.m3u', 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for film in filmler:
            f.write(f"#EXTINF:-1,{film['isim']}\n")
            f.write(f"{film['link']}\n")
        
    driver.quit()

if __name__ == "__main__":
    profil_id = "591501811898"
    ok_ru_filmleri_getir(profil_id)
