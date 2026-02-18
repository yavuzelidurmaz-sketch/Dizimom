import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def ok_ru_filmleri_getir(profil_id):
    # GitHub Actions (Linux) üzerinde sorunsuz çalışması için gereken ayarlar
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-notifications')
    options.add_argument('--window-size=1920,1080')
    
    # Chrome Sürücüsünü otomatik indir ve başlat
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    url = f"https://ok.ru/profile/{profil_id}/video"
    print(f"Bağlanılıyor: {url}")
    driver.get(url)
    time.sleep(5)
    
    print("Sayfa aşağı kaydırılarak içerikler yükleniyor...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # Maksimum 20 kez kaydır (Sonsuz döngüde takılmamak için bir sınır koyuyoruz)
    scroll_count = 0
    max_scrolls = 20 
    
    while scroll_count < max_scrolls:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scroll_count += 1

    print("Veriler çekiliyor...")
    
    filmler = []
    # OK.ru video linkleri yapısı
    video_elementleri = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/') and text()!='']")
    
    for element in video_elementleri:
        isim = element.text.strip()
        link = element.get_attribute('href')
        
        # Tam linki oluştur (eğer link relative olarak geliyorsa)
        if link.startswith('/'):
            link = f"https://ok.ru{link}"
            
        if isim and not any(film['link'] == link for film in filmler):
            filmler.append({'isim': isim, 'link': link})
            
    print(f"Toplam {len(filmler)} film bulundu. JSON olarak kaydediliyor...")
    
    # Verileri bir JSON dosyasına kaydet
    with open('filmler.json', 'w', encoding='utf-8') as f:
        json.dump(filmler, f, ensure_ascii=False, indent=4)
        
    driver.quit()

if __name__ == "__main__":
    profil_id = "591501811898"
    ok_ru_filmleri_getir(profil_id)
