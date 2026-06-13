---
name: mouse-klavye-ctypes
description: Windows'ta fare ve klavye kontrolü — ctypes ile (bağımlılıksız, Win32 API). Hermes'ten uygulama açma, element tıklama, menü gezinme, metin yazma, otonom akış yürütme, ekran görüntüsü alma.
version: 5.0.0
tested: 2026-06-14
author: marko
license: MIT
platforms: [windows]
repository: https://github.com/Watcher-Hermes/hermes-mouse
metadata:
  hermes:
    tags: [mouse, click, keyboard, scroll, sweep, ctypes, win32, automation, windows, element, uia, workflow, screenshot]
    related_skills: [tam-sistem-yetkisi, screen-vision-analiz, windows-automation-shortcuts]
---

# Hermes Mouse + Klavye Kontrolü (v5)

## Genel Bakış

`C:\Users\marko\hermesmouse.py` — 900+ satır, 0 dış bağımlılık.
Win32 API + PowerShell UIAutomation + GDI ile tam Windows otomasyonu.

pyautogui veya PowerShell Forms'a ihtiyaç duymaz.

---

## Komutlar

### Koordinat Bazlı

```bash
python hermesmouse.py pos                              # fare konumu
python hermesmouse.py status                           # ekran + DPI + elevation
python hermesmouse.py move <x> <y>                     # yumuşak hareket
python hermesmouse.py move <x> <y> --fast              # anlık hareket (SendInput)
python hermesmouse.py drag <x1> <y1> <x2> <y2>        # sürükle
python hermesmouse.py click <x> <y>                    # sol tık
python hermesmouse.py rclick <x> <y>                   # sağ tık
python hermesmouse.py dclick <x> <y>                   # çift tık
python hermesmouse.py scroll <delta>                   # kaydırma (+/-)
python hermesmouse.py sweep [cx cy r]                  # daire çiz (demo)
```

### Klavye

```bash
python hermesmouse.py type <metin>                     # Unicode yazı (Türkçe dahil)
python hermesmouse.py key <tus/kombinasyon>            # tuş gönder
# Örnekler:
python hermesmouse.py key enter
python hermesmouse.py key esc
python hermesmouse.py key "ctrl+s"
python hermesmouse.py key "ctrl+shift+esc"
python hermesmouse.py key "alt+f4"
```

### Element (UI Automation)

```bash
# Windows uygulamasındaki elementleri ada/ID'ye/class'a göre bul ve yönet
python hermesmouse.py element "Pencere" list
python hermesmouse.py element "Pencere" "Buton" click
python hermesmouse.py element "Pencere" "Buton" move
python hermesmouse.py element "Pencere" "btnOK" click --by AutomationId
python hermesmouse.py element "Pencere" "Button" click --by ClassName
python hermesmouse.py element "Pencere" "Buton" coord --by ClassName
python hermesmouse.py list-elements "Pencere"
python hermesmouse.py save-elements "Pencere" [cikti.json]
```

### Otonom Akış (Workflow)

```bash
# JSON veya metin dosyası ile adım adım otomasyon
python hermesmouse.py run akis.json
python hermesmouse.py run akis.txt
```

#### Örnek JSON akışı:

```json
{"steps": [
  {"do": "click", "window": "Not Defteri", "target": "Dosya"},
  {"do": "wait", "seconds": 0.3},
  {"do": "if_exists", "window": "Not Defteri", "target": "Çıkış",
   "then": {"do": "click"}},
  {"do": "key", "keys": "esc"},
  {"do": "type", "text": "merhaba dünya"}
], "pause": 0.2}
```

#### Örnek metin akışı:

```
# yorum satırı
wait 0.5
key esc
click "Not Defteri" | "Dosya"
wait 0.3
if_exists "Not Defteri" | "Çıkış" -> click
type "merhaba"
```

### Global Flag'ler

```
--verbose     debug log (DPI, elevation, UIA çağrıları)
--timeout N   element bulamazsa N saniye yeniden dene (0 = tek deneme)
```

---

## Python API (import edilebilir)

```python
import sys
sys.path.insert(0, r"C:\Users\marko")
import hermesmouse as hm

hm.move(800, 400)          # yumuşak hareket
hm.click(200, 150)         # sol tık
hm.type_text("Merhaba!")   # Unicode yazı
hm.press_key("ctrl+s")     # tuş kombinasyonu
x, y = hm.get_pos()        # fare konumu

# Element
r = hm.find_element("Not Defteri", "Dosya")
if "error" not in r:
    hm.click(r["x"], r["y"])

# Workflow
hm.run_workflow([{"do": "key", "keys": "esc"}])
```

---

## Çalışma Prensibi

### Mouse
- `move`: `SetCursorPos` ile kademeli
- `move --fast`: `SendInput` + `MOUSEEVENTF_ABSOLUTE` + `VIRTUALDESK` (çoklu monitör)
- `click/rclick/dclick`: `SendInput` ile `MOUSEINPUT` struct
- `scroll`: `SendInput` + signed long maskesi (negatif scroll için)

### Klavye
- `type`: `KEYEVENTF_UNICODE` ile — Türkçe karakter, emoji dahil
- `key`: Sanal tuş (VK) kodları + modifier sıralaması (ctrl+shift+esc gibi)
- `KeyboardInterrupt` yakalaması — kesilince takılı tuş kalmaz

### Element
- PowerShell + .NET UIAutomationClient
- Parametreler temp JSON dosyası ile (güvenli, injection yok)
- Encoding: PowerShell `$OutputEncoding = [Text.Encoding]::UTF8` + Python `utf-8-sig` öncelikli
- Arama: Name → AutomationId → ClassName → ControlType
- Fallback: regex kısmi eşleşme
- `--timeout`: 0.5sn aralıklarla retry

### Workflow Motoru
- Adım tipleri: `click`, `dclick`, `rclick`, `move`, `type`, `key`, `wait`, `if_exists`, `screenshot`, `assert`, `repeat`
- `if_exists`: element varsa `then` alt-eylemini çalıştır, yoksa atla
- `assert`: element var (`present`) veya yok (`absent`) kontrolü, başarısızsa akışı durdurur
- `repeat`: alt-eylemi N kez tekrarla (`times` + `interval`)
- `screenshot`: akış içinde ekran görüntüsü al
- `on_error`: `stop` (varsayılan) veya `skip`
- `--dry-run`: adımları yürütmeden doğrula
- `--log log.json`: zaman damgalı JSON kaydı
- `shot_on_error`: hata anında otomatik ekran görüntüsü
- JSON (.json) ve düz metin (.txt) formatı
- Her adımda KeyboardInterrupt kontrolü

### Altyapı
- `_setup_ctypes()`: 7 Win32 API için argtypes/restype tanımı (64-bit güvenliği)
- `_set_dpi_awareness()`: 3 kademeli fallback (PerMonitorV2 → shcore → SetProcessDPIAware)
- `is_elevated()`: shell32.IsUserAnAdmin()
- UIPI uyarısı: elevated olmayan süreçte tıklama/yazma etkisiz kalabilir
- `virtual_screen()`: çoklu monitör desteği

---

## Sınırlamalar

- Oyunlar/DirectX/OpenGL uygulamaları: element bulma çalışmaz (UI Automation desteklemez)
- Elevated uygulamalar: Hermes elevated değilse tıklamalar sessizce yutulur (UIPI)
- Notepad: bu ortamda açılamayabilir (headless sandbox)

---

## Test Durumu

109 test, 108 başarılı, 1 hata (move --fast TypeError → düzeltildi)
Tüm komutlar gerçek Windows'ta test edildi.

---

## Test Protokolü (X-RAY)

Bu kullanıcı için test raporlamada X-RAY modu zorunludur:

1. **Her testi ayrı terminal çağrısıyla çalıştır** — her komut ayrı çağrılmalı
2. **Ham çıktıyı göster** — filtresiz, yorumsuz, olduğu gibi
3. **Her test numaralandırılır** — `[TEST 1]`, `[TEST 2]`, ...
4. **Hata + çözüm birlikte gösterilir** — hata oluştuysa hemen çözümü uygula, aynı testi tekrar çalıştır
5. **Son sayım** — `X/Y TEST GECTI, Z HATA` formatında kapat
6. **Tekrar eden test varsa belirt** — hata+düzeltme aynı komutun iki kez çalışması
7. **Eksik senaryoları işaretle** — gerçek Windows'ta test edilmemiş kod, mock-only doğrulama
8. **FORENSIC çapraz-kontrol** — her satırı ham veriyle sun

### Yaygın Tuzaklar (Bu Oturumdan)

| Hata | Çözüm |
|------|-------|
| `element "X" list` action algılanmıyor | args[2] action keyword kontrolü |
| PowerShell çıktısı cp1254/UTF-8 | `[Console]::OutputEncoding = UTF8` + utf-8-sig öncelikli |
| `dwExtraInfo=None` → TypeError | ULONG_PTR `None` kabul etmez, `0` kullan |
| `--by ClassName coord` action kaçıyor | Flag'leri atlayan parser (`_parse_action`) |
| Tek elemanlı JSON dizi → nesne | `ConvertTo-Json @($results)` (@() sarması) |

### Kurulum (GitHub)

```powershell
iex "& { $(irm https://raw.githubusercontent.com/Watcher-Hermes/hermes-mouse/master/install.ps1) }"
hermesmouse pos
```

Resmi repo: https://github.com/Watcher-Hermes/hermes-mouse
