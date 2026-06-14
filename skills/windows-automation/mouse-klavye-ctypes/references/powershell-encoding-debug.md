# PowerShell Encoding Debug (14 Haziran 2026)

## Problem

`element` komutu PowerShell UIAutomation çıktısını parse edemiyordu:
`HATA: No output from PowerShell: [{"name":"Komut stemi",...}]`

JSON verisi geliyor ama decode edilemiyordu.

## Root Cause

PowerShell `Add-Type` assembly yüklemesi, stdout'u sistemin aktif kod sayfasıyla (Turkish: ISO-8859-9/OEM 857) üretiyordu. Python tarafında `text=True` ile UTF-8 decode deneyince Türkçe karakterler (`İ`, `ş`, `ç`, `ğ`, `ü`, `ö`) patlıyordu.

## Hex Kanıtı

```
Bytes 460-480: 65 22 3a 22 4b 6f 6d 75 74 20 98 73 74 65 6d 69
               e  "  :  "  K  o  m  u  t 20 98  s  t  e  m  i
```

0x98 = ISO-8859-9'da tanımsız (C1 kontrol karakteri). UTF-8'de geçersiz.

## Çözüm (2 yönlü)

### 1. PowerShell tarafı (PS script başına)
```powershell
$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
```

### 2. Python tarafı (decode sırası)
```python
for enc in ("utf-8-sig", "utf-8", "cp1254", "cp1252"):
    try:
        return raw_bytes.decode(enc).strip()
    except:
        continue
```

`utf-8-sig` önce denenir (BOM'u otomatik atar). `cp1254` (Turkish ANSI) son çare.

## Ayrıca: text=False

`subprocess.run(text=True)` UTF-8 varsayar. `text=False` ile ham bytes alınır, manuel decode edilir.

```python
# Hatalı:
result = subprocess.run(..., capture_output=True, text=True)

# Doğru:
result = subprocess.run(..., capture_output=True, text=False)
raw = _decode_ps_bytes(result.stdout or b"")
```
