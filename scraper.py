import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    url = f"https://ok.ru/profile/{profil_id}/video"
    print(f"Bağlanılıyor: {url}")
    driver.get(url)
    time.sleep(5)
    
    print("Sayfa aşağı kaydırılarak içerikler yükleniyor...")
    
    # Sayfayı klavye tuşlarıyla aşağı kaydırma (OK.ru için daha güvenilir yöntem)
    body = driver.find_element(By.TAG_NAME, 'body')
    for _ in range(30): # Daha fazla film yüklemek için bu sayıyı artırabilirsiniz
        body.send_keys(Keys.END)
        time.sleep(2)

    print("Veriler çekiliyor ve filmler ayıklanıyor...")
    
    filmler_sozlugu = {}
    elementler = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
    
    for element in elementler:
        try:
            link = element.get_attribute('href')
            if not link:
                continue
                
            temiz_url = link.split('?')[0]
            match = re.search(r'/video/(\d+)$', temiz_url) 
            
            if match:
                video_id = match.group(1)
                temiz_link = f"https://ok.ru/video/{video_id}"
                
                # Başlığı farklı yerlerden yakalamayı dene
                isim = element.get_attribute('title') or element.get_attribute('aria-label') or element.text
                isim = isim.strip() if isim else ""
                
                # Gereksiz kısa yazıları ("View", "1:30" vb.) elemek için filtre
                if len(isim) > 5 and not isim.isdigit():
                    # Link daha önce eklendiyse, elimizdeki isim yenisinden kısaysa güncelle (Gerçek başlığı bulmak için)
                    if temiz_link not in filmler_sozlugu:
                        filmler_sozlugu[temiz_link] = isim
                    else:
                        if len(isim) > len(filmler_sozlugu[temiz_link]):
                            filmler_sozlugu[temiz_link] = isim
        except Exception:
            continue
            
    # Sözlüğü listeye çevir
    filmler = [{"isim": isim, "link": link} for link, isim in filmler_sozlugu.items()]
    
    print(f"Toplam {len(filmler)} TEKİL FİLM bulundu. Dosyalar kaydediliyor...")
    
    # 1. JSON olarak kaydet
    with open('filmler.json', 'w', encoding='utf-8') as f:
        json.dump(filmler, f, ensure_ascii=False, indent=4)

    # 2. IPTV/Media Player için M3U olarak kaydet
    with open('filmler.m3u', 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for film in filmler:
            f.write(f"#EXTINF:-1,{film['isim']}\n")
            f.write(f"{film['link']}\n")
        
    driver.quit()

if __name__ == "__main__":
    profil_id = "591501811898"
    ok_ru_filmleri_getir(profil_id)
