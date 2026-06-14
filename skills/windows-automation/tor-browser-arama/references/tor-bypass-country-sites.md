# Ülke Siteleri Tor Bypass Referansı

Test tarihi: 11.06.2026
Python: "/c/Users/marko/AppData/Local/Python/pythoncore-3.14-64/python.exe" (PySocks VAR)
Proxy: socks5h://127.0.0.1:9150

## 🇷🇺 Rusya

### Sorun: habr.com, xakep.ru → CAPTCHA bloku

### Çözüm: RSS Feed
habr.com HTML sayfası CAPTCHA gösterir ancak RSS feed'i CAPTCHA'sız çalışır.

```python
# Habr RSS arama
r = requests.get(f'https://habr.com/en/rss/search/?q={urllib.parse.quote(SORGU)}',
                 proxies=proxies, headers=headers, timeout=20)
# RSS'den sonuç çıkar:
items = re.findall(r'<item>(.*?)</item>', r.text, re.DOTALL)
for item in items:
    title = re.findall(r'<title>(.*?)</title>', item)
    link = re.findall(r'<link>(.*?)</link>', item)
```

- Test: "bluetooth sniffing attack" sorgusu → 20 makale (BLUFFS, BLESA, BlueBorne, vb.)
- Xakep RSS: `requests.get('https://xakep.ru/feed/', ...)` → 10 son makale
- Bing RU: `https://www.bing.com/search?q={q}&cc=RU` → 10 sonuç (genel)

### Bloklu: habr.com HTML, xakep.ru HTML

---

## 🇨🇳 Çin

### Sorun: freebuf.com, csdn.net, anquanke.com → SOCKSHTTPSConnectionPool hatası
Sebep: Çin CDN/GFW Tor IP'lerini engelliyor.

### Çözüm: Kaspersky CN + Google Cache

```python
# Kaspersky CN (direkt çalışır)
r = requests.get('https://www.kaspersky.com.cn/blog/?s=' + urllib.parse.quote('蓝牙 安全'),
                 proxies=proxies, headers=headers, timeout=15)  # 133KB içerik

# Google Cache (domain cache çalışır, search cache bazen 429)
url = f'https://webcache.googleusercontent.com/search?q=cache:{DOMAIN}'
```

### Bloklu
- freebuf.com → SOCKS (kalıcı)
- csdn.net → SOCKS (kalıcı)
- anquanke.com → SOCKS (kalıcı)
- 360 netlab → SOCKS (kalıcı)
- Alibaba Security → SOCKS (kalıcı)
- Zhihu → HTTP 403
- Baidu → verification sayfası

---

## 🇰🇷 Kore

### Sorun: boannews.com, dailysec.kr → SOCKS hatası

### Çözüm: Bing KR + Naver

```python
# Bing KR
r = requests.get(f'https://www.bing.com/search?q={urllib.parse.quote(sorgu)}&cc=KR',
                 proxies=proxies, headers=headers, timeout=15)  # 119KB

# Naver (Kore arama motoru)
r = requests.get(f'https://search.naver.com/search.naver?query={urllib.parse.quote(sorgu)}',
                 proxies=proxies, headers=headers, timeout=15)  # 580KB
```

### Bloklu: boannews.com, dailysec.kr

---

## 🇯🇵 Japonya

### Sorun: security-next.com → 404, atmarkit → SOCKS hatası

### Çözüm: Bing JP
```python
r = requests.get(f'https://www.bing.com/search?q={q}&cc=JP&setlang=ja',
                 proxies=proxies, headers=headers, timeout=15)
```

### Bloklu: security-next.com, atmarkit.co.jp

---

## 🇮🇳 Hindistan

### Sorun: thehackernews.com → Cloudflare 403

### Çözüm: GBHackers + Bing IN

```python
# GBHackers (direkt çalışır, 193KB güvenlik içeriği)
r = requests.get(f'https://gbhackers.com/?s={urllib.parse.quote(sorgu)}',
                 proxies=proxies, headers=headers, timeout=15)

# Bing IN
r = requests.get(f'https://www.bing.com/search?q={q}&cc=IN&setlang=en-IN',
                 proxies=proxies, headers=headers, timeout=15)  # 122KB
```

### Bloklu: thehackernews.com (Cloudflare)
