import cloudscraper
from bs4 import BeautifulSoup
import time
import re

# Ayarlar
BASE_URL = "https://www.kanald.com.tr"

# Taranacak URL Listesi
TARGETS = [
    {"url": "https://www.kanald.com.tr/diziler", "type": "DIZI", "is_archive": False},
    {"url": "https://www.kanald.com.tr/programlar", "type": "PROGRAM", "is_archive": False},
    # İstersen arşivleri de açabilirsin, şimdilik test için kapalı kalsın dersen yorum satırı yapma:
    {"url": "https://www.kanald.com.tr/diziler/arsiv?page=", "type": "DIZI", "is_archive": True},
    {"url": "https://www.kanald.com.tr/programlar/arsiv?page=", "type": "PROGRAM", "is_archive": True}
]

def get_real_m3u8(scraper, bolum_url):
    """Bölüm sayfasından ve embed içinden gerçek M3U8 linkini bulur"""
    try:
        # 1. Aşama: Bölüm sayfasından Embed URL'yi çek
        r1 = scraper.get(bolum_url, timeout=15)
        embed_match = re.search(r'<link[^>]+itemprop=["\']embedURL["\'][^>]+href=["\']([^"\']+)["\']', r1.text)

        if not embed_match:
            # Alternatif: Iframe src içinde ara
            soup = BeautifulSoup(r1.text, 'html.parser')
            iframe = soup.find('iframe', src=re.compile(r'embed'))
            if iframe:
                embed_url = iframe['src']
                if embed_url.startswith('//'): embed_url = "https:" + embed_url
            else:
                return None
        else:
            embed_url = embed_match.group(1)

        # 2. Aşama: Embed sayfasının içine girip M3U8 pattern'lerini ara
        r2 = scraper.get(embed_url, timeout=15, headers={"Referer": BASE_URL})
        embed_html = r2.text

        # Regex Pattern'leri
        patterns = [
            r'https?://vod[0-9]*\.cf\.dmcdn\.net/[^\s"\']+\.m3u8', # DMCDN Pattern
            r'https?://[^\s"\']+\.m3u8',                          # Genel M3U8
            r'["\']videoUrl["\']\s*:\s*["\']([^"\']+)["\']',       # JS VideoURL
            r'src=["\']([^"\']+\.m3u8)["\']'                       # Src tag
        ]

        for p in patterns:
            m = re.search(p, embed_html)
            if m:
                found_url = m.group(1) if "(" in p else m.group(0)
                return found_url.replace('\\/', '/') # Unescape yap

        return None
    except Exception as e:
        # print(f"      Link bulma hatası: {e}") # Çok kalabalık etmesin diye kapattım
        return None

def get_episodes(scraper, show_url):
    """Bir dizinin/programın TÜM sayfalarındaki bölümlerini çeker"""
    episodes = []
    page = 1
    
    # URL sonundaki slash'ı temizle ve bolumler ekle
    base_bolum_url = show_url.rstrip('/') + "/bolumler"
    
    print(f"  👉 Bölümler taranıyor: {base_bolum_url}")

    while True:
        # Sayfalama URL yapısı (Senin istediğin format)
        target_url = f"{base_bolum_url}?page={page}&orderby=StartDate%20desc,EpisodeNumber%20desc"
        
        try:
            print(f"     📄 Bölüm Sayfası {page} taranıyor...")
            resp = scraper.get(target_url, timeout=15)
            
            # Eğer sayfa yoksa veya yönlendirme yapıyorsa çık
            if resp.status_code != 200:
                print("     ✅ Sayfa bitti veya erişilemiyor.")
                break

            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Kartları bul
            cards = soup.select('.story-card, .content-card, .video-card, .card-item, .item-card')
            
            # Eğer bu sayfada hiç kart yoksa döngüyü kır (Bitiş noktası)
            if not cards:
                print("     🚫 Bu sayfada içerik yok, tarama tamamlandı.")
                break

            found_in_page = 0
            for card in cards:
                link_tag = card.find('a', href=True) or (card if card.name == 'a' else None)
                name_tag = card.select_one('.title, h3, h2, .caption, .card-title')
                
                if link_tag:
                    b_url = link_tag['href']
                    if not b_url.startswith('http'):
                        b_url = BASE_URL + b_url if b_url.startswith('/') else BASE_URL + '/' + b_url
                    
                    # Başlık yoksa URL'den üret
                    if name_tag:
                        ep_name = name_tag.get_text(strip=True)
                    else:
                        ep_name = b_url.split('/')[-1].replace('-', ' ').title()

                    # M3U8 Linkini bul
                    m3u8 = get_real_m3u8(scraper, b_url)
                    
                    if m3u8:
                        episodes.append({
                            "name": ep_name,
                            "url": m3u8
                        })
                        found_in_page += 1
                        print(f"      🔗 Eklendi ({len(episodes)}. Toplam): {ep_name[:40]}...")
            
            # Eğer sayfada hiç geçerli link bulamadıysa yine de sonraki sayfaya bakmalı mı?
            # Genelde boş sayfa gelince 'cards' boş olur ve yukarıda break olur.
            # Ama kart var link yoksa devam etsin.
            
            page += 1 # Sonraki sayfaya geç
            time.sleep(1) # Siteyi boğmamak için ufak bekleme

        except Exception as e:
            print(f"     ❌ Sayfa {page} hatası: {e}")
            break
            
    return episodes

def run_scraper():
    print("🚀 Kanal D Full Arşiv Scraper Başlatıldı...")
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    
    all_content = {} 

    for target in TARGETS:
        print(f"\n📂 Ana Kategori Taranıyor: {target['url']} ({target['type']})")
        
        page_range = range(1, 4) if target['is_archive'] else range(1, 2)
        
        for page in page_range:
            current_url = f"{target['url']}{page}" if target['is_archive'] else target['url']
            
            try:
                resp = scraper.get(current_url, timeout=15)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                cards = soup.select('a.poster-card, .program-card a, .series-card a')
                
                if not cards and target['is_archive']:
                    break
                
                for card in cards:
                    href = card.get('href')
                    if not href: continue
                    
                    full_url = BASE_URL + href if href.startswith('/') else href
                    
                    img_tag = card.find('img')
                    title = card.get('title')
                    if not title and img_tag: title = img_tag.get('alt')
                    if not title: 
                        title = href.strip('/').split('/')[-1].replace('-', ' ').title()
                    
                    poster = ""
                    if img_tag:
                        poster = img_tag.get('data-src') or img_tag.get('src') or ""
                    
                    if title not in all_content:
                        print(f"\n📺 DİZİ/PROGRAM BULUNDU: {title}")
                        # get_episodes artık max_episodes almıyor, hepsini alıyor
                        episodes = get_episodes(scraper, full_url)
                        
                        if episodes:
                            all_content[title] = {
                                "poster": poster,
                                "type": target['type'],
                                "bolumler": episodes
                            }
                            
            except Exception as e:
                print(f"  ❌ Ana liste hatası: {e}")
                continue

    create_m3u(all_content)

def create_m3u(data):
    file_name = "kanald_full.m3u"
    print(f"\n📝 {file_name} dosyası oluşturuluyor...")
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for title, content in data.items():
            group_title = title
            poster = content['poster']
            
            for ep in content['bolumler']:
                ep_name = ep['name']
                link = ep['url']
                display_name = f"{group_title} - {ep_name}"
                
                f.write(f'#EXTINF:-1 group-title="{group_title}" tvg-logo="{poster}",{display_name}\n')
                f.write(f'{link}\n')

    print("✅ M3U dosyası hazır!")

if __name__ == "__main__":
    run_scraper()
