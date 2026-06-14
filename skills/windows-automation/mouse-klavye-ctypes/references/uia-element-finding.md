# UI Automation Element Finding — Teknik Referans

## PowerShell UIA Script Mimarisi (v2.1)

hermesmouse.py v2.1+ parametreleri **temp JSON dosyası** ile geçer.
Injection riski sıfır, Unicode sorunsuz.

```
Python                         PowerShell
  │                               │
  ├── json.dump(params.json) ───→ │
  ├── subprocess.run(powershell)─→│ Get-Content params.json | ConvertFrom-Json
  │                               │ Find window → Find element
  │                               │ Write-Output (ConvertTo-Json -Compress)
  │←── stdout (JSON) ─────────────│
  └── json.loads(stdout)          │
```

## Encoding Fix (Türkçe Windows) — KRITIK

**Sorun:** PowerShell stdout'u sistemin aktif kod sayfasına göre yazar.
Türkçe Windows'ta bu `cp1254` (Windows-1254 Turkish ANSI) veya
`cp857` (Turkish OEM) olabilir. `subprocess.run(text=True)` UTF-8 varsayar
→ `UnicodeDecodeError`.

Ayrıca cp1254, ISO-8859-9'dan farklıdır — cp1254 0x80-0x9F aralığında
ek karakterler tanımlar (€, ‚, ƒ, …, †, ‡, ˆ, ‰, Š, ‹, Œ, Ž, vb.).
Standart Windows cp1254 codec'i bu karakterleri `cp1254` codec'inde
tanımlı olmayabilir → decode ederken hata.

**Çözüm (PowerShell tarafı):** Çıktı kodlamasını UTF-8'e zorla:

```powershell
$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
```

Bu satır **PowerShell script'inin ilk çalışan satırı** olmalı
(Add-Type çağrısından önce).

**Çözüm (Python tarafı — yedek):** Binary mode + encoding fallback:

```python
result = subprocess.run(..., capture_output=True, text=False)
raw_bytes = result.stdout or b""

# UTF-8-sig once (BOM'u otomatik kaldirir)
for enc in ("utf-8-sig", "utf-8", "cp1254", "cp1252"):
    try:
        raw = raw_bytes.decode(enc).strip()
        if raw:
            break
    except (UnicodeDecodeError, LookupError):
        continue

if not raw:
    # Fallback: stderr + stdout birlestir, replace ile decode et
    err = (result.stderr or b"") + (result.stdout or b"")
    raw = err.decode("utf-8", errors="replace").strip()
```

**Neden utf-8-sig önce?** PowerShell Windows'ta bazen UTF-8 BOM
(`\xef\xbb\xbf`) ekler. utf-8-sig codec'i BOM'u otomatik kaldırır.
`cp1254` (Turkish ANSI) ikinci sırada — PowerShell `$OutputEncoding`
UTF-8'e ayarlıysa gereksiz olur ama Türkçe karakter içeren
eski sistemlerde yedek görevi görür.

## ControlType Çözümü

`--by ControlType` için Reflection kullanılır:

```powershell
$ctField = [System.Windows.Automation.ControlType].GetField(
    $elementId, [System.Reflection.BindingFlags]'Public,Static')
$ctValue = $ctField.GetValue($null)
$elemCond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
    $ctValue)
```

Bu yöntem, PropertyConditionFlags kullanmadan doğrudan ControlType
enum'ından PropertyCondition oluşturur. Eski `$propMap["ControlType"]`
yaklaşımı yanlıştı çünkü ControlTypeProperty farklı constructor
imzası gerektirir.

## Pencere Bulma Optimizasyonu

Eski: `$desktop.FindAll(Children, TrueCondition)` — tüm UI öğelerini tara
(yavaş, gereksiz).

Yeni: `ControlType=Window` filtresi ile sadece pencereleri bul:

```powershell
$typeProp = New-Object PropertyCondition(ControlTypeProperty,
    [ControlType]::Window)
$windows = $desktop.FindAll(Children, $typeProp)
```

Pencere bulunduktan sonra element arama sadece o pencerenin alt ağacında
yapılır (`TreeScope::Descendants`).

## Parametre Geçiş Yöntemi: JSON Dosyası

**Neden env variable değil?** Eski (v2.0) yaklaşım:
```powershell
# KÖTÜ: string interpolation ile JSON — kaçış hataları, injection riski
$json = "{`"x`":$cx,`"y`":$cy}"
```

Yeni (v2.1+) yaklaşım — Python tarafı:
```python
# İYİ: Python json.dump ile yaz, PowerShell oku
params = {"windowTitle": title, "elementId": id, ...}
with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                  delete=False, encoding="utf-8") as f:
    json.dump(params, f, ensure_ascii=False)
    tmp_param = f.name
```

PowerShell tarafı:
```powershell
param([string]$ParamFile)
$params = Get-Content $ParamFile -Raw | ConvertFrom-Json
$windowTitle = $params.windowTitle
```

**Avantajlar:**
- String interpolation yok → injection riski sıfır
- Unicode karakterler sorunsuz (ensure_ascii=False)
- Hata ayıklaması kolay (param.json dosyasını okuyabilirsin)
- Temp dosyalar `finally` bloğunda silinir

## Argüman Ayrıştırma (CLI)

`element` komutunun argüman sıralaması:

```bash
# ŞABLON:
hermesmouse element <pencere> [<element>] [action] [--by <type>]

# ÖRNEKLER:
hermesmouse element "Komut" list           # listele (action 2. arg)
hermesmouse element "Chrome" "Adres" click # tıkla (varsayılan)
hermesmouse element "VS Code" "Dosya" move --by AutomationId
hermesmouse element "Hesap" "7" coord      # koordinat al
```

**Kritik kural:** `element` komutu 3'e ayrılır:
1. Sadece pencere adı → list modu
2. Pencere + action keyword'u (list, click move, coord) → o action
3. Pencere + element + action (opsiyonel) → elementi bul + action

**`--by` flag'inin action algilamasini yemesini engelleme:**
`args[3]` direkt kontrol edilmez cunku `--by` flag'i orada olabilir.
Bunun yerine tum argumanlar taranir, `--` ile baslayanlar atlanir:

```
args: element "Komut" "NewTabButton" --by AutomationId coord
  0       1         2              3    4             5
```

Python'da implementasyon: args[3]'ten basla, `--` on ekini atla, ilk action keyword'u bul.

## Yaygın Kontrol Tipleri

| ControlType | Kullanım | Örnek |
|---|---|---|
| `Button` | Butonlar | OK, Cancel, Gönder |
| `Edit` | Metin kutuları | Arama çubuğu, form alanı |
| `Text` | Statik metin | Etiketler, başlıklar |
| `ComboBox` | Açılır menü | Dropdown seçim |
| `CheckBox` | Onay kutuları | Beni hatırla |
| `ListItem` | Liste öğeleri | Dosya listesi |
| `TabItem` | Sekmeler | Tarayıcı sekmeleri |
| `MenuItem` | Menü öğeleri | Dosya > Kaydet |
| `Pane` | Panel/bölme | VS Code bölmeleri |
| `Window` | Pencere | Uygulama pencereleri |
