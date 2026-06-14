# ~/.bashrc Yapılandırması — SSH + Git Credential Bypass

## Tam ~/.bashrc İçeriği

```bash
# Hermes SSH/GIT askpass disable
export GIT_ASKPASS=echo
export SSH_ASKPASS=echo
export DISPLAY=
export GIT_TERMINAL_PROMPT=0

# Git credential manager'ı tamamen devre dışı
alias git='GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=echo git'

# SSH varsayılan olarak sshpass kullansın
alias ssh='sshpass -p 1234 /c/Windows/System32/OpenSSH/ssh.exe'
alias scp='sshpass -p 1234 /c/Windows/System32/OpenSSH/scp.exe'
```

## Ne İşe Yarar

| Değişken/Alias | Açıklama |
|----------------|----------|
| `GIT_ASKPASS=echo` | Git şifre sorma programını echo ile değiştirir → sessizce başarısız olur |
| `SSH_ASKPASS=echo` | SSH şifre GUI'sini devre dışı bırakır |
| `DISPLAY=` | GUI programlarının ekranı yok → hiçbir dialog açılmaz |
| `GIT_TERMINAL_PROMPT=0` | Git terminalde şifre sormaz |
| `alias git='...'` | Her git komutunda GIT_TERMINAL_PROMPT=0 ve GIT_ASKPASS=echo otomatik |
| `alias ssh='sshpass ...'` | Tüm SSH komutları otomatik sshpass + 1234 ile gider |
| `alias scp='sshpass ...'` | Tüm SCP komutları da aynı şekilde |

## Neden Windows OpenSSH?

Windows'ta iki farklı SSH binary'si var:
- **git-bash SSH** (`/usr/bin/ssh`, OpenSSH_10.3) — sshpass ile çalışmaz
- **Windows OpenSSH** (`/c/Windows/System32/OpenSSH/ssh.exe`, OpenSSH_9.5p2) — sshpass ile çalışır

sshpass sadece Windows OpenSSH ile uyumlu. Alias'ta doğrudan Windows OpenSSH yolu belirtilir.

## sshpass Yolu

Tam sshpass binary yolu:
```
C:\Users\marko\AppData\Local\Microsoft\WinGet\Packages\xhcoding.sshpass-win32_Microsoft.Winget.Source_8wekyb3d8bbwe\sshpass.exe
```

## Oluşturma

```bash
cat > ~/.bashrc << 'BASHRC_EOF'
# content here
BASHRC_EOF
```

## Doğrulama

```bash
source ~/.bashrc
echo "GIT_ASKPASS=$GIT_ASKPASS GIT_TERMINAL_PROMPT=$GIT_TERMINAL_PROMPT"
# → GIT_ASKPASS=echo GIT_TERMINAL_PROMPT=0

ssh kali "echo SSH_OK"
# → SSH_OK (otomatik sshpass ile)
```
