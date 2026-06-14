# hermesmouse.py v3 — SendInput Migration

## Why SendInput?

`mouse_event()` / `keybd_event()` Win32 API'leri deprecate edildi.
Uygulamalar (özellikle oyunlar, Electron, Uygulama pencereleri)
bunları görmezden gelebiliyor. `SendInput` shared input queue'ya
yazar — anti-cheat/katmanlı pencereler dahil TÜM uygulamalar görür.

## Migration Pattern

| Eski (mouse_event) | Yeni (SendInput) |
|---|---|
| `user32.mouse_event(MOUSEEVENTF_LEFTDOWN, ...)` | `MOUSEINPUT(dwFlags=MOUSEEVENTF_LEFTDOWN) + SendInput` |
| `user32.keybd_event(vk, 0, 0, 0)` | `KEYBDINPUT(wScan=unicode, dwFlags=KEYEVENTF_UNICODE) + SendInput` |
| `dwExtraInfo=None` | `dwExtraInfo=0` (ULONG_PTR asla None almaz) |

## STRUCT Layout

```python
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),          # X absolute/relative
        ("dy", ctypes.c_long),          # Y absolute/relative
        ("mouseData", wintypes.DWORD),  # wheel delta / X-button
        ("dwFlags", wintypes.DWORD),    # MOUSEEVENTF_*
        ("time", wintypes.DWORD),       # 0 = auto
        ("dwExtraInfo", ULONG_PTR),     # 0 = none (never None!)
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),         # virtual key (0 for unicode)
        ("wScan", wintypes.WORD),       # scan code or unicode char
        ("dwFlags", wintypes.DWORD),    # KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
        ("time", wintypes.DWORD),       # 0 = auto
        ("dwExtraInfo", ULONG_PTR),     # 0 = none
    ]
```

## Critical Pitfalls

1. **dwExtraInfo MUST be int 0, not None** — `ULONG_PTR` ctypes type rejects None with `TypeError: 'NoneType' object cannot be interpreted as an integer`. Tüm `MOUSEINPUT` ve `KEYBDINPUT` yapılarında son parametre `0` olmalı.

2. **MOUSEEVENTF_WHEEL mouseData signed** — Scroll delta `(delta * 120)` `raw & 0xFFFFFFFF` ile signed->unsigned donusumu yapilir. `ctypes.c_long(raw).value & 0xFFFFFFFF` bazi Python surumlerinde OverflowError verir; dogrudan `raw & 0xFFFFFFFF` kullan.

3. **VIRTUALDESK flag multi-monitor** — `move_fast` `MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK` kullanır. Bu olmadan arttırılmış masaüstünde (extended display) koordinatlar yanlış hesaplanır.

## Unicode Keyboard (FIX #5)

`VkKeyScanW` yalnızca mevcut klavye düzenindeki tuşları destekler.
Türkçe `İ`, `ı`, `ş`, `ç`, `ğ`, `ü`, `ö` + emoji desteklenmez.

Yöntem: `KEYEVENTF_UNICODE` flag'i ile wScan alanına doğrudan
Unicode codepoint yazılır. Klavye düzeninden bağımsız çalışır.

```python
down = KEYBDINPUT(0, ord('İ'), KEYEVENTF_UNICODE, 0, 0)
up   = KEYBDINPUT(0, ord('İ'), KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
```

BMP dışı karakterler (emoji) için surrogate pair gerekir:
```python
if code > 0xFFFF:
    code -= 0x10000
    units = [0xD800 + (code >> 10), 0xDC00 + (code & 0x3FF)]
```

## ctypes Type Safety (FIX #4)

Tüm Win32 fonksiyonlarına argtypes/restype eklenmeli — 64-bit Python'da
pointer boyutu farkı hatalara yol açar:

```python
user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
user32.SetCursorPos.restype  = wintypes.BOOL
user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype  = wintypes.UINT
```

## Encoding Pipeline (v3 fix)

```
PowerShell → $OutputEncoding = [Text.Encoding]::UTF8
          → Bytes stdout
Pipeline → _decode_ps_bytes(bytes)
       → utf-8-sig → utf-8 → cp1254 → cp1252
       → fallback: utf-8 errors=replace
```

## DPI Awareness (v3.1)

Yuksek cozunurluklu ekranlarda (%125/%150) koordinat kaymasini onler.

3 kademeli fallback:
1. **SetProcessDpiAwarenessContext(DWMWA_PER_MONITOR_AWARE_V2)** — Win10 1703+, monitor-bazli, en iyi
2. **shcore SetProcessDpiAwareness(2)** — Win8.1+, Per-Monitor
3. **user32 SetProcessDPIAware()** — Vista+, sistem geneli

```python
def _set_dpi_awareness():
    # Once en iyisini dene, basarisizsa fallback
    try:
        user32.SetProcessDpiAwarenessContext(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
        return
    except: pass
    try:
        shcore = ctypes.WinDLL("shcore")
        shcore.SetProcessDpiAwareness(2)
        return
    except: pass
    user32.SetProcessDPIAware()
```

## Elevation / UIPI Detection (v3.1)

Elevated (yonetici) bir surece elevated olmayan bir surecten gonderilen SendInput/UIA mesajlari, UIPI (User Interface Privilege Isolation) tarafindan **sessizce yutulur**. Komut `1` doner ama hicbir sey olmaz.

```python
def is_elevated() -> bool:
    \"\"\"shell32.IsUserAnAdmin() ile elevation kontrolu.\"\"\"
    shell32 = ctypes.WinDLL("shell32")
    return bool(shell32.IsUserAnAdmin())
```

CLI'da click/dclick/rclick oncesi otomatik kontrol:
```python
if action in ("click", "dclick", "rclick") and not is_elevated():
    print("[uyari] Surec yonetici degil; ...")
```

## type_text KeyboardInterrupt Safety (v3.1)

Ctrl+C ile kesilirse yarim kalan son tusun KEYUP'i otomatik gonderilir:

```python
try:
    for i, ch in enumerate(text):
        ...  # SendInput down + up
except KeyboardInterrupt:
    log.warning("type_text kesildi (indeks %d/%d)", i, len(text))
    return i
```

Bu takili tusu (stuck key) engeller. Kesilme aninda kac karakter yazildigi bildirilir.
