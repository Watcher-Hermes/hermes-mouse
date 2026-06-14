---
name: mouse-klavye-ctypes
description: Use when moving the mouse, clicking, scrolling, typing text, or drawing on screen on Windows. Uses C:\Users\marko\hermesmouse.py via ctypes (Win32 API) — no pip dependencies needed. ALWAYS use this script instead of pyautogui or PowerShell Forms which fail in terminal environments.
version: 1.0.0
author: marko
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [mouse, click, keyboard, scroll, sweep, ctypes, win32, automation, windows]
    related_skills: [tam-sistem-yetkisi, screen-vision-analiz]
---

# Mouse / Klavye Kontrolü (ctypes, bağımlılıksız)

## Overview

`C:\Users\marko\hermesmouse.py` scripti, Win32 API üzerinden fare ve klavyeyi
kontrol eder. pyautogui veya PowerShell Forms gerektirmez — sadece standart
Python `ctypes` kütüphanesi yeterli.

**KRITIK:** Terminal ortamında pyautogui veya PowerShell Forms genellikle bozulur.
Her zaman bu scripti kullan.

## When to Use

- Fare hareketi, tıklama, scroll
- Klavyeyle metin yazma
- Ekranda görünür demo (sweep/daire)
- "Fare hareket ettirildi ama görünmedi" durumları

Don't use for: Oyun anti-cheat korumalı uygulamalar.

---

## Komut Referansı

```bash
# Mevcut fare konumu
python C:\Users\marko\hermesmouse.py pos

# Fareyi (x,y)'ye yumusak tasi
python C:\Users\marko\hermesmouse.py move 800 400

# Sol tik
python C:\Users\marko\hermesmouse.py click 800 400

# Sag tik
python C:\Users\marko\hermesmouse.py rclick 800 400

# Cift tik
python C:\Users\marko\hermesmouse.py dclick 800 400

# Scroll (pozitif=yukari, negatif=asagi)
python C:\Users\marko\hermesmouse.py scroll 3
python C:\Users\marko\hermesmouse.py scroll -3

# Gorunum demo - buyuk daire cizer (kullaniciya gosterim icin)
python C:\Users\marko\hermesmouse.py sweep

# Metin yaz (aktif alana)
python C:\Users\marko\hermesmouse.py type "Merhaba Hermes"
```

## Terminal'den Calistirma (Hermes Agent)

```bash
# Hermes terminal aracinda kullan:
python C:\Users\marko\hermesmouse.py move 500 400
python C:\Users\marko\hermesmouse.py sweep
```

Cikti: `moved 500 400` veya `Tamamlandi.`

## Python API (script icinde kullanim)

```python
import sys
sys.path.insert(0, r"C:\Users\marko")
import hermesmouse as m

m.move(800, 400)          # yumusak hareket
m.click(200, 150)         # sol tik
m.rclick(200, 150)        # sag tik
m.scroll(-3)              # asagi scroll
m.sweep()                 # daire demo
m.type_text("Merhaba!")   # klavye yazma
x, y = m.get_pos()        # mevcut konum
```

## Ekran Koordinat Sistemi

- Sol ust kose: (0, 0)
- 1920x1080 ekranda sag alt: (1919, 1079)
- Merkez tahmini: (960, 540)
- Mevcut konumu ogren: `python hermesmouse.py pos`

## Common Pitfalls

1. **pyautogui kullaniyor ama asmaliyor** — hermesmouse.py kullan, ctypes hic takilmaz.
2. **PowerShell Forms exit 1 veya exit 127** — hermesmouse.py tek satir terminal komutuyla calisir.
3. **Hareket oldu ama gorunmedi** — sweep komutunu kullan, daire cizerek gosterir.
4. **Path bosluk hatasi** — script `C:\Users\marko\hermesmouse.py` (bosluksuz kok).
5. **Ekran cozunurlugu farkli** — once `pos` ile gercek koordinatlari al.

## Verification Checklist

- [ ] `python C:\Users\marko\hermesmouse.py pos` konum yazdi
- [ ] `python C:\Users\marko\hermesmouse.py move 800 400` fare gitti
- [ ] `python C:\Users\marko\hermesmouse.py sweep` daire gorundu
- [ ] Hermes terminal ciktisi `moved X Y` veya `Tamamlandi.` icerdi
