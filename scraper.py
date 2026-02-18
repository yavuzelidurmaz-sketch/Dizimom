import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def limitsiz_kaydir(driver, mesaj):
    print(f"{mesaj} - Tüm içerik bitene kadar kaydırılıyor...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    hareketsiz_kalma = 0
    
    while True:
        # Bir insan gibi 1500 piksel aşağı kaydır
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(2) # Yeni içeriğin internetten inmesi için bekle
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            hareketsiz_kalma += 1
            # Sayfa üst üste 5 kez (10 saniye boyunca) hiç uzamadıysa kesinlikle en dipteyiz demektir
            if hareketsiz_kalma >= 5:
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
            # Sadece tekil filmleri al (Klasör linklerini pas geç)
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
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    filmler_sozlugu = {}
    
    # --- 1. ADIM: ANA SAYFAYI LİMİTSİZ TARA VE ALBÜMLERİ BUL ---
    ana_url = f"https://ok.ru/profile/{profil_id}/video"
    print(f"Bağlanılıyor: {ana_url}")
    driver.get(ana_url)
    time.sleep(5)
    
    limitsiz_kaydir(driver, "Ana Sayfa")
    
    album_linkleri = []
    tum_linkler = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/c')]")
    for el in tum_linkler:
        try:
            href = el.get_attribute('href')
            if href:
                temiz_href = href.split('?')[0]
                # Sadece 'c' ile başlayan albüm/klasör linklerini topla
                if re.search(r'/video/c\d+$', temiz_href) and temiz_href not in album_linkleri:
                    album_linkleri.append(temiz_href)
        except:
            pass

    print(f"Toplam {len(album_linkleri)} albüm/klasör bulundu. Şimdi hepsi tek tek taranacak!")
    
    # Ana sayfada klasör dışında duran filmleri de kaçırmayıp havuza at
    videolari_ayikla(driver, filmler_sozlugu)

    # --- 2. ADIM: ALBÜMLERİN İÇİNE GİR VE LİMİTSİZ TARA ---
    for i, album_url in enumerate(album_linkleri, 1):
        print(f"[{i}/{len(album_linkleri)}] Albüm taranıyor: {album_url}")
        driver.get(album_url)
        time.sleep(4)
        
        # Albüm içindeki tüm içerik bitene kadar in
        limitsiz_kaydir(driver, f"Albüm {i}")
        videolari_ayikla(driver, filmler_sozlugu)

    # --- 3. ADIM: İSİMLERİ SÜZ VE DOSYALARI OLUŞTUR ---
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
