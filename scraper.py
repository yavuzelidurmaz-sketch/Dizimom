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
    # Sitenin bot olduğumuzu anlamaması için gerçek bir tarayıcı kimliği:
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    url = f"https://ok.ru/profile/{profil_id}/video"
    print(f"Bağlanılıyor: {url}")
    driver.get(url)
    
    # Sitenin ilk yüklemesi için bekle
    time.sleep(5)
    
    print("Ana sayfa taranıyor. Tüm filmlerin yüklenmesi için sayfa yavaşça en alta kadar kaydırılacak...")
    print("Bu işlem sayfanın uzunluğuna göre 2-3 dakika sürebilir, lütfen bekleyin.")
    
    # ---------------------------------------------------------
    # AGRESİF VE UZUN SÜRELİ KAYDIRMA (Sadece ana sayfa için)
    # ---------------------------------------------------------
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_denemesi = 0
    max_scroll = 200 # Çok fazla film varsa bu sayıyı 300-400 yapabilirsiniz
    
    for i in range(max_scroll):
        # Bir insan gibi 800 piksel aşağı kaydır
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1.5) # Resimlerin ve yeni linklerin DOM'a düşmesi için bekle
        
        # Her 10 kaydırmada bir, sayfanın sonuna gelip gelmediğimizi kontrol et
        if i % 10 == 0:
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_denemesi += 1
                if scroll_denemesi >= 3:
                    print(f"Sayfanın en sonuna ulaşıldı! (Toplam {i} kez kaydırıldı)")
                    break # 3 kere kontrol ettik, sayfa daha uzamıyorsa döngüyü kır
            else:
                scroll_denemesi = 0
                last_height = new_height

    print("Kaydırma bitti! Şimdi sayfadaki veriler toplanıyor...")
    
    filmler_sozlugu = {}
    # Sayfadaki tüm video linklerini bul
    elementler = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
    
    for element in elementler:
        try:
            link = element.get_attribute('href')
            if not link: continue
                
            temiz_url = link.split('?')[0]
            
            # SADECE TEKİL FİLMLERİ AL (Sonu rakamla bitenler. 'c' ile başlayan klasörleri çöpe at)
            match = re.search(r'/video/(\d+)$', temiz_url) 
            
            if match:
                video_id = match.group(1)
                temiz_link = f"https://ok.ru/video/{video_id}"
                
                # Film ismini bulabileceğimiz her yere bak
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
            
    print("İsimler filtreleniyor...")
    filmler = []
    
    for link, isimler in filmler_sozlugu.items():
        gecerli_isimler = []
        for isim in isimler:
            isim_kucuk = isim.lower()
            # Kısa/Anlamsız yazıları ele
            if len(isim) > 2 and not isim.replace(':', '').isdigit() and isim_kucuk not in ['view', 'views', 'görüntüleme', 'izlenme', 'izlenme sayısı']:
                gecerli_isimler.append(isim)
        
        if gecerli_isimler:
            en_iyi_isim = max(gecerli_isimler, key=len)
            en_iyi_isim = en_iyi_isim.replace('\n', ' - ') 
            filmler.append({"isim": en_iyi_isim, "link": link})
    
    print(f"İŞLEM TAMAMLANDI! Toplam {len(filmler)} TEKİL FİLM bulundu.")
    
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
