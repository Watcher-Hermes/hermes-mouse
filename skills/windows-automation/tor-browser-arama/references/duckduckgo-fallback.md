# DuckDuckGo Arama Alternatifleri

## Sorun
`hermestor.py search "sorgu"` komutu DuckDuckGo'nun `/html/` endpoint'ini kullanır.
Bazen bu endpoint:
- Tor çıkış IP'si banlı olduğu için boş döner
- DuckDuckGo taraf değiştirdiği için çalışmaz
- Captcha ister (görünmez)
- **Uzun sorgularda (>50 karakter) sessizce 0 sonuç döndürür**

## ÖNCELİKLİ YÖNTEM — DuckDuckGo Lite (Browser)

En güvenilir yaklaşım — DDG Lite'in basit HTML arayüzü CAPTCHA istemez.

```python
# 1. Browser'ı DDG Lite'a yönlendir
browser_navigate("https://lite.duckduckgo.com/lite/")

# 2. Sorguyu yaz
browser_type(ref="e1", text="kısa odaklı sorgu")

# 3. Ara
browser_click(ref="e2")

# 4. Sonuçları oku
browser_snapshot(full=true)

# 5. Detaylı sayfa için
browser_navigate("sonuc_url")
```

**Avantajlar:** CAPTCHA yok, query length sınırı yok, Tor ile çalışır.
**Dezavantaj:** Browser tool seti gerekir, her sayfada manuel adım gerekir.

## Alternatif Arama Yöntemleri

### 1. DuckDuckGo HTML (Python 3.14 + POST — en iyi 2. seçenek)
```python
import requests, urllib.parse, re

python314 = r"C:\Users\marko\AppData\Local\Python\pythoncore-3.14-64\python.exe"
proxies = {"https": "socks5h://127.0.0.1:9150", "http": "socks5h://127.0.0.1:9150"}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:128.0) Gecko/20100101 Firefox/128.0"}

r = requests.post("https://html.duckduckgo.com/html/", proxies=proxies, headers=headers,
                  data={"q": sorgu}, timeout=20)

# Sonuçları parse et
results = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.DOTALL)
snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</(?:a|div)>', r.text, re.DOTALL)
```

**ÖNEMLİ:**
- POST kullan, GET çalışmaz
- Sorgu kısa tut (<50 karakter)
- Uzun sorguda sonuç sayısı düşükse kısalt ve dene
- `requests` + `PySocks` Python 3.14'te kurulu (Hermes venv'de değil)

### 2. Google (Tor proxy üzerinden — sık bloke olur)
```python
url = "https://www.google.com/search?q=" + urllib.parse.quote(sorgu)
r = requests.get(url, proxies=proxies, headers=headers, timeout=20)
# Google Tor exit node'larını sık bloke eder. Çalışırsa:
titles = re.findall(r'<h3[^>]*>(.*?)</h3>', r.text, re.DOTALL)
links = re.findall(r'href="/url\?q=(https?://[^&"]+)"', r.text)
```

### 3. Bing (Tor proxy üzerinden — lokalize sonuç)
```python
url = "https://www.bing.com/search?q=" + urllib.parse.quote(sorgu)
r = requests.get(url, proxies=proxies, headers=headers, timeout=20)
# Bing Tor'dan gelen istekleri Tor çıkış düğümünün konumuna göre lokalize eder
# (örn. Almanya çıkışı → Almanca sonuçlar)
# `&setlang=en` veya `&cc=US` parametreleri eklemek işe yaramayabilir
```

### 4. Sayfa içeriğini doğrudan fetch et
```python
url = "https://hedef-site.com/sayfa"
r = requests.get(url, proxies=proxies, headers=headers, timeout=20)
print(r.text[:3000])
```

## Hata Ayıklama

```bash
# Tor çalışıyor mu kontrol
python C:\Users\marko\hermestor.py proxy "https://check.torproject.org"
# "Congratulations" içermeli

# DDG HTML endpoint'ine test
python314 -c "
import requests
proxies = {'https': 'socks5h://127.0.0.1:9150'}
r = requests.post('https://html.duckduckgo.com/html/', proxies=proxies,
                  data={'q': 'test'}, timeout=15)
print(f'Sonuc: {\"BASARILI\" if \"result__a\" in r.text else \"BOS\"} ({len(r.text)} byte)')
"

# Browser ile DDG Lite test (en güvenilir)
# browser_navigate("https://lite.duckduckgo.com/lite/")
```

## Query Length Sorunu

DuckDuckGo HTML endpoint'i uzun sorgularda (>50 karakter) **sessizce 0 sonuç döndürür** — hata mesajı yok, sadece boş sayfa.

**Çözüm:**
1. Sorguyu 2-3 kısa parçaya böl
2. Her parçayı ayrı arayıp sonuçları birleştir
3. Veya DDG Lite browser yöntemini kullan (bu sınırdan etkilenmez)

**Örnek:** "bluetooth audio sniffing intercept attack tools ubertooth" (61 karakter) → 0 sonuç
"bluetooth audio sniffing tools" (30 karakter) → sonuç döner
