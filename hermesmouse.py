"""
Hermes Mouse Control - ctypes ile (bagimliliksiz, Win32 API)

Kullanim:
  python hermesmouse.py pos
  python hermesmouse.py status
  python hermesmouse.py move <x> <y> [--fast]
  python hermesmouse.py drag <x1> <y1> <x2> <y2>
  python hermesmouse.py click <x> <y>
  python hermesmouse.py rclick <x> <y>
  python hermesmouse.py dclick <x> <y>
  python hermesmouse.py scroll <delta>
  python hermesmouse.py sweep [cx cy r]
  python hermesmouse.py type <metin>
  python hermesmouse.py key <tus>            (or: "ctrl+s", "alt+f4", "esc")
  python hermesmouse.py screenshot [dosya.bmp]
  python hermesmouse.py run <akis.json|akis.txt> [--dry-run] [--log log.json]
  python hermesmouse.py element "Pencere" list
  python hermesmouse.py element "Pencere" "Buton" click
  python hermesmouse.py element "Pencere" "Buton" move
  python hermesmouse.py element "Pencere" "btnOK" click --by AutomationId
  python hermesmouse.py element "Pencere" "Button" click --by ClassName
  python hermesmouse.py element "Pencere" "Button" click --by ControlType
  python hermesmouse.py element "Pencere" "Buton" coord --by ClassName
  python hermesmouse.py element "Pencere" "Buton" --by ClassName coord
  python hermesmouse.py list-elements "Pencere"
  python hermesmouse.py save-elements "Pencere" [cikti.json]

Global flag'ler:
  --verbose   ayrintili log
  --timeout N element arama yeniden deneme suresi (saniye, vars. 0 = tek deneme)
"""

import sys
import math
import time
import ctypes
import json
import subprocess
import tempfile
import os
import logging
from ctypes import wintypes

MOUSEEVENTF_LEFTDOWN  = 0x0002
MOUSEEVENTF_LEFTUP    = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP   = 0x0010
MOUSEEVENTF_WHEEL     = 0x0800
MOUSEEVENTF_MOVE      = 0x0001
MOUSEEVENTF_ABSOLUTE  = 0x8000
MOUSEEVENTF_VIRTUALDESK = 0x4000
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_UNICODE     = 0x0004

# GetSystemMetrics indeksleri
SM_CXSCREEN        = 0
SM_CYSCREEN        = 1
SM_XVIRTUALSCREEN  = 76
SM_YVIRTUALSCREEN  = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79

INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1

user32 = ctypes.WinDLL('user32', use_last_error=True)

log = logging.getLogger("hermes")

# Action keyword seti — arguman parse'inda kullanilir
_ACTION_KEYWORDS = {"click", "move", "dclick", "rclick", "coord", "list"}
_VALID_SEARCH_BY = {"Name", "AutomationId", "ClassName", "ControlType"}


# ---------------------------------------------------------------------------
# FIX #4: ctypes argtypes / restype tanimlari — 64-bit guvenligi
# ---------------------------------------------------------------------------

def _setup_ctypes():
    user32.GetSystemMetrics.argtypes = [ctypes.c_int]
    user32.GetSystemMetrics.restype  = ctypes.c_int

    user32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    user32.SetCursorPos.restype  = wintypes.BOOL

    user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
    user32.GetCursorPos.restype  = wintypes.BOOL

    user32.VkKeyScanW.argtypes = [wintypes.WCHAR]
    user32.VkKeyScanW.restype  = ctypes.c_short

    # mouse_event/keybd_event eski API; yine de imza netligi icin
    user32.mouse_event.argtypes = [
        wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
        wintypes.DWORD, ctypes.POINTER(ctypes.c_ulong)
    ]
    user32.keybd_event.argtypes = [
        wintypes.BYTE, wintypes.BYTE, wintypes.DWORD,
        ctypes.POINTER(ctypes.c_ulong)
    ]

    _set_dpi_awareness()


# DPI farkindalik sabitleri
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)


def _set_dpi_awareness():
    """Sureci DPI-aware yap — yuksek olcekli ekranlarda (%125/%150) koordinat
    kaymasini onler (KRITIK).

    Kademeli fallback:
      1. SetProcessDpiAwarenessContext (Win10 1703+) — en iyi, monitor-bazli
      2. shcore.SetProcessDpiAwareness(2)            — Win8.1+
      3. user32.SetProcessDPIAware()                 — Vista+ sistem geneli
    Hicbiri yoksa sessizce gecer; eski Windows'ta ölçekleme zaten yoktur.
    """
    try:
        user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user32.SetProcessDpiAwarenessContext.restype  = wintypes.BOOL
        if user32.SetProcessDpiAwarenessContext(
                DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2):
            log.debug("DPI: PerMonitorV2 etkin")
            return
    except (AttributeError, OSError):
        pass

    try:
        shcore = ctypes.WinDLL("shcore", use_last_error=True)
        # 2 = PROCESS_PER_MONITOR_DPI_AWARE
        if shcore.SetProcessDpiAwareness(2) == 0:
            log.debug("DPI: shcore PerMonitor etkin")
            return
    except (OSError, AttributeError):
        pass

    try:
        if user32.SetProcessDPIAware():
            log.debug("DPI: sistem geneli aware etkin")
    except (AttributeError, OSError):
        log.debug("DPI: farkindalik ayarlanamadi (eski Windows olabilir)")


# ---------------------------------------------------------------------------
# SendInput yapilari — Unicode yazim ve guvenilir mouse icin (FIX #5)
# ---------------------------------------------------------------------------

ULONG_PTR = ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_ulong


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTunion)]


user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype  = wintypes.UINT


def _send_input(inp: INPUT):
    n = user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    if n != 1:
        err = ctypes.get_last_error()
        log.warning("SendInput basarisiz (err=%s)", err)
    return n


# ---------------------------------------------------------------------------
# Elevation (yonetici) tespiti — UIPI sessiz basarisizlik uyarisi
# ---------------------------------------------------------------------------

def is_elevated() -> bool:
    """Bu surec yonetici (elevated) olarak mi calisiyor?

    shell32.IsUserAnAdmin() — yeterli ve hizli. Erisilemezse False.
    """
    try:
        shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        return bool(shell32.IsUserAnAdmin())
    except (OSError, AttributeError):
        return False


def warn_if_uipi_risk():
    """Surec elevated DEGILSE uyar: elevated bir pencereye gonderilen
    SendInput/UIA, UIPI (User Interface Privilege Isolation) tarafindan
    SESSIZCE yutulur — komut '1' doner ama hicbir sey olmaz.

    Cozum: bu betigi yonetici komut isteminden calistir.
    Cagiran tarafa True/False doner; CLI bunu bir kez, baslangicta yazar.
    """
    if not is_elevated():
        log.debug("Surec elevated degil — elevated pencerelerde UIPI riski var")
        return False
    return True


# ---------------------------------------------------------------------------
# Temel mouse fonksiyonlari
# ---------------------------------------------------------------------------

def screen_size():
    """Birincil monitor boyutu."""
    return user32.GetSystemMetrics(SM_CXSCREEN), user32.GetSystemMetrics(SM_CYSCREEN)


def virtual_screen():
    """FIX #3: Tum sanal masaustu — cok monitorlu absolute hareket icin.

    Donus: (left, top, width, height)
    """
    return (
        user32.GetSystemMetrics(SM_XVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_YVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CXVIRTUALSCREEN),
        user32.GetSystemMetrics(SM_CYVIRTUALSCREEN),
    )


def to_absolute(x, y):
    """Sanal masaustune gore 0..65535 normalize — cok monitor dogru calisir."""
    left, top, w, h = virtual_screen()
    w = w or 1
    h = h or 1
    ax = int((x - left) * 65535 / w)
    ay = int((y - top) * 65535 / h)
    return ax, ay


def get_pos():
    pt = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


def move(x, y, steps=25, delay=0.008):
    """Yumusak mouse hareketi — SetCursorPos ile kademeli.

    FIX #2: steps <= 0 korumasi eklendi.
    """
    x, y = int(x), int(y)
    steps = max(1, int(steps))
    cx, cy = get_pos()
    for i in range(1, steps + 1):
        user32.SetCursorPos(
            int(cx + (x - cx) * i / steps),
            int(cy + (y - cy) * i / steps),
        )
        time.sleep(delay)
    user32.SetCursorPos(x, y)


def move_fast(x, y):
    """Tek atim mouse hareketi — SendInput absolute + VIRTUALDESK ile (--fast)."""
    ax, ay = to_absolute(x, y)
    mi = MOUSEINPUT(ax, ay, 0,
                    MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE | MOUSEEVENTF_VIRTUALDESK,
                    0, 0)
    _send_input(INPUT(INPUT_MOUSE, _INPUTunion(mi=mi)))


def _mouse_button(down_flag, up_flag, hold=0.05):
    """SendInput tabanli tek tiklama — mouse_event yerine (FIX #1)."""
    down = MOUSEINPUT(0, 0, 0, down_flag, 0, 0)
    up   = MOUSEINPUT(0, 0, 0, up_flag, 0, 0)
    _send_input(INPUT(INPUT_MOUSE, _INPUTunion(mi=down)))
    time.sleep(hold)
    _send_input(INPUT(INPUT_MOUSE, _INPUTunion(mi=up)))


def click(x, y):
    move(x, y)
    _mouse_button(MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP)


def rclick(x, y):
    move(x, y)
    _mouse_button(MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP)


def dclick(x, y):
    click(x, y)
    time.sleep(0.12)
    click(x, y)


def drag(x1, y1, x2, y2):
    """Sol tus basili tutarak surukle (yeni komut)."""
    move(x1, y1)
    down = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, 0)
    _send_input(INPUT(INPUT_MOUSE, _INPUTunion(mi=down)))
    time.sleep(0.08)
    move(x2, y2)
    time.sleep(0.08)
    up = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, 0)
    _send_input(INPUT(INPUT_MOUSE, _INPUTunion(mi=up)))


def scroll(delta):
    """WHEEL deltasi SendInput ile gonderilir.

    mouseData alani DWORD (c_uint32, isaretsiz). delta*120 negatif olabilir
    (asagi scroll); negatif Python int'i dogrudan c_uint32'ye atamak bazi
    ctypes surumlerinde OverflowError verir, bu yuzden 32-bit 2's-complement
    karsiligina elle ceviriyoruz. Bu maske dekorasyon degil, gereklidir.
    """
    raw = delta * 120
    wheel = MOUSEINPUT(0, 0, raw & 0xFFFFFFFF, MOUSEEVENTF_WHEEL, 0, 0)
    _send_input(INPUT(INPUT_MOUSE, _INPUTunion(mi=wheel)))


def sweep(cx=None, cy=None, r=220):
    if cx is None or cy is None:
        sw, sh = screen_size()
        cx = cx if cx is not None else sw // 2
        cy = cy if cy is not None else sh // 2
    print(f"Daire ciziliyor ({cx},{cy}) r={r}...", flush=True)
    for deg in range(0, 361, 2):
        rad = math.radians(deg)
        user32.SetCursorPos(
            int(cx + r * math.cos(rad)),
            int(cy + r * math.sin(rad))
        )
        time.sleep(0.010)
    print("Tamamlandi.")


# ---------------------------------------------------------------------------
# Ekran goruntusu — GDI ile, bagimliliksiz (BMP cikti)
# ---------------------------------------------------------------------------

# GDI sabitleri
SRCCOPY        = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB         = 0


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


def screenshot(path, region=None):
    """Ekran goruntusu al, BMP olarak kaydet (bagimliliksiz, GDI).

    region=None  -> tum sanal masaustu
    region=(x,y,w,h) -> belirli alan

    Donus: {"ok": True, "path": ..., "w": w, "h": h} veya {"error": ...}
    Critic Note: HDC/HBITMAP GDI nesneleri finally'de serbest birakilir;
                 sizdirma olmamasi icin DeleteObject/ReleaseDC zorunlu.
    """
    gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

    if region is None:
        vl, vt, vw, vh = virtual_screen()
    else:
        vl, vt, vw, vh = region
    if vw <= 0 or vh <= 0:
        return {"error": f"gecersiz bolge boyutu: {vw}x{vh}"}

    hdc_screen = None
    hdc_mem    = None
    hbmp       = None
    try:
        hdc_screen = user32.GetDC(0)
        hdc_mem    = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp       = gdi32.CreateCompatibleBitmap(hdc_screen, vw, vh)
        gdi32.SelectObject(hdc_mem, hbmp)
        ok = gdi32.BitBlt(hdc_mem, 0, 0, vw, vh,
                          hdc_screen, vl, vt, SRCCOPY)
        if not ok:
            return {"error": f"BitBlt basarisiz (err={ctypes.get_last_error()})"}

        # 24-bit, alt-ust ters (negatif height ile duzeltilir)
        bmi = BITMAPINFOHEADER()
        bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.biWidth = vw
        bmi.biHeight = -vh  # top-down
        bmi.biPlanes = 1
        bmi.biBitCount = 24
        bmi.biCompression = BI_RGB

        row_stride = ((vw * 3 + 3) // 4) * 4  # 4-byte hizalama
        buf_size = row_stride * vh
        buffer = (ctypes.c_char * buf_size)()

        got = gdi32.GetDIBits(hdc_mem, hbmp, 0, vh, buffer,
                              ctypes.byref(bmi), DIB_RGB_COLORS)
        if got == 0:
            return {"error": "GetDIBits basarisiz"}

        # BMP dosya basligi (14) + info header (40) + piksel
        file_size = 14 + 40 + buf_size
        path = os.path.abspath(path)
        with open(path, "wb") as f:
            # BITMAPFILEHEADER
            f.write(b"BM")
            f.write(file_size.to_bytes(4, "little"))
            f.write((0).to_bytes(4, "little"))
            f.write((14 + 40).to_bytes(4, "little"))  # piksel offset
            # BITMAPINFOHEADER (biHeight pozitif yaz, veri zaten top-down)
            f.write(bytes(bmi)[:4])                    # biSize
            f.write(vw.to_bytes(4, "little", signed=True))
            f.write((-vh).to_bytes(4, "little", signed=True))
            f.write((1).to_bytes(2, "little"))         # planes
            f.write((24).to_bytes(2, "little"))        # bitcount
            f.write((0).to_bytes(4, "little"))         # compression
            f.write(buf_size.to_bytes(4, "little"))
            f.write((0).to_bytes(4, "little"))         # xppm
            f.write((0).to_bytes(4, "little"))         # yppm
            f.write((0).to_bytes(4, "little"))         # clrused
            f.write((0).to_bytes(4, "little"))         # clrimportant
            f.write(buffer.raw)

        return {"ok": True, "path": path, "w": vw, "h": vh}
    except OSError as e:
        return {"error": f"screenshot OSError: {e}"}
    finally:
        if hbmp:       gdi32.DeleteObject(hbmp)
        if hdc_mem:    gdi32.DeleteDC(hdc_mem)
        if hdc_screen: user32.ReleaseDC(0, hdc_screen)


# ---------------------------------------------------------------------------
# Klavye — ozel tuslar ve kisayollar (key komutu icin)
# ---------------------------------------------------------------------------

# Sanal-Tus (VK) kodlari — yaygin tuslar. Tam liste MS docs'ta.
_VK = {
    "enter": 0x0D, "return": 0x0D, "tab": 0x09, "esc": 0x1B, "escape": 0x1B,
    "space": 0x20, "backspace": 0x08, "bksp": 0x08, "delete": 0x2E, "del": 0x2E,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "insert": 0x2D, "ins": 0x2D, "printscreen": 0x2C, "pause": 0x13,
    "capslock": 0x14, "numlock": 0x90,
    # modifier'lar
    "ctrl": 0x11, "control": 0x11, "alt": 0x12, "shift": 0x10,
    "win": 0x5B, "lwin": 0x5B, "rwin": 0x5C,
}
# F1..F24
for _n in range(1, 25):
    _VK[f"f{_n}"] = 0x70 + (_n - 1)
# 0..9 ve a..z dogrudan ASCII upper VK kodu
for _c in "0123456789":
    _VK[_c] = ord(_c)
for _c in "abcdefghijklmnopqrstuvwxyz":
    _VK[_c] = ord(_c.upper())

_MODIFIERS = {"ctrl", "control", "alt", "shift", "win", "lwin", "rwin"}


def _vk_down(vk):
    ki = KEYBDINPUT(vk, 0, 0, 0, 0)
    _send_input(INPUT(INPUT_KEYBOARD, _INPUTunion(ki=ki)))


def _vk_up(vk):
    ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP, 0, 0)
    _send_input(INPUT(INPUT_KEYBOARD, _INPUTunion(ki=ki)))


def press_key(combo):
    """Tek tus veya kisayol gonder.

    Ornekler: 'enter', 'esc', 'tab', 'ctrl+c', 'ctrl+shift+esc', 'alt+f4'.
    Modifier'lar basili tutulur, ana tus basilip birakilir, sonra modifier'lar
    ters sirada birakilir (gercek tuş davranisi).

    Donus: True basarili, False taninmayan tus.
    """
    parts = [p.strip().lower() for p in combo.split("+") if p.strip()]
    if not parts:
        return False

    mods = [p for p in parts if p in _MODIFIERS]
    keys = [p for p in parts if p not in _MODIFIERS]

    unknown = [k for k in parts if k not in _VK]
    if unknown:
        log.warning("Taninmayan tus: %s", ", ".join(unknown))
        return False

    # Modifier'lari bas
    for m in mods:
        _vk_down(_VK[m])
    # Ana tuslari bas+birak
    for k in keys:
        _vk_down(_VK[k])
        time.sleep(0.02)
        _vk_up(_VK[k])
    # Modifier'lari ters sirada birak
    for m in reversed(mods):
        _vk_up(_VK[m])
    return True


def type_text(text, delay=0.01):
    """Metin yaz — Unicode SendInput ile (FIX #5).

    VkKeyScanW yerine KEYEVENTF_UNICODE kullanir; mevcut klavye duzeninde
    olmayan karakterler (Turkce ge/se/ce vb.) artik dogru yazilir.

    Ctrl+C ile guvenle kesilebilir: kesilme aninda hangi indekste durduldugu
    bildirilir, yarim kalan tus yukari (KEYUP) gonderilir — takili tus kalmaz.

    Critic Note: her INPUT yapisinin yasam suresi iterasyon sonunda biter;
                 dis referans tutulmaz, GC'ye guvenle birakilir.
    """
    i = 0
    try:
        for i, ch in enumerate(text):
            code = ord(ch)
            # BMP disi karakterler (emoji vb.) icin surrogate pair gerekir
            if code > 0xFFFF:
                code -= 0x10000
                units = [0xD800 + (code >> 10), 0xDC00 + (code & 0x3FF)]
            else:
                units = [code]
            for unit in units:
                down = KEYBDINPUT(0, unit, KEYEVENTF_UNICODE, 0, 0)
                up   = KEYBDINPUT(0, unit, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, 0)
                _send_input(INPUT(INPUT_KEYBOARD, _INPUTunion(ki=down)))
                _send_input(INPUT(INPUT_KEYBOARD, _INPUTunion(ki=up)))
                time.sleep(delay)
    except KeyboardInterrupt:
        # Yarim kalmis olabilecek son tusu serbest birak; takili tus onle
        log.warning("type_text kesildi (indeks %d/%d)", i, len(text))
        print(f"\n[kesildi] {i}/{len(text)} karakter yazildi", file=sys.stderr)
        return i
    return len(text)


# ---------------------------------------------------------------------------
# Element Secimi — UI Automation (PowerShell + .NET)
# ---------------------------------------------------------------------------

_UIA_PS_SCRIPT = r"""
param([string]$ParamFile)

$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$params      = Get-Content $ParamFile -Raw | ConvertFrom-Json
$windowTitle = $params.windowTitle
$elementId   = $params.elementId
$searchBy    = $params.searchBy
$action      = $params.action

$desktop = [System.Windows.Automation.AutomationElement]::RootElement

# --------------- Pencereyi bul ---------------
$winCond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NameProperty, $windowTitle,
    [System.Windows.Automation.PropertyConditionFlags]::IgnoreCase)

$window = $desktop.FindFirst(
    [System.Windows.Automation.TreeScope]::Children, $winCond)

if (-not $window) {
    $typeProp = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::Window)
    $allWins = $desktop.FindAll(
        [System.Windows.Automation.TreeScope]::Children, $typeProp)
    foreach ($w in $allWins) {
        if ($w.Current.Name -match [regex]::Escape($windowTitle)) {
            $window = $w; break
        }
    }
}

if (-not $window) {
    Write-Output (@{error="Window not found"; window=$windowTitle} | ConvertTo-Json -Compress)
    exit 1
}

# --------------- LIST modu ---------------
if ($action -eq 'list') {
    $allElems = $window.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    $results = @()
    foreach ($e in $allElems) {
        $r = $e.Current.BoundingRectangle
        if ($r -and $r.Width -gt 0 -and $r.Height -gt 0) {
            $results += [ordered]@{
                name = $e.Current.Name
                aid  = $e.Current.AutomationId
                ct   = $e.Current.ControlType.ProgrammaticName
                cls  = $e.Current.ClassName
                x    = [int]$r.X
                y    = [int]$r.Y
                w    = [int]$r.Width
                h    = [int]$r.Height
            }
        }
    }
    # FIX: tek elemanli dizinin JSON'da nesneye dusmesini onle (@() sarmasi)
    Write-Output (ConvertTo-Json @($results) -Compress -Depth 4)
    exit 0
}

# --------------- FIND modu ---------------
$propMap = @{
    'Name'         = [System.Windows.Automation.AutomationElement]::NameProperty
    'AutomationId' = [System.Windows.Automation.AutomationElement]::AutomationIdProperty
    'ClassName'    = [System.Windows.Automation.AutomationElement]::ClassNameProperty
}

if ($searchBy -eq 'ControlType') {
    $ctField = [System.Windows.Automation.ControlType].GetField(
        $elementId,
        [System.Reflection.BindingFlags]'Public,Static')
    if (-not $ctField) {
        Write-Output (@{error="Unknown ControlType"; value=$elementId} | ConvertTo-Json -Compress)
        exit 1
    }
    $ctValue  = $ctField.GetValue($null)
    $elemCond = New-Object System.Windows.Automation.PropertyCondition(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        $ctValue)
} elseif ($propMap.ContainsKey($searchBy)) {
    $elemCond = New-Object System.Windows.Automation.PropertyCondition(
        $propMap[$searchBy], $elementId,
        [System.Windows.Automation.PropertyConditionFlags]::IgnoreCase)
} else {
    Write-Output (@{error="Unknown searchBy"; value=$searchBy} | ConvertTo-Json -Compress)
    exit 1
}

$elem = $window.FindFirst(
    [System.Windows.Automation.TreeScope]::Descendants, $elemCond)

if (-not $elem) {
    $all2 = $window.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($e in $all2) {
        if ($e.Current.Name -match [regex]::Escape($elementId)) {
            $elem = $e; break
        }
    }
}

if (-not $elem) {
    Write-Output (@{error="Element not found"; searchBy=$searchBy; id=$elementId} | ConvertTo-Json -Compress)
    exit 1
}

$r  = $elem.Current.BoundingRectangle
$cx = [int]($r.X + $r.Width  / 2)
$cy = [int]($r.Y + $r.Height / 2)

Write-Output (@{
    ok   = $true
    x    = $cx
    y    = $cy
    w    = [int]$r.Width
    h    = [int]$r.Height
    name = $elem.Current.Name
    aid  = $elem.Current.AutomationId
} | ConvertTo-Json -Compress)
exit 0
"""


def _decode_ps_bytes(raw_bytes: bytes) -> str:
    """PowerShell stdout decode — UTF-8 varyantlari once, sonra sistem kodlamasi."""
    for enc in ("utf-8-sig", "utf-8", "cp1254", "cp1252"):
        try:
            decoded = raw_bytes.decode(enc).strip()
            if decoded:
                return decoded
        except (UnicodeDecodeError, LookupError):
            continue
    return raw_bytes.decode("utf-8", errors="replace").strip()


def _run_uia(window_title: str, element_id: str = "",
             search_by: str = "Name", action: str = "find") -> dict:
    """PowerShell UIA alt sureci. Parametreler temp JSON ile gecilir.

    Critic Note: tmp_param/tmp_script finally blogunda silinir; subprocess
                 referansi fonksiyon scope'u biterken GC'ye birakilir.
    """
    params = {
        "windowTitle": window_title,
        "elementId":   element_id,
        "searchBy":    search_by,
        "action":      action,
    }

    tmp_param  = None
    tmp_script = None
    raw        = ""

    try:
        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(params, f, ensure_ascii=False)
            tmp_param = f.name

        with tempfile.NamedTemporaryFile(
                mode="w", suffix=".ps1", delete=False, encoding="utf-8") as f:
            f.write(_UIA_PS_SCRIPT)
            tmp_script = f.name

        log.debug("UIA cagrisi: window=%r id=%r by=%s action=%s",
                  window_title, element_id, search_by, action)

        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass",
             "-File", tmp_script,
             "-ParamFile", tmp_param],
            capture_output=True, text=False, timeout=15
        )

        raw = _decode_ps_bytes(result.stdout or b"")

        if not raw:
            err_bytes = (result.stderr or b"") + (result.stdout or b"")
            err = err_bytes.decode("utf-8", errors="replace").strip()
            return {"error": f"No output from PowerShell: {err}"}

        return json.loads(raw)

    except FileNotFoundError:
        return {"error": "PowerShell bulunamadi (bu komut yalnizca Windows'ta calisir)"}
    except subprocess.TimeoutExpired:
        return {"error": "PowerShell timeout (15s)"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}", "raw": raw[:200]}
    finally:
        for path in (tmp_param, tmp_script):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# Python API — dogrudan import edilebilir
# ---------------------------------------------------------------------------

_UIA_EMPTY_HINT = (
    "  ipucu: Bu pencere UI Automation'a kapali gorunuyor. LM Studio, VS Code, "
    "Discord, Slack gibi\n"
    "  Electron/Chrome tabanli uygulamalarda element agaci bos gelir. Secenekler:\n"
    "    1) Koordinatla calis: once 'screenshot' al, butonun yerini gor, "
    "'click <x> <y>' kullan\n"
    "    2) Varsa uygulamanin kendi CLI'sini kullan (or. LM Studio icin 'lms load ...')\n"
    "    3) Native (Win32) pencerelerde (Not Defteri, klasik uygulamalar) "
    "element bulma calisir"
)


def _looks_electron_empty(window_title):
    """Pencere VAR ama icinde hic gorunur element YOKSA True — UIA-kapali
    (Electron/Chrome) gostergesi. Pencere hic yoksa False (bu farkli bir hata).
    """
    listing = _run_uia(window_title, "", "Name", action="list")
    if isinstance(listing, dict) and "error" in listing:
        return False  # pencere yok ya da baska hata; Electron tanisi koyma
    return isinstance(listing, list) and len(listing) == 0


def find_element(window_title, element_id, search_by="Name", timeout=0.0):
    """Element bul, bounding box merkezini don.

    timeout > 0 ise element bulunana kadar ~0.5sn araliklarla yeniden dener
    (yeni acilan pencere/gecikmeli yuklenen UI icin).

    Element bulunamaz VE pencerede hic element yoksa, hataya Electron/UIA-kapali
    isareti eklenir ("hint": "electron_empty") — sessizce bos donmek yerine
    cagiran tarafa dogru yolu gosterme imkani verir.

    Donus: {"x": cx, "y": cy, "w": w, "h": h, "name": "...", "aid": "..."}
    veya   {"error": "...", "hint": "..."(opsiyonel)}
    """
    deadline = time.time() + max(0.0, timeout)
    while True:
        result = _run_uia(window_title, element_id, search_by, action="find")
        if "error" not in result:
            return result
        if time.time() >= deadline:
            if _looks_electron_empty(window_title):
                result["hint"] = "electron_empty"
            return result
        time.sleep(0.5)


def list_elements(window_title):
    """Penceredeki tum gorunur UI elementlerini listele.

    FIX #6: tutarli donus — basari her zaman list, hata her zaman {"error":...}.
    """
    result = _run_uia(window_title, "", "Name", action="list")
    if isinstance(result, list):
        return result
    if isinstance(result, dict) and "error" in result:
        return result
    # Tek nesne dondurulduyse (eski PS surumu) listeye sar
    return [result] if isinstance(result, dict) else []


def element_click(window_title, element_id, search_by="Name", timeout=0.0):
    """Elementi bul, uzerine git ve tikla."""
    result = find_element(window_title, element_id, search_by, timeout)
    if "error" in result:
        print(f"HATA: {result['error']}", flush=True)
        return False
    click(result["x"], result["y"])
    print(f"clicked '{element_id}' at ({result['x']},{result['y']})", flush=True)
    return True


def element_move(window_title, element_id, search_by="Name", timeout=0.0):
    """Elementi bul, uzerine git (tiklamadan)."""
    result = find_element(window_title, element_id, search_by, timeout)
    if "error" in result:
        print(f"HATA: {result['error']}", flush=True)
        return False
    move(result["x"], result["y"])
    print(f"moved to '{element_id}' at ({result['x']},{result['y']})", flush=True)
    return True


def save_elements(window_title, out_path):
    """Penceredeki elementleri JSON dosyasina aktar (otomasyon kesfi icin)."""
    data = list_elements(window_title)
    if isinstance(data, dict) and "error" in data:
        return data
    out_path = os.path.abspath(out_path)  # cwd belirsizligini kaldir
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return {"ok": True, "count": len(data), "path": out_path}


# ---------------------------------------------------------------------------
# WORKFLOW MOTORU — otonom adim dizisi yurutucu
# ---------------------------------------------------------------------------
#
# Bir is akisi = adim listesi. Her adim bir dict:
#   {"do": "click", "window": "Ayarlar", "target": "Tamam",
#    "by": "Name", "on_error": "stop", "timeout": 2}
#
# Desteklenen 'do' tipleri:
#   click / dclick / rclick  -> element bul + tikla
#   move                     -> element uzerine git
#   type                     -> "text" alanini yaz
#   key                      -> "keys" alanini gonder (ornn "ctrl+s", "esc")
#   wait                     -> "seconds" kadar bekle
#   if_exists                -> element VARSA "then" alt-eylemini yap, yoksa atla
#                               (dialog kapatma icin: dialog varsa Kapat'a bas)
#
# Ortak alanlar:
#   on_error: "stop" (varsayilan) | "skip"   -- adim bazinda
#   by:       Name | AutomationId | ClassName | ControlType  (varsayilan Name)
#   timeout:  element arama yeniden deneme suresi (sn, varsayilan 0)
# ---------------------------------------------------------------------------

_WF_VALID_DO = {"click", "dclick", "rclick", "move", "type", "key",
                "wait", "if_exists", "screenshot", "assert", "repeat", "shell"}


def _wf_do_element_action(do, window, target, by, timeout):
    """click/dclick/rclick/move ortak yurutucusu. (ok: bool, mesaj) doner."""
    result = find_element(window, target, by, timeout)
    if "error" in result:
        msg = result["error"]
        if result.get("hint") == "electron_empty":
            msg += " [pencere UIA'ya kapali (Electron?); koordinatla ya da 'shell' adimiyla dene]"
        return False, msg
    x, y = result["x"], result["y"]
    if do == "click":
        click(x, y)
    elif do == "dclick":
        dclick(x, y)
    elif do == "rclick":
        rclick(x, y)
    elif do == "move":
        move(x, y)
    return True, f"{do} '{target}' @({x},{y})"


def run_step(step, index):
    """Tek adim yurut. (ok: bool, mesaj: str) doner.

    'stop' politikasinda basarisizlik motoru durdurur; 'skip'te atlanir.
    Critic Note: her adim bagimsiz; durum tutulmaz, dis referans birakmaz.
    """
    if not isinstance(step, dict):
        return False, f"adim {index}: dict bekleniyordu, {type(step).__name__} geldi"

    do = str(step.get("do", "")).lower()
    if do not in _WF_VALID_DO:
        return False, f"adim {index}: bilinmeyen 'do': {do!r}"

    by      = step.get("by", "Name")
    timeout = float(step.get("timeout", 0))
    window  = step.get("window", "")

    # --- wait ---
    if do == "wait":
        secs = float(step.get("seconds", 1))
        time.sleep(secs)
        return True, f"wait {secs}s"

    # --- key ---
    if do == "key":
        combo = step.get("keys", "")
        ok = press_key(combo)
        return ok, (f"key '{combo}'" if ok else f"taninmayan tus: {combo!r}")

    # --- type ---
    if do == "type":
        txt = step.get("text", "")
        type_text(txt)
        return True, f"type ({len(txt)} krk)"

    # --- screenshot: ekran goruntusu al ---
    if do == "screenshot":
        sc_path = step.get("path") or f"hermes_{int(time.time())}.bmp"
        res = screenshot(sc_path)
        if "error" in res:
            return False, f"screenshot: {res['error']}"
        return True, f"screenshot -> {res['path']} ({res['w']}x{res['h']})"

    # --- shell: harici CLI komutu calistir ---
    #   Electron/UIA-kapali uygulamalarin GERCEK cozumu: uygulamanin kendi
    #   CLI'sini cagir (or. LM Studio icin "lms load ...").
    #   {"do":"shell","cmd":"lms load model-adi","timeout":30,"expect_code":0}
    if do == "shell":
        cmd = step.get("cmd", "")
        if not cmd:
            return False, f"adim {index}: shell icin 'cmd' gerekli"
        sh_timeout = float(step.get("timeout", 30))
        expect_code = step.get("expect_code", 0)
        try:
            proc = subprocess.run(cmd, shell=True, capture_output=True,
                                  text=True, timeout=sh_timeout)
        except subprocess.TimeoutExpired:
            return False, f"shell zaman asimi ({sh_timeout}s): {cmd}"
        out = (proc.stdout or "").strip()
        snippet = (out[:120] + "...") if len(out) > 120 else out
        if expect_code is not None and proc.returncode != expect_code:
            err = (proc.stderr or "").strip()[:120]
            return False, (f"shell cikis {proc.returncode} (beklenen {expect_code}): "
                           f"{cmd} | {err}")
        return True, f"shell ok: {cmd}" + (f" | {snippet}" if snippet else "")

    # --- assert: element OLMALI (expect=present) ya da OLMAMALI (absent) ---
    if do == "assert":
        target = step.get("target", "")
        expect = str(step.get("expect", "present")).lower()
        if not target:
            return False, f"adim {index}: assert icin 'target' gerekli"
        probe = find_element(window, target, by, timeout)
        exists = "error" not in probe
        if expect == "present":
            return (exists,
                    f"assert '{target}' var" if exists
                    else f"assert BASARISIZ: '{target}' bulunamadi")
        elif expect == "absent":
            return (not exists,
                    f"assert '{target}' yok (beklendigi gibi)" if not exists
                    else f"assert BASARISIZ: '{target}' hala var")
        return False, f"adim {index}: assert 'expect' present|absent olmali"

    # --- repeat: alt-eylemi N kez tekrarla ---
    if do == "repeat":
        times = int(step.get("times", 1))
        sub = step.get("step") or step.get("then")
        if not sub:
            return False, f"adim {index}: repeat icin 'step' gerekli"
        sub = dict(sub)
        sub.setdefault("window", window)
        done = 0
        for n in range(times):
            ok, msg = run_step(sub, f"{index}.rep{n + 1}")
            if not ok:
                return False, f"repeat {done}/{times} sonra basarisiz: {msg}"
            done += 1
            time.sleep(float(step.get("interval", 0.2)))
        return True, f"repeat x{done}: {sub.get('do')}"

    # --- if_exists: element varsa then alt-eylemini yap, yoksa atla ---
    if do == "if_exists":
        target = step.get("target", "")
        probe = find_element(window, target, by, timeout)
        if "error" in probe:
            return True, f"if_exists '{target}': yok, atlandi"
        then = step.get("then")
        if not then:
            # then yoksa sadece varligini dogrula
            return True, f"if_exists '{target}': var"
        # then bir alt-adim; ayni window'u miras al, ozyinele
        sub = dict(then)
        sub.setdefault("window", window)
        ok, msg = run_step(sub, f"{index}.then")
        return ok, f"if_exists '{target}': var -> {msg}"

    # --- click / dclick / rclick / move ---
    target = step.get("target", "")
    if not target:
        return False, f"adim {index}: '{do}' icin 'target' gerekli"
    if not window:
        return False, f"adim {index}: '{do}' icin 'window' gerekli"
    return _wf_do_element_action(do, window, target, by, timeout)


def run_workflow(steps, default_pause=0.3, dry_run=False,
                 shot_on_error=True, log_path=None):
    """Adim listesini sirayla yurut.

    on_error: "stop" (vars.) basarisizlikta durur; "skip" atlar ve devam eder.
    dry_run:  adimlari YURUTMEDEN dogrula (gecersiz adim/eksik alan yakalar).
    shot_on_error: bir adim 'stop' ile akisi durdurursa otomatik ekran goruntusu.
    log_path: verilirse her adimin zaman damgali JSON kaydi buraya yazilir.

    Donus: {"ran","ok","failed","stopped_at","log":[...]}
    """
    ran = ok_count = failed = 0
    stopped_at = None
    run_log = []
    t0 = time.time()

    for i, step in enumerate(steps, 1):
        policy = str((step or {}).get("on_error", "stop")).lower() \
            if isinstance(step, dict) else "stop"
        ran += 1

        if dry_run:
            # Yurutme yok; sadece yapisal dogrulama
            valid = isinstance(step, dict) and \
                str(step.get("do", "")).lower() in _WF_VALID_DO
            ok = valid
            msg = (f"[dry] {step.get('do')} '{step.get('target', step.get('keys', ''))}'"
                   if valid else f"[dry] GECERSIZ adim: {step}")
        else:
            try:
                ok, msg = run_step(step, i)
            except KeyboardInterrupt:
                print(f"\n[kesildi] adim {i}", file=sys.stderr)
                stopped_at = i
                run_log.append({"i": i, "ok": False, "msg": "kesildi",
                                "t": round(time.time() - t0, 2)})
                break
            except Exception as e:  # tek adim cokerse tum akis cokmesin
                ok, msg = False, f"istisna: {e}"

        tag = "OK " if ok else "HATA"
        print(f"  [{i}/{len(steps)}] {tag} {msg}", flush=True)
        run_log.append({"i": i, "ok": ok, "msg": msg,
                        "do": (step.get("do") if isinstance(step, dict) else None),
                        "t": round(time.time() - t0, 2)})

        if ok:
            ok_count += 1
        else:
            failed += 1
            if policy == "skip":
                print(f"       on_error=skip -> devam", flush=True)
            else:
                print(f"       on_error=stop -> akis durduruldu", file=sys.stderr)
                # Hata anini goruntule (tani icin)
                if shot_on_error and not dry_run:
                    shot = screenshot(f"hermes_hata_adim{i}_{int(time.time())}.bmp")
                    if "ok" in shot:
                        print(f"       hata goruntusu -> {shot['path']}",
                              file=sys.stderr)
                stopped_at = i
                break

        if not dry_run:
            time.sleep(default_pause)

    summary = {"ran": ran, "ok": ok_count, "failed": failed,
               "stopped_at": stopped_at, "log": run_log}

    if log_path:
        try:
            log_path = os.path.abspath(log_path)
            with open(log_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"  akis logu -> {log_path}", flush=True)
        except OSError as e:
            log.warning("akis logu yazilamadi: %s", e)

    return summary


# --- Akis dosyasi yukleyiciler: JSON ve basit metin ---

def load_workflow_json(path):
    """JSON akis dosyasi yukle. Bicim:
      {"steps": [ {...}, {...} ], "pause": 0.3}   veya  dogrudan [ {...}, ... ]
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data, 0.3
    return data.get("steps", []), float(data.get("pause", 0.3))


def load_workflow_text(path):
    """Basit metin akis dosyasi yukle. Her satir bir adim:

      # yorum satiri
      wait 2
      key esc
      click "Ayarlar" | "Tamam"
      click "Ayarlar" | "Tamam" | AutomationId | skip
      type "Ayarlar" | "merhaba"          (type icin target=metin)
      if_exists "Uygulama" | "Kapat" -> click

    Bicim: <do> "<window>" | "<target>" [| <by>] [| stop|skip]
    type:  <do> "<window>" | "<metin>"
    key:   key <kombinasyon>
    wait:  wait <saniye>
    if_exists: if_exists "<window>" | "<target>" -> <do>
    Tirnaklar opsiyonel ama bosluk iceren degerlerde onerilir.
    """
    steps = []

    def _strip_q(s):
        s = s.strip()
        if len(s) >= 2 and s[0] in "\"'" and s[-1] == s[0]:
            return s[1:-1]
        return s

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            head, _, rest = line.partition(" ")
            do = head.lower()

            if do == "wait":
                steps.append({"do": "wait", "seconds": float(_strip_q(rest) or 1)})
                continue
            if do == "key":
                steps.append({"do": "key", "keys": _strip_q(rest)})
                continue
            if do == "shell":
                # shell <komut...>  (komut tirnak gerektirmez, satir sonuna kadar)
                steps.append({"do": "shell", "cmd": rest.strip()})
                continue
            if do == "screenshot":
                # screenshot [dosya.bmp]
                p = _strip_q(rest)
                step = {"do": "screenshot"}
                if p:
                    step["path"] = p
                steps.append(step)
                continue
            if do == "assert":
                # assert "Win" | "Target" [| present|absent]
                fields = [_strip_q(p) for p in rest.split("|")]
                step = {"do": "assert",
                        "window": fields[0] if fields else "",
                        "target": fields[1] if len(fields) > 1 else ""}
                if len(fields) > 2 and fields[2].strip().lower() in ("present", "absent"):
                    step["expect"] = fields[2].strip().lower()
                steps.append(step)
                continue

            # if_exists "Win" | "Target" -> click
            if do == "if_exists":
                body, _, thendo = rest.partition("->")
                fields = [_strip_q(p) for p in body.split("|")]
                step = {"do": "if_exists",
                        "window": fields[0] if fields else "",
                        "target": fields[1] if len(fields) > 1 else ""}
                if len(fields) > 2 and fields[2]:
                    step["by"] = fields[2]
                if thendo.strip():
                    step["then"] = {"do": thendo.strip().lower(),
                                    "target": step["target"]}
                steps.append(step)
                continue

            # genel: <do> "win" | "target" [| by] [| stop|skip]
            fields = [_strip_q(p) for p in rest.split("|")]
            if do == "type":
                steps.append({"do": "type",
                              "window": fields[0] if fields else "",
                              "text": fields[1] if len(fields) > 1 else ""})
                continue

            step = {"do": do,
                    "window": fields[0] if fields else "",
                    "target": fields[1] if len(fields) > 1 else ""}
            for extra in fields[2:]:
                ex = extra.strip().lower()
                if ex in ("stop", "skip"):
                    step["on_error"] = ex
                elif extra.strip() in _VALID_SEARCH_BY:
                    step["by"] = extra.strip()
            steps.append(step)

    return steps, 0.3


def load_workflow(path):
    """Uzantiya gore JSON ya da metin yukle."""
    if path.lower().endswith(".json"):
        return load_workflow_json(path)
    return load_workflow_text(path)


# ---------------------------------------------------------------------------
# CLI yardimci
# ---------------------------------------------------------------------------

def _parse_by(args):
    """--by parametresini ara, dogrula; yoksa 'Name' don."""
    if "--by" in args:
        idx = args.index("--by")
        if idx + 1 < len(args):
            val = args[idx + 1]
            if val not in _VALID_SEARCH_BY:
                print(f"HATA: gecersiz --by '{val}'. "
                      f"Gecerli: {', '.join(sorted(_VALID_SEARCH_BY))}", file=sys.stderr)
                sys.exit(2)
            return val
    return "Name"


def _parse_timeout(args):
    """--timeout N (saniye); yoksa 0."""
    if "--timeout" in args:
        idx = args.index("--timeout")
        if idx + 1 < len(args):
            try:
                return max(0.0, float(args[idx + 1]))
            except ValueError:
                print("HATA: --timeout sayisal olmali.", file=sys.stderr)
                sys.exit(2)
    return 0.0


def _parse_action(args, start=3):
    """args[start]'tan itibaren flag olmayan ilk action keyword'unu bul."""
    skip_next = False
    for i in range(start, len(args)):
        token = args[i]
        if skip_next:
            skip_next = False
            continue
        if token in ("--by", "--timeout"):
            skip_next = True  # bir sonraki token bu flag'in degeri, atla
            continue
        if token.startswith("--"):
            continue
        if token.lower() in _ACTION_KEYWORDS:
            return token.lower()
    return "click"


def _print_find_error(result):
    """find_element hatasini bas; electron_empty ipucu varsa yol goster."""
    print(f"HATA: {result['error']}", file=sys.stderr)
    if result.get("hint") == "electron_empty":
        print(_UIA_EMPTY_HINT, file=sys.stderr)


def _print_elements(result):
    if isinstance(result, list):
        if not result:
            print("(gorunur element bulunamadi)")
            print(_UIA_EMPTY_HINT, file=sys.stderr)
            return
        for e in result:
            ct = e.get("ct", "?").replace("System.Windows.Automation.ControlType.", "")
            print(f"  [{ct}] \"{e.get('name','')}\"  "
                  f"aid={e.get('aid','-')}  "
                  f"pos=({e.get('x',0)},{e.get('y',0)})  "
                  f"size={e.get('w',0)}x{e.get('h',0)}")
    else:
        print(f"HATA: {result.get('error', 'Bilinmeyen hata')}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]

    # Global flag'ler — DPI/elevation loglarinin gorunmesi icin
    # _setup_ctypes()'tan ONCE ayarlanir
    if "--verbose" in args:
        logging.basicConfig(level=logging.DEBUG,
                            format="[%(levelname)s] %(message)s")
        args = [a for a in args if a != "--verbose"]

    _setup_ctypes()  # DPI awareness burada etkinlesir
    log.debug("elevated=%s", is_elevated())

    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0].lower()

    # --- Temel mouse komutlari ---

    if cmd == "pos":
        x, y = get_pos()
        print(f"{x} {y}")

    elif cmd == "status":
        # Tani: ekran, DPI farkindalik, elevation durumu
        sw, sh = screen_size()
        vl, vt, vw, vh = virtual_screen()
        elev = is_elevated()
        print(f"Birincil ekran : {sw}x{sh}")
        print(f"Sanal masaustu : {vw}x{vh} (sol={vl}, ust={vt})")
        print(f"Yonetici (elevated): {'EVET' if elev else 'HAYIR'}")
        if not elev:
            print("  not: elevated pencerelerde tiklama/yazma etkisiz kalabilir.")

    elif cmd == "move" and len(args) >= 3:
        if "--fast" in args:
            move_fast(int(args[1]), int(args[2]))
        else:
            move(int(args[1]), int(args[2]))
        print(f"moved {args[1]} {args[2]}")

    elif cmd == "drag" and len(args) >= 5:
        drag(int(args[1]), int(args[2]), int(args[3]), int(args[4]))
        print(f"dragged ({args[1]},{args[2]}) -> ({args[3]},{args[4]})")

    elif cmd == "click" and len(args) >= 3:
        click(int(args[1]), int(args[2]))
        print(f"clicked {args[1]} {args[2]}")

    elif cmd == "rclick" and len(args) >= 3:
        rclick(int(args[1]), int(args[2]))
        print("rclicked")

    elif cmd == "dclick" and len(args) >= 3:
        dclick(int(args[1]), int(args[2]))
        print("dclicked")

    elif cmd == "scroll" and len(args) >= 2:
        scroll(int(args[1]))
        print(f"scrolled {args[1]}")

    elif cmd == "sweep":
        extra = [int(a) for a in args[1:4] if a.lstrip("-").isdigit()]
        sweep(*extra)

    elif cmd == "type" and len(args) >= 2:
        type_text(" ".join(args[1:]))
        print("typed")

    elif cmd == "key" and len(args) >= 2:
        # python hermesmouse.py key enter
        # python hermesmouse.py key "ctrl+s"
        combo = args[1]
        if press_key(combo):
            print(f"key '{combo}'")
        else:
            print(f"HATA: taninmayan tus: {combo}", file=sys.stderr)
            sys.exit(1)

    elif cmd == "screenshot":
        # python hermesmouse.py screenshot [dosya.bmp]
        out = args[1] if len(args) >= 2 and not args[1].startswith("--") \
            else f"hermes_{int(time.time())}.bmp"
        res = screenshot(out)
        if "error" in res:
            print(f"HATA: {res['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"[OK] ekran goruntusu -> {res['path']} ({res['w']}x{res['h']})")

    elif cmd == "run" and len(args) >= 2:
        # python hermesmouse.py run akis.json [--dry-run] [--log log.json]
        wf_path = args[1]
        dry = "--dry-run" in args
        log_path = None
        if "--log" in args:
            li = args.index("--log")
            if li + 1 < len(args):
                log_path = args[li + 1]
        if not os.path.exists(wf_path):
            print(f"HATA: akis dosyasi bulunamadi: {wf_path}", file=sys.stderr)
            sys.exit(1)
        try:
            steps, pause = load_workflow(wf_path)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"HATA: akis dosyasi okunamadi: {e}", file=sys.stderr)
            sys.exit(1)
        if not steps:
            print("HATA: akiste hic adim yok.", file=sys.stderr)
            sys.exit(1)
        if dry:
            print(f"DRY-RUN: {len(steps)} adim dogrulaniyor (yurutme yok)")
        else:
            if not is_elevated():
                print("[uyari] Surec yonetici degil; elevated pencerelerde adimlar "
                      "etkisiz kalabilir.", file=sys.stderr)
            print(f"Akis baslatiliyor: {len(steps)} adim ({os.path.basename(wf_path)})")
        summary = run_workflow(steps, default_pause=pause,
                               dry_run=dry, log_path=log_path)
        print(f"\nOzet: {summary['ok']}/{summary['ran']} basarili, "
              f"{summary['failed']} hata"
              + (f", adim {summary['stopped_at']}'de durdu"
                 if summary["stopped_at"] else ""))
        sys.exit(0 if summary["failed"] == 0 else 1)

    # --- Element komutlari ---

    elif cmd == "list-elements" and len(args) >= 2:
        _print_elements(list_elements(args[1]))

    elif cmd == "save-elements" and len(args) >= 2:
        out = args[2] if len(args) >= 3 else "elements.json"
        res = save_elements(args[1], out)
        if "error" in res:
            print(f"HATA: {res['error']}", file=sys.stderr)
            sys.exit(1)
        print(f"[OK] {res['count']} element -> {res['path']}")

    elif cmd == "element":
        if len(args) < 2:
            print('Kullanim: element "PencereAdi" ["ElementAdi"|list] '
                  '[click|move|dclick|rclick|coord|list] '
                  '[--by Name|AutomationId|ClassName|ControlType] [--timeout N]')
            sys.exit(1)

        window_title = args[1]

        if len(args) == 2:
            _print_elements(list_elements(window_title))
            sys.exit(0)

        token2 = args[2]
        if token2.lower() in _ACTION_KEYWORDS:
            action     = token2.lower()
            element_id = ""
        else:
            element_id = token2
            action = _parse_action(args, start=3)

        search_by = _parse_by(args)
        timeout   = _parse_timeout(args)

        if action == "list":
            _print_elements(list_elements(window_title))
            sys.exit(0)

        if action == "coord":
            if not element_id:
                print("HATA: coord icin element adi gerekli.", file=sys.stderr)
                sys.exit(1)
            result = find_element(window_title, element_id, search_by, timeout)
            if "error" in result:
                _print_find_error(result)
                sys.exit(1)
            print(f"{result['x']} {result['y']}")
            sys.exit(0)

        if not element_id:
            print("HATA: bu action icin element adi gerekli.", file=sys.stderr)
            sys.exit(1)

        result = find_element(window_title, element_id, search_by, timeout)
        if "error" in result:
            _print_find_error(result)
            sys.exit(1)

        x, y  = result["x"], result["y"]
        label = result.get("name", element_id)

        # UIPI riski: elevated bir pencereye tiklama sessizce yutulabilir
        if action in ("click", "dclick", "rclick") and not is_elevated():
            print("[uyari] Surec yonetici degil; hedef pencere yonetici olarak "
                  "calisiyorsa tiklama etkisiz kalabilir. Sorun yasarsan bu "
                  "betigi yonetici komut isteminden calistir.", file=sys.stderr)

        if action == "click":
            click(x, y)
        elif action == "dclick":
            dclick(x, y)
        elif action == "rclick":
            rclick(x, y)
        elif action == "move":
            move(x, y)

        print(f"[OK] {action} '{label}' at ({x},{y})")

    else:
        print(f"Bilinmeyen komut: {cmd}")
        print("Yardim icin: python hermesmouse.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
