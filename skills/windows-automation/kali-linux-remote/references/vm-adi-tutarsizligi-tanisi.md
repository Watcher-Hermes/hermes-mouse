# VM Adı Tutarsızlığı Tanısı

## Sorun
Hermes `VBoxManage` ile Kali VM'e komut gönderirken "Could not find a registered machine named 'X'" hatası alır.

## Kök Neden
VM adı `"kal"` (3 harf) — `VBoxManage list vms` ile doğrulanır. Ama bazı script/referans dosyalarında `"kali"` (4 harf) yazılıdır.

## Tanı Adımları

### 1. VM adını doğrula
```bash
\"/c/Program Files/Oracle/VirtualBox/VBoxManage.exe\" list vms
```
Çıktı: `"kal" {809fe6be-771a-4f69-8522-34a29c7d078f}`

### 2. Yanlış VM adını kullanan dosyaları bul
```bash
grep -rn '\"kali\"' /c/Users/marko/AppData/Local/hermes/scripts/ --include='*.py'
grep -rn '\"kali\"' /c/Users/marko/AppData/Local/hermes/skills/ --include='*.md'
grep -rn '\"kali\"' /c/Users/marko/AppData/Local/hermes/skills/ --include='*.py'
```

### 3. Düzeltme
```bash
# Python script'leri
# VM_NAME = "kali" -> VM_NAME = "kal"
# veya: VM_NAME = "kal"  # NOT: "kali" değil!

# Markdown referansları
# VBoxManage komutlarında "kali" -> "\"kal"\"
```

## Etkilenen Dosyalar (Son Güncelleme: 2026-06-07)

| Dosya | Düzeltildi mi? | Not |
|-------|---------------|------|
| `scripts/kali_rdp.py` | EVET | `KALI_VM = "kali"` → `"kal"` |
| `scripts/kali_unlock_vrde.py` | EVET | `VM = "kali"` → `"kal"` |
| `skills/.../references/kali-access.md` | EVET | 4 VBoxManage komutu düzeltildi |

## Önleme
- Yeni Kali script'i yazarken VM adını `VBoxManage list vms` ile doğrula
- VM adını bir sabite al (örn. `KALI_VM = "kal"`), tüm script'ler bu sabiti kullansın
- Türkçe karakter sorunu VM adıyla ilgili değil — VM adı pure ASCII `"kal"`
