# 🖱️ Hermes Mouse

**Zero-dependency Windows input automation.** (sıfır bağımlılıkla Windows otomasyonu)

Click buttons by **name**, send keyboard shortcuts, move the mouse, type text (Turkish/Unicode), take screenshots, and run automated workflows — all with **no pip install, no extra libraries**. Just Python + Windows.

---

## 🚀 One-Line Install / Tek Satır Kurulum

Open **PowerShell as Administrator** and run:

```powershell
iex "& { $(irm https://raw.githubusercontent.com/Watcher-Hermes/hermes-mouse/main/install.ps1) }"
```

That's it. Now type `hermes-mouse` in any terminal.

**Hermes Agent kullanıcıları için:** Kurulum otomatik olarak skill'i Hermes'e kaydeder.
Hermes'e "Not Defteri'nde Dosya'ya tıkla" dediğinizde ne yapacağını bilir.

---

## 📋 Commands / Komutlar

### Mouse
```
hermes-mouse pos                          # cursor position
hermes-mouse status                       # screen info + DPI + admin status
hermes-mouse move <x> <y>                 # smooth move
hermes-mouse move <x> <y> --fast          # instant move (SendInput)
hermes-mouse drag <x1> <y1> <x2> <y2>    # drag
hermes-mouse click <x> <y>               # left click
hermes-mouse rclick <x> <y>              # right click
hermes-mouse dclick <x> <y>              # double click
hermes-mouse scroll <delta>              # scroll (+/-)
hermes-mouse sweep [cx cy r]             # draw circle (demo)
```

### Keyboard / Klavye
```
hermes-mouse type <text>                 # Unicode text (Turkish supported)
hermes-mouse key <key>                   # send key or combo
```

Examples / Örnekler:
```
hermes-mouse key enter
hermes-mouse key esc
hermes-mouse key "ctrl+s"
hermes-mouse key "ctrl+shift+esc"
hermes-mouse key "alt+f4"
```

### Element (UI Automation)
Find and click UI elements by **name**, **AutomationId**, or **ClassName** — no coordinates needed.

```
hermes-mouse element "Notepad" list
hermes-mouse element "Notepad" "OK" click
hermes-mouse element "Notepad" "Cancel" move
hermes-mouse element "Chrome" "address-bar" click --by AutomationId
hermes-mouse element "Settings" "Button" coord --by ClassName
hermes-mouse list-elements "Calculator"
hermes-mouse save-elements "Explorer" elements.json
```

### Screenshot / Ekran Görüntüsü
```
hermes-mouse screenshot [file.bmp]       # GDI-based, zero deps
```

### Workflow / Otomatik Akış
Run a JSON or plain-text file with multiple steps:

```
hermes-mouse run workflow.json
hermes-mouse run workflow.txt
hermes-mouse run workflow.json --dry-run
hermes-mouse run workflow.json --log output.json
```

Example workflow (JSON):
```json
{
  "steps": [
    {"do": "click", "window": "Notepad", "target": "File"},
    {"do": "wait", "seconds": 0.3},
    {"do": "if_exists", "window": "Notepad", "target": "Exit",
     "then": {"do": "click"}},
    {"do": "screenshot", "path": "exit_dialog.bmp"},
    {"do": "key", "keys": "esc"},
    {"do": "type", "text": "hello world"},
    {"do": "assert", "window": "Notepad", "target": "Edit", "expect": "present"}
  ],
  "pause": 0.2
}
```

Example workflow (text):
```
# this is a comment
wait 0.5
key esc
click "Notepad" | "File"
wait 0.3
if_exists "Notepad" | "Exit" -> click
screenshot
assert "Notepad" | "Edit" | present
type "merhaba dünya"
```

### Flags
```
--verbose        debug logging (DPI, UIA calls, elevation)
--timeout N      retry N seconds if element not found
--dry-run        validate workflow without executing
--log path.json  save timestamped JSON log
```

---

## 🧠 How It Works / Nasıl Çalışır

| Feature | Technology |
|---------|-----------|
| Mouse movement | `SetCursorPos` (smooth) or `SendInput` (instant) |
| Mouse click | `SendInput` with `MOUSEINPUT` struct |
| Keyboard text | `KEYEVENTF_UNICODE` — supports Turkish, emoji |
| Keyboard shortcuts | Virtual key codes (VK) with modifier ordering |
| Element detection | PowerShell + .NET UIAutomationClient |
| Screenshot | GDI32 `BitBlt` + `GetDIBits` |
| Workflow engine | Pure Python step executor |
| Multi-monitor | `virtual_screen()` with `MOUSEEVENTF_VIRTUALDESK` |
| High-DPI | `SetProcessDpiAwarenessContext` (PerMonitorV2) |
| Elevation check | `shell32.IsUserAnAdmin()` with UIPI warning |

**Zero external dependencies.** Only `ctypes`, `json`, `subprocess`, `tempfile`, `os`, `logging` — all Python standard library.

---

## 📦 File Structure

```
hermes-mouse/
├── hermesmouse.py       # main script (~900 lines)
├── install.ps1          # one-line installer
├── README.md            # this file
└── LICENSE              # MIT
```

---

## 🔧 System Requirements

- **OS:** Windows 10 / Windows 11
- **Python:** 3.7+ (any — 3.11, 3.12, 3.13, 3.14)
- **PowerShell:** 5.1+ (for UI Automation element detection)
- **Admin:** Not required for normal use. Admin needed only if targeting elevated windows.

---

## ⚠️ Limitations

- Games / DirectX / OpenGL apps: element detection won't work (no UI Automation)
- Elevated apps: clicks may be silently dropped if this script is not admin (UIPI)
- Headless environments: no real desktop → mouse commands send API codes that return OK but may not reach visible UI

---

## 🧪 Test Status

**109+ tests passed** across 3 sessions on real Windows.  
1 bug found and fixed (`dwExtraInfo=None` → `TypeError` in `move --fast`).

---

## 📜 License

MIT — do whatever you want.

---

## 🤝 Contributing

PRs welcome. Keep it zero-dependency.

---

## Yapılanlar / Credits

Built by [Watcher-Hermes](https://github.com/Watcher-Hermes) for [Hermes Agent](https://hermes-agent.nousresearch.com).
