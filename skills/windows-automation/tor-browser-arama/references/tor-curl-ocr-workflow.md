# Tor Browser — curl + OCR ile Tarayıcı İçeriği Okuma

## Ne Zaman Kullanılır

- `hermestor.py proxy` veya `tor_get()` SOCKS üzerinden zaman aşımına uğrarsa
- Tarayıcıda bir sayfa açık ama Python SOCKS istemcisi bağlanamıyorsa
- Ekranda ne olduğunu görmek için OCR gerekirse

## curl ile Tor Proxy Üzerinden HTTP

Python `requests[socks]` zaman aşımına uğradığında `curl` alternatifi:

```bash
curl --socks5-hostname 127.0.0.1:9150 --connect-timeout 10 -s "https://github.com/trending"
```

- `--socks5-hostname` = DNS de Tor üzerinden çözülsün (socks5h mantığı)
- `--connect-timeout 10` = 10 sn'de bağlanamazsa vazgeç
- `-s` = sessiz mod (progress bar yok)

## Pencere Odağı (Foreground)

Tor Browser açık ama arka plandaysa, EnumWindows ile bulup öne getir:

```bash
powershell -ExecutionPolicy Bypass -File "C:\Users\marko\AppData\Local\hermes\skills\windows-automation\tor-browser-arama\scripts\focus_tor.ps1"
```

## Klavye Navigasyonu (hermesmouse.py)

Pencere odaktayken:

| İşlem | Komut |
|-------|-------|
| Adres çubuğuna odaklan | `python /c/Users/marko/hermesmouse.py type "^l"` |
| URL yaz | `python /c/Users/marko/hermesmouse.py type "https://github.com/trending"` |
| Enter bas | `python /c/Users/marko/hermesmouse.py type "{ENTER}"` |
| Aşağı scroll (8 tık) | `python /c/Users/marko/hermesmouse.py scroll -8` |
| Yukarı scroll | `python /c/Users/marko/hermesmouse.py scroll 5` |

## OC ile Ekran Doğrulama

Vision desteklemeyen modellerde (DeepSeek V4 Flash gibi), Tesseract OCR ile tarayıcı içeriğini oku:

```bash
"C:\Users\marko\AppData\Local\Python\PythonCore-3.14-64\python.exe" -c "
from PIL import Image; import subprocess; from mss import mss
with mss() as sct:
    sct_img = sct.grab(sct.monitors[1])
    img = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
    # Tarayıcı alanını kırp (sol %75, üst/alt kenar boşlukları)
    w, h = img.size
    crop = img.crop((0, 80, int(w*0.75), h-80))
    crop.save(r'C:\Users\marko\AppData\Local\hermes\scripts\screen_ocr.png')

import os
tess = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
result = subprocess.run([tess, r'C:\Users\marko\AppData\Local\hermes\scripts\screen_ocr.png', 'stdout', '-l', 'eng', '--psm', '4'], capture_output=True, text=True, timeout=30)
print(result.stdout[:3000])
"
```

## Tam İş Akışı (Örnek: GitHub Trending Açma)

```bash
# 1. Tor'u başlat (kapalıysa)
python /c/Users/marko/hermestor.py start

# 2. GitHub'ı Tor Browser'da aç
python /c/Users/marko/hermestor.py open "https://github.com/trending"
```bash
# Klavye tuşları adres çubuğuna gitmezse, navigate dene:
python /c/Users/marko/hermestor.py navigate "https://github.com/trending"

# Pencereyi öne getir
powershell -ExecutionPolicy Bypass -File "C:\Users\marko\AppData\Local\hermes\skills\windows-automation\tor-browser-arama\scripts\focus_tor.ps1"

# 4. Scroll yap (sayfa yüklendiyse)
python /c/Users/marko/hermesmouse.py scroll -8

# 5. OCR ile oku
# (yukarıdaki Python komutu)

# 6. curl ile yedek: Python SOCKS zaman aşarsa
curl --socks5-hostname 127.0.0.1:9150 --connect-timeout 10 -s "https://github.com/trending" | python -c "
import sys, re; html = sys.stdin.read()
links = re.findall(r'<h2[^>]*class=\"[^\"]*\"[^>]*>\s*<a[^>]*href=\"/([^\"]+)\"', html)
for l in links[:20]: print(' ', l)
"
```

## Püf Noktaları

- `curl --socks5-hostname` Python `requests[socks]`'tan daha hızlı bağlanabilir
- OCR için `--psm 4` (tek sütun) tarayıcı metni için `--psm 6`'dan daha iyi sonuç verir
- Tarayıcı alanını kırpmak OCR kalitesini önemli ölçüde artırır
- Klavye komutları gönderildikten sonra sayfanın yüklenmesi için 3-5 sn bekle

## Kritik Navigasyon Sorunları ve Çözümleri

### Sorun: Klavye tuşları adres çubuğu yerine sayfadaki arama kutusuna gidiyor

**Belirti:** Ctrl+L + URL + Enter gönderince, sayfadaki DuckDuckGo arama kutusuna yazılıyor.
OCR'da `"https://...{ENTER}github.com/ — DuckDuckGo ile ara"` şeklinde görünür.

**Neden:** Tor Browser'da varsayılan sayfa DuckDuckGo'dur. Sayfa içindeki arama kutusu odaklanmışsa,
Ctrl+L bazen adres çubuğu yerine sayfadaki DuckDuckGo kutusuna gider.

**Çözüm (öncelik sırasına göre):**
1. **TERCIH EDILEN: `hermestor.py navigate <URL>` kullan** — Bu komut Firefox'a doğrudan
   `urlInput.value=` ile adres çubuğuna yazar. Ctrl+L'den daha güvenilir.
2. **Alternatif: Adres çubuğuna mouse ile tıkla, sonra yaz** — `hermesmouse.py click X Y`
   ile adres çubuğu koordinatına tıkla (1920x1200'de ~300,85), ardından Ctrl+A + URL + Enter.
3. **Son çare: Ctrl+L + URL + Enter manuel** — Çalışır ama bazen sayfadaki arama kutusuna gider.

### Sorun: `hermestor.py open` arka planda açıyor, ön planda değil

**Belirti:** `open` komutu çalıştı, sayfa yüklendi ama ekranda eski sayfa görünüyor.

**Çözüm:** `open`'dan hemen sonra focus script'i çalıştır:
```bash
python /c/Users/marko/hermestor.py open "https://github.com/trending"
sleep 3
powershell -ExecutionPolicy Bypass -File "C:\Users\marko\AppData\Local\hermes\skills\windows-automation\tor-browser-arama\scripts\focus_tor.ps1"
```

### Sorun: Sayfa yüklendi ama scroll gitmiyor / tıklamalar işlemiyor

**Belirti:** Scroll komutu gönderildi ama OCR aynı içeriği gösteriyor.

**Çözüm:** Pencere odağını tekrar dene. Bazen Tor Browser odaklanmış görünür
ama klavye olaylarını kabul etmez. Bir Alt+Tab atıp geri dön:
```bash
python /c/Users/marko/hermesmouse.py type "%{TAB}"
sleep 1
powershell -ExecutionPolicy Bypass -File "...scripts\focus_tor.ps1"
```
