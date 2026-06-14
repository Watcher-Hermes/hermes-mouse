# Tor Çıkış Düğümü — Site Engelleme Durumu (2026-06)

Test ortamı: Windows 10, Tor Browser, SOCKS5h:127.0.0.1:9150

| Site | Durum | Not |
|---|---|---|
| check.torproject.org | ✅ Çalışıyor | "Congratulations" sayfası |
| google.com/search | ✅ Çalışıyor | JS ağırlıklı, CAPTCHA yok |
| html.duckduckgo.com | ❌ Engellendi | "Tor exit node blocked" |
| lite.duckduckgo.com | ❌ Engellendi | Boş sonuç döner |
| en.wikipedia.org | ❌ Engellendi | "Wikimedia Error" sayfası |
| bing.com/search | ⚠️ Kısmi | 200 döner, JS render gerekli |

## Çalışan Arama Yöntemleri

### Yöntem 1: Google (requests + Tor proxy)
```python
import requests
proxies = {'https': 'socks5h://127.0.0.1:9150'}
url = 'https://www.google.com/search?q=Bluetooth+pairing&hl=en'
resp = requests.get(url, proxies=proxies, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
# resp.text HTML içinde sonuçlar var, regex ile çıkarılabilir
```

### Yöntem 2: Browser aracı (browser_navigate)
Tor proxy'siz direct browser kullan. Google CAPTCHA çıkabilir — "Refresh" dene veya farklı sorgu gir.

### Yöntem 3: Bing (requests)
```python
url = 'https://www.bing.com/search?q=bluetooth+pairing'
resp = requests.get(...)  # 200 döner ama JS render gerekir
```

## CAPTCHA Çözümü (Google)
Google CAPTCHA görürsen:
- Tarayıcıda manuel çözüm gerekir
- `browser_vision` ile captcha'yı okuyamazsın (DeepSeek vision yok)
- Yeni Tor devresi dene: Tor'u kapat/aç (yeni IP)
