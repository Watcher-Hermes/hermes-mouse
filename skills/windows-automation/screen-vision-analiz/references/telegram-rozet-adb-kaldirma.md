# Telegram Reaksiyon Rozeti Kaldırma (ADB + uiautomator)

## Sorun

Telegram sohbetinde sağ altta mavi daire içinde sayı (125, 127...) + kalp (❤️) ikonu görünür. Bu "okunmamış reaksiyon bildirimi"dir.

## Çözüm — ADB ile UI element bul + tıkla

### 1. UI dump al

```python
import subprocess

adb = r"C:\Users\marko\AppData\Local\Android\Sdk\platform-tools\adb.exe"

subprocess.run([adb, "shell", "uiautomator", "dump", "/data/local/tmp/ui.xml"], capture_output=True, timeout=15)
subprocess.run([adb, "pull", "/data/local/tmp/ui.xml", "C:\\Users\\marko\\Desktop\\ui.xml"], capture_output=True, timeout=10)
```

> **NOT:** `adb pull` direkt Git Bash'te çalışmaz (yol dönüşümü: `/data/...` → `C:/Program Files/Git/data/...`). Her zaman Python `subprocess.run()` ile yap.

### 2. Rozet elementini bul

```
bounds=[613,610][718,730]   desc='Sonraki okunmamış tepkiye git'
```

Regex ile ara:
```python
import re, xml.etree.ElementTree as ET

tree = ET.parse("C:\\Users\\marko\\Desktop\\ui.xml")
root = tree.getroot()

def find_reaction_badge(node):
    desc = node.get("content-desc", "")
    if "tepki" in desc.lower() or "reaction" in desc.lower():
        return node.get("bounds")
    for child in node:
        result = find_reaction_badge(child)
        if result:
            return result
    return None

bounds_str = find_reaction_badge(root)
# "bounds" string: [613,610][718,730]
```

### 3. Koordinatları hesapla ve tıkla

```python
# [x1,y1][x2,y2] → merkez
import re
match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds_str)
x1, y1, x2, y2 = map(int, match.groups())
tap_x, tap_y = (x1 + x2) // 2, (y1 + y2) // 2

subprocess.run([adb, "shell", "input", "tap", str(tap_x), str(tap_y)], timeout=5)
```

### 4. Doğrula

```python
subprocess.run([adb, "shell", "uiautomator", "dump", "/data/local/tmp/ui.xml"], capture_output=True, timeout=15)
subprocess.run([adb, "pull", "/data/local/tmp/ui.xml", "C:\\Users\\marko\\Desktop\\ui2.xml"], capture_output=True, timeout=10)

with open("C:\\Users\\marko\\Desktop\\ui2.xml") as f:
    content = f.read()

if "tepki" in content.lower():
    print("HALA VAR")
else:
    print("ROZET GİTTİ ✓")
```

## Alternatif: doğrudan koordinat (ekran çözünürlüğü 720x1544)

Rozet genelde `x: 665, y: 670` civarında olur. Ama uiautomator ile bulmak daha güvenilir.

## Önemli

- Bu rozet **bildirim değil**, UI içindeki bir navigasyon butonudur
- Tıklayınca okunmamış reaksiyonların olduğu mesaja gider
- Rozetin kaybolması için tıklamak yeterlidir
