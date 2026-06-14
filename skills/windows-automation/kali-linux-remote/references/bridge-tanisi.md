# Bridged Ağ Tanısı — Kali VM

Kali'nin WiFi ağından (bridged) IP alıp almadığını kontrol etme.

## Adımlar

```
1. Host WiFi subnet'ini bul
   ipconfig | grep -A 20 "Wi-Fi" | grep "IPv4"
   → 192.168.0.20/24

2. Kali bridged NIC MAC'ini bul
   VBoxManage showvminfo "kal" --machinereadable | grep macaddress
   → macaddress1="080027E20251"  (bridged)

3. WiFi subnet'ini tara, Kali MAC'ini ara
   nmap -sn 192.168.0.0/24
   → Çıktıda 08:00:27 ile başlayan MAC ara

4. Eşleşme yoksa → Kali bridged'dan IP almamış
   - VM ayarlarında bridged NIC doğru WiFi kartına bağlı mı kontrol et
   - VM'i yeniden başlat (dhclient eth0)
   - VirtualBox bridged driver'ı yeniden yükle
```

## Ya SSH da timeout veriyorsa?

VM çalışıyor ama SSH yanıt vermiyor → Kali'de sshd çalışmıyor olabilir.
Çözüm: VirtualBox GUI'den VM'e bağlan, `systemctl status ssh` kontrol et.
