import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def ok_ru_filmleri_getir(profil_id):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-notifications')
    options.add_argument('--window-size=1920,1080')
    # ÖNEMLİ: Sitenin mobil sürüm veya eksik sayfa vermesini engellemek için User-Agent ekliyoruz
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    url = f"https://ok.ru/profile/{profil_id}/video"
    print(f"Bağlanılıyor: {url}")
    driver.get(url)
    time.sleep(5)
    
    print("Sayfa yavaş yavaş aşağı kaydırılıyor (Görüntülerin yüklenmesi için)...")
    
    # OK.ru gibi siteler tek seferde en alta inmeyi sevmez. 
    # Adım adım inerek tüm filmlerin isimlerinin DOM'a yüklenmesini zorluyoruz.
    for _ in range(60): # 60 adım aşağı kaydır (daha çok film için artırabilirsiniz)
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1.5)

    print("Veriler çekiliyor ve filmler ayıklanıyor...")
    
    filmler_sozlugu = {}
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
                
                # Sitedeki her türlü etiketten isim koparmayı deniyoruz
                if element.text: olasi_isimler.append(element.text.strip())
                if element.get_attribute('title'): olasi_isimler.append(element.get_attribute('title').strip())
                if element.get_attribute('aria-label'): olasi_isimler.append(element.get_attribute('aria-label').strip())
                
                # Kapak resimlerinin (thumbnail) içindeki yazıları da çek (Gerçek isim genelde buradadır)
                resimler = element.find_elements(By.TAG_NAME, 'img')
                for resim in resimler:
                    alt_metin = resim.get_attribute('alt')
                    if alt_metin: olasi_isimler.append(alt_metin.strip())
                    
                if temiz_link not in filmler_sozlugu:
                    filmler_sozlugu[temiz_link] = []
                    
                filmler_sozlugu[temiz_link].extend(olasi_isimler)
        except Exception:
            continue
            
    filmler = []
    
    for link, isimler in filmler_sozlugu.items():
        gecerli_isimler = []
        for isim in isimler:
            isim_kucuk = isim.lower()
            # "View", "1:30" gibi gereksiz verileri ele
            if len(isim) > 2 and not isim.replace(':', '').isdigit() and isim_kucuk not in ['view', 'views', 'görüntüleme', 'izlenme']:
                gecerli_isimler.append(isim)
        
        if gecerli_isimler:
            # Olası isimler arasından en uzun ve en mantıklı olanı seç
            en_iyi_isim = max(gecerli_isimler, key=len)
            en_iyi_isim = en_iyi_isim.replace('\n', ' - ') # Varsa alt satıra geçişleri temizle
            filmler.append({"isim": en_iyi_isim, "link": link})
    
    print(f"Toplam {len(filmler)} TEKİL FİLM bulundu. Dosyalar kaydediliyor...")
    
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
