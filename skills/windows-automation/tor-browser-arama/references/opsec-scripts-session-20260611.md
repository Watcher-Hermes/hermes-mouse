# OpSec Scripts — Session 2026-06-11

## Oluşturulan Dosyalar

### 1. Tor İz Temizleme
| Dosya | Yol | Ne işe yarar? |
|-------|-----|---------------|
| Python script (ana kopya) | `C:\Users\marko\hermes_iz_temizle.py` | Tor Browser profili, cache, prefetch, recent items temizler |
| Python script (skill) | `C:\Users\marko\AppData\Local\hermes\skills\windows-automation\tor-browser-arama\scripts\iz_temizle.py` | Skill içindeki ana kopya (senkronize) |
| `.bat` wrapper | `C:\Users\marko\hermes_tor_cleanup.bat` | Script'i sessiz çalıştırır + Tor kontrolü yapar |
| Startup link | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Hermes_Tor_Temizleme.lnk` | Her Windows açılışında otomatik tetikler |

### 2. Pagefile Temizlik
| Dosya | Yol | Ne işe yarar? |
|-------|-----|---------------|
| `.bat` admin script | `C:\Users\marko\hermes_pagefile_on.bat` | Registry'den ClearPageFileAtShutdown=1 set eder (admin gerekir) |

**Durum:** ✅ Aktif (ClearPageFileAtShutdown = 1)

### 3. Pre-Flight Check
| Dosya | Yol | Ne işe yarar? |
|-------|-----|---------------|
| `.bat` script | `C:\Users\marko\hermes_preflight.bat` | Tor + IP + DNS + Kali kontrolu (4 test) |
| Masaüstü kısayolu | `C:\Users\marko\Desktop\Pre-Flight Check.lnk` | Script'e tek tık erişim |

## Nasıl Çalışır?

### Startup Akışı
1. Windows açılır
2. Startup klasöründeki `Hermes_Tor_Temizleme.lnk` tetiklenir
3. `hermes_tor_cleanup.bat` çalışır
4. `iz_temizle.py` tüm Tor izlerini temizler
5. Tor proxy kontrolü yapılır (`check.torproject.org` üzerinden)
   - **Tor açıksa:** `C:\Users\marko\tor_kapali.flag` varsa silinir
   - **Tor kapalıysa:** `C:\Users\marko\tor_kapali.flag` oluşturulur
6. Kullanıcı hiçbir şey fark etmez

### Tor Kapalı Uyarı Sistemi
- `tor_kapali.flag` dosyası sadece startup'ta oluşur/silinir
- Hermes kullanıcı mesaj attığında flag'i kontrol eder
- Flag varsa → "Bu arada Tor kapalı, haberin olsun." uyarısı
- Flag yoksa → normal devam
- Kullanıcı Tor'u açar, bir sonraki startup'ta flag otomatik silinir

### Pre-Flight Akışı
1. Kullanıcı siber işlem öncesi masaüstündeki kısayola tıklar
2. 4 test sırayla çalışır
3. Yeşil ✅ = güvende, kırmızı 🔴 = Tor kapalı
4. Python 3.14 (PySocks var) kullanır

## Kaldırma
- Startup: `Hermes_Tor_Temizleme.lnk` sil
- Script'ler: `hermes_iz_temizle.py`, `hermes_tor_cleanup.bat`, `hermes_preflight.bat`, `hermes_pagefile_on.bat` sil
- Flag: `C:\Users\marko\tor_kapali.flag` varsa manuel sil
