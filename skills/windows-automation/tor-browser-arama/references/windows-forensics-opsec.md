# Windows Forensics — Bilgisayara El Konulursa

## Silinemez Kayitlar (Forensic Kesin Bulur)

| Iz | Konum | Ne gosterir? |
|----|-------|-------------|
| Windows Event Log | `C:\Windows\System32\winevt\Logs\` | Bilgisayar acilis/saatleri, program calistirmalari, servis durumlari |
| USB takilis gecmisi | Registry `HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR` | Hangi USB takildi, seri numarasi, ilk/son takilma zamani |
| Ag baglanti gecmisi | Registry `NLA` + `SRUM` | Hangi WiFi aglarina baglanildi, saat |
| Dosya sistemi ($MFT) | NTFS master file table | Silinen dosyalarin adlari, boyutlari, silinme zamanlari |
| OneDrive senkronizasyon | OneDrive logs + cloud | Obsidian vault'taki dosyalarin gecmis versiyonlari |
| VirtualBox kayitlari | Registry + XML | Kali VM kurulumu, MAC adresi, ag ayarlari |

## Az Bilinen Ama Kritik Izler

| Iz | Ne kaydeder? |
|----|-------------|
| $USN Journal | Her dosya isleminin kaydi (silinen .md adlari bile durur) |
| Windows Timeline | "Bugun saat 14:00'te Tor Browser acikti" |
| AmCache / ShimCache | Calistirilan her .exe'nin adi ve ilk calistirma zamani |
| DNS Cache | `ipconfig /displaydns` — ziyaret edilen domain'ler |
| Volume Shadow Copy | Windows'un eski dosya surumleri (silinen dosyalar) |
| Search Index | Windows Search'te indexlenen dosya icerikleri |
| Prefetch | Calistirilan .exe'lerin izleri |
| Recycle Bin | $I ve $R dosyalari — silinen dosyalar |

## Korumali Olan / Olmayan

**Korumali (Bu oturumda kurulan):**
- Tor Browser profili (gecmis, cookie, onbellek, oturum) → startup'ta temizlenir
- Prefetch (firefox.exe) → startup'ta temizlenir
- Recent Items / Jump Lists → startup'ta temizlenir
- Pagefile (RAM takasi) → kapanista sifirlanir (ClearPageFileAtShutdown=1)

**Acik (korunmamis):**
- Obsidian vault → duz metin, sifresiz
- Windows Event Log → silinemez
- $MFT / USN Journal → silinemez
- Kali VDI dosyasi → sifresiz
- OneDrive bulut yedegi → vault gecmisi bulutta

## Onlem Sirasi

1. Obsidian vault sifreleme (VeraCrypt — devam ediyor, 2026-06-11 session)\n2. Windows Timeline kapatma (GPO ile)
3. OneDrive baglantisini kesme
4. Kali VM sifreleme (LUKS)
5. Shadow Copies periyodik temizlik (vssadmin)
6. USN Journal kucultme (fsutil usn)
