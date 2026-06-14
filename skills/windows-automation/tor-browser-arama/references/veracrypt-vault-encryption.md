# VeraCrypt Vault Encryption — Session 2026-06-11

## Durum
Kurulum tamamlandı (VeraCrypt 1.26.7, `C:\Program Files\VeraCrypt\`).
Container dosyasi olusturuldu: `C:\Users\marko\Desktop\vault.hc` (500MB, bos dosya).
**Format bekliyor** — VeraCrypt Format.exe ile sifrelenip NTFS olarak bicimlendirilmesi gerekiyor.

## Yapilanlar
- [x] VeraCrypt kuruldu (C:\Program Files\VeraCrypt\)
- [x] vault.hc dosyasi olusturuldu (fsutil ile 500MB)
- [ ] Format + sifreleme (kullanici sifresini girecek)
- [ ] Container mount
- [ ] Obsidian vault tasima
- [ ] Startup auto-mount ayari

## Plan
1. `VeraCrypt Format.exe` ile container'i formatla (GUI, kullanici yapacak)
2. VeraCrypt ana penceresinden mount et (kullanici sifre girecek)
3. Obsidian vault'u (`C:\Users\marko\OneDrive\Belgeler\Obsidian Vault`) container icine kopyala
4. Obsidian'i yeni yola yonlendir
5. Original vault'u sil (veya yedek olarak tut)
6. Startup'ta kullanici sifresini girerek manuel mount (otomatik degil)

## CLI Yaklasimi (Alternatif)
VeraCrypt Format.exe GUI gerektirir (UAC yukseltmesiyle calisir, screenshot alinamaz).
Deneysel CLI:
```
"C:\Program Files\VeraCrypt\VeraCrypt.exe" /create C:\Users\marko\Desktop\vault.hc /password <sifre> /size 500M /encryption AES /hash SHA-512 /filesystem NTFS
```
Not: Bu komut da UAC gerektirir, dogrulama yapilmadi.

## Pifallar
- **VeraCrypt Format UAC ile yukselir** — screenshot/goruntu yakalanamaz, otomasyon zor
- **Bos dosya vs formatli container** — fsutil ile bos dosya olusturulur, VeraCrypt Format ile sifrelenip NTFS yapisi eklenmeli
- **OneDrive senkronizasyonu** — container tasininca OneDrive vault icindeki bireysel dosyalari degil, container'in tamamini senkronize eder (sifreli oldugu icin anlamsiz). Guvenlik icin iyi ama yedekleme kaybolur.

## Notlar
- Windows 11 Home → BitLocker yok, VeraCrypt dogru secim
- Vault boyutu: 217MB → 500MB container yeterli
- Kullanici sifreyi kendisi belirleyecek (startup'ta manuel giris)
