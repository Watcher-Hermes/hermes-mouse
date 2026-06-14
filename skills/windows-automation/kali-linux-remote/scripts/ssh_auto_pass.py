"""
SSH_ASKPASS otomatik şifre doldurma scripti.

GIT_ASKPASS=echo ve SSH_ASKPASS=echo ortam değişkenleriyle SSH şifre
sorulması bastırılır. Eğer GUI şifre penceresi açılırsa (pygetwindow ile
algılanır), pyautogui ile "1234" yazıp Enter gönderir.

Kullanım:
  python ssh_auto_pass.py &
  (arka planda çalışır, her 2 sn'de bir kontrol eder)

Bağımlılıklar:
  pip install pygetwindow pyautogui
"""

import time
import sys

try:
    import pygetwindow as gw
    import pyautogui
except ImportError:
    print("HATA: pygetwindow veya pyautogui kurulu değil.")
    print("pip install pygetwindow pyautogui")
    sys.exit(1)

PENCERE_ADLARI = [
    "SSH",
    "ssh",
    "Enter password",
    "OpenSSH",
    "Kimlik Doğrulama",
    "Authentication",
    "şifre",
    "password",
]

def find_ssh_password_window():
    """Açık SSH şifre pencerelerini bul."""
    try:
        windows = gw.getWindowsWithTitle("")
        for win in windows:
            for kw in PENCERE_ADLARI:
                if kw.lower() in win.title.lower() and win.visible:
                    return win
    except Exception:
        pass
    return None

def fill_password(window, password="1234"):
    """Şifre penceresine odağı ver, şifreyi yaz ve Enter'a bas."""
    try:
        window.activate()
        time.sleep(0.3)
        pyautogui.write(password, interval=0.05)
        pyautogui.press("enter")
        return True
    except Exception as e:
        print(f"Şifre doldurma hatası: {e}")
        return False

def main():
    print("SSH şifre otomatik doldurucu başladı (her 2 sn'de bir kontrol)...")
    print("Çıkmak için Ctrl+C")

    while True:
        try:
            win = find_ssh_password_window()
            if win:
                print(f"Şifre penceresi bulundu: {win.title}")
                fill_password(win)
                time.sleep(1)  # Tekrar tetiklenmeyi önle
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nDurduruldu.")
            break
        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
