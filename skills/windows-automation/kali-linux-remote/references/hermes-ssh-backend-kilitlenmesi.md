# Hermes SSH Backend Kilitlenmesi — Recovery Rehberi

## Durum

Hermes `terminal.backend: ssh` olarak ayarlandığında ve config doğru olsa bile (ssh_host, ssh_user, ssh_password eksiksiz), **mevcut session'da terminal ve execute_code tool'ları tamamen bloke olur**. Config tekrar `local`'e çevrilse bile blokaj kalkmaz.

## Belirtiler

```
[ERROR] SSH environment requires ssh_host and ssh_user to be configured
```
Bu hata, config'de SSH bilgileri **eksiksiz olsa bile** gelir. Çünkü Hermes runtime'ı config'i session başında bir kere okur, dinamik reload yapmaz.

## Kök Neden

- Hermes tool runtime'ı (`terminal_tool.py`, execute_code) config'i session initialization'da okur
- `terminal.backend: ssh` ile başlatılan bir session'da `_create_environment()` SSH backend'e zorlanır
- Config'de `backend: local` olsa bile cached config `ssh` olarak kalır
- Terminal, execute_code, ve subprocess.run tümü **aynı Hermes Python process'ini** kullanır — biri bloke olursa hepsi bloke olur
- Gateway süreci (node.exe) de config'i kendi cache'inde tutar — taskkill/f/im ile öldürülmezse eski SSH config'ini yeni session'lara enjekte etmeye devam eder

## Tespit — Gateway Cache SSH Kirlenmesi (EN SIK YENİ DURUM)

**Belirti:** `config.yaml`'de `backend: local` yazılı, hiç `ssh_host`/`ssh_user` satırı yok, ama `execute_code` ve `terminal` hâlâ "SSH environment requires ssh_host and ssh_user" hatası veriyor.

**Kök neden:** Gateway süreci (node.exe) eski config'i cache'lemiş. Önceki bir session'da SSH backend kullanıldığında, gateway belleğinde SSH bağlantı bilgilerini tutar. Config dosyası değişse bile gateway runtime'ı yeniden okumaz.

**Çözüm adımları:**

1. Config'i önce doğrula (dosyada SSH satırı kalmadı mı?):
   ```
   grep -i ssh C:\Users\marko\AppData\Local\hermes\config.yaml
   ```
   Boş dönmeli. SSH satırları **tamamen silinmiş** olmalı — yorum satırına çevirmek yetmez, silinmeli.

2. **TÜM** Hermes süreçlerini öldür — sadece hermes.exe yetmez, gateway (node.exe) da öldürülmeli:
   ```powershell
   taskkill /f /im node.exe
   taskkill /f /im hermes.exe
   ```

3. Cache klasörünü temizle (varsa):
   ```powershell
   Remove-Item "$env:APPDATA\hermes\*" -Recurse -Force -ErrorAction SilentlyContinue
   ```

4. Hermes'i yeniden başlat.

5. Yeni session'ın temiz olduğunu doğrula — `execute_code` veya `terminal` çalışmalı.

**Önemli:** Sadece `taskkill /f /im hermes.exe` yapmak yetmez, çünkü gateway (node.exe) hâlâ ayakta kalır ve eski config cache'i ile yeni session'lar spawn eder. **İkisini de öldürmek şart.**

## Recovery Yöntemi

**Tek çözüm: Yeni bir session başlatmak.**

1. Config'i doğrula:
   ```
   backend: local
   ssh_host: 192.168.0.19 (veya doğru IP)
   ssh_user: kali
   ```

2. `/new` komutu ile yeni session başlat
   - VS Code'da: `Ctrl + Shift + P` → "Reload Window"
   - Telegram'da: `/new` yaz
   - CLI'da: yeni terminal penceresi

3. Yeni session'da `terminal` aracı **local** backend'de çalışır
   - Kali'ye SSH: `sshpass -p 'kali' ssh -o StrictHostKeyChecking=no kali@192.168.0.19 "komut"`
   - Veya config'de `backend: ssh` ile başka bir session daha aç (ama mevcut session'da kurtarma imkansız)

## Önleme

SSH backend'e geçmeden ÖNCE şu adımları izle:

1. **Önce SSH config'i yaz, backend'i en son değiştir:**
   ```
   hermes config set terminal.ssh_host <ip>
   hermes config set terminal.ssh_user kali
   hermes config set terminal.ssh_password "1234"
   hermes config set terminal.ssh_port 22
   hermes config set terminal.ssh_strict_host_key_check false
   ```

2. **Config'i doğrula:**
   ```
   hermes config get terminal.ssh_host  # → <ip> dönmeli
   hermes config get terminal.ssh_user  # → kali dönmeli
   ```

3. **En son backend'i değiştir ve hemen /new yap:**
   ```
   hermes config set terminal.backend ssh
   # → /new ile yeni session başlat
   ```

4. **Asla mevcut session'da SSH backend ile çalışmaya devam etme** — herhangi bir hata durumunda tool'ların tamamı kullanılamaz hale gelir.

## Test

Yeni session'da SSH backend çalışıyorsa:
```bash
whoami && pwd  # → kali ve /home/kali dönmeli
```

Eğer hala SSH hatası alınıyorsa: config'i tekrar kontrol et, `hermes config get terminal.backend` ile doğrula.
