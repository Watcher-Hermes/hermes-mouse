# Son 24 Saat Güvenlik Taraması (Windows)

Temiz kurulum / jailbreak / "siber suç unsuru kalmasın" öncesi sistem denetimi.

## Kontrol Maddeleri

### 1. Registry — Yeni yüklenen yazılımlar
```
Get-WmiObject Win32_Product | Where-Object { $_.InstallDate -ge (Get-Date).AddHours(-24).ToString('yyyyMMdd') } | Select Name, Vendor, Version, InstallDate
```
Ayrıca:
```
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Where-Object { $_.InstallDate -ge (Get-Date).AddHours(-24).ToString('yyyyMMdd') -and $_.DisplayName } | Select DisplayName, Publisher, InstallDate
```
Her iki kaynağı da (HKLM + HKCU + WOW6432Node) tara.

### 2. Windows Olay Günlüğü — Installer olayları
```
Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='MsiInstaller'; StartTime=(Get-Date).AddHours(-24)} | Select TimeCreated, Id, Message | Format-Table -AutoSize
```

### 3. Dosya sistemi — Son 24 saatte değişen çalıştırılabilir dosyalar
- `C:\Users\<user>\Desktop\*.exe, *.ps1, *.py, *.bat`
- `C:\*.exe, *.ps1, *.py, *.bat, *.dll`
- `%TEMP%` ve `C:\Windows\Temp` içinde yeni `.exe, .ps1`
- WinGet Packages: `C:\Users\<user>\AppData\Local\Microsoft\WinGet\Packages\`

### 4. Scheduled Tasks
```
Get-ScheduledTask | Where-Object { $_.State -eq 'Ready' -or $_.State -eq 'Running' }
```
Şüpheli: bilinmeyen publisher, açıklamasız task.

### 5. Startup
```
Get-CimInstance Win32_StartupCommand
```
Beklenmedik `.vbs`, `.ps1`, `.exe` girişleri.

### 6. Aktif ağ bağlantıları
```
Get-NetTCPConnection | Where-Object State -eq Established | Select LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess
```
Şüpheli: yabancı IP'ler, bilinmeyen portlar, P2P/anonim bağlantılar.

### 7. Servisler
```
Get-Service | Where-Object { $_.Status -eq 'Running' -and $_.Name -notlike '*Microsoft*' -and $_.Name -notlike '*Windows*' -and $_.Name -notlike '*Driver*' -and $_.Name -notlike '*Edge*' }
```
Bilinmeyen/dışarıdan kurulmuş servis.

### 8. Bilinen güvenlik riski yazılımlar
- `sshpass` / `sshpass-win32` → SSH şifreli bağlantı için, yetkisiz erişim aracı
- Process Hacker, Cheat Engine, x64dbg, Wireshark (izinli olabilir ama raporlanmalı)
- Herhangi bir pentest aracı (nmap, metasploit, burp suite vb. — izin alınmamışsa risk)

### 9. Web geçmişi kontrolü (isteğe bağlı)
```
Get-ChildItem "C:\Users\<user>\AppData\Local\Google\Chrome\User Data\Default\History" -ErrorAction SilentlyContinue
```
Sadece son 24 saatte ziyaret edilen domain listesi çıkar.

## Çıktı Formatı

Her madde için:
```
[OK] / [SAPTANDI] / [TEMIZLENDI] — kısa açıklama
```

Son satır:
```
DURUM: TEMIZ / RISK VAR / TEMIZLENDI
```
