import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def ok_ru_filmleri_getir(profil_id):
    # GitHub Actions için Headless Chrome Ayarları
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-notifications')
    options.add_argument('--window-size=1920,1080')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Kullanıcının video sayfasına git
    url = f"https://ok.ru/profile/{profil_id}/video"
    print(f"Bağlanılıyor: {url}")
    driver.get(url)
    time.sleep(5)
    
    print("Sayfa aşağı kaydırılarak içerikler yükleniyor...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    scroll_count = 0
    max_scrolls = 40 # Daha fazla film yükleyebilmek için kaydırma sayısını artırdık
    
    while scroll_count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break # Sayfa sonuna gelindi
        last_height = new_height
        scroll_count += 1

    print("Veriler çekiliyor ve sadece tekil filmler ayıklanıyor...")
    
    filmler = []
    
    # Sayfadaki tüm linkleri bul
    elementler = driver.find_elements(By.XPATH, "//a[@href]")
    
    for element in elementler:
        try:
            link = element.get_attribute('href')
            
            # Filmin adını bulmak için farklı özellikleri (attributes) tara
            isim = element.get_attribute('aria-label') or element.get_attribute('title') or element.text
            isim = isim.strip() if isim else ""
            
            if not link or not isim:
                continue
            
            # Regex ile kontrol et: Link "/video/123456" şeklinde BİTMELİ (Albüm linklerini engeller)
            # URL'deki gereksiz parametreleri (?fromTime= vb) ayırarak kontrol et
            temiz_url_kismi = link.split('?')[0]
            match = re.search(r'/video/(\d+)$', temiz_url_kismi) 
            
            if match:
                video_id = match.group(1)
                temiz_link = f"https://ok.ru/video/{video_id}"
                
                # İsimde gereksiz uzun metinler veya sadece süre (örn: "01:45:00") varsa atla
                if isim and len(isim) > 2 and not any(film['link'] == temiz_link for film in filmler):
                    filmler.append({'isim': isim, 'link': temiz_link})
        except:
            # Stale element (sayfa yüklenirken kaybolan öğeler) hatalarını yoksay
            continue
            
    print(f"Toplam {len(filmler)} TEKİL FİLM bulundu. JSON olarak kaydediliyor...")
    
    # Verileri JSON dosyasına kaydet
    with open('filmler.json', 'w', encoding='utf-8') as f:
        json.dump(filmler, f, ensure_ascii=False, indent=4)
        
    driver.quit()

if __name__ == "__main__":
    profil_id = "591501811898"
    ok_ru_filmleri_getir(profil_id)
