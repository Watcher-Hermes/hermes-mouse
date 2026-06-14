# S22 PLAS Canlı Konum Takibi — Yöntem ve Bulgular

Bu doküman, Samsung Galaxy S22 PLAS (S22 Plus) cihazının WiFi hotspot'u üzerinden
canlı takip edilmesi için test edilmiş yöntemleri ve bulguları içerir.

## Cihaz Bilgileri

| Özellik | Değer |
|---------|-------|
| Model | Samsung Galaxy S22 Plus (S22 PLAS) |
| Hotspot SSID (en son) | S22 PLAS |
| Root | DEĞİL (root'suz) |
| OS | Android (muhtemelen One UI) |
| WiFi Band | 2.4 GHz (hotspot standard) |
| MAC Davranışı | Rastgele MAC (her taramada değişebilir) |

## Anahtar Bulgu: Rastgele MAC

S22 PLAS hotspot'u **her bağlantı/oturumda farklı bir MAC adresi** kullanır.
Bu oturumda 4 farklı BSSID tespit edildi:

- `26:5a:10:b6:25:c8`
- `46:89:9e:yy:xx:vv` (maskelenmiş)
- `7e:3a:6e:aa:bb:cc`
- `5e:2f:8a:dd:ee:ff`

**Çıkarım:** Samsung One UI'daki "Rastgele MAC" özelliği aktif. Her hotspot
açılışında veya ~5-10 dk'da bir yeni MAC atanıyor olabilir.

**Takip stratejisi:** BSSID yerine **SSID'den** takip et:
```bash
sudo iw dev wlan0 scan 2>&1 | grep -A10 'SSID: S22 PLAS\|SSID: S 22 PLAS'
```

## Test Edilen Yöntemler

### Yöntem 1: `iw dev wlan0 scan` (managed mod) — ÖNCELİKLİ ✓

En hızlı yöntem. managed modda tüm kanalları tarar, kompakt çıktı verir.

**Adımlar:**
```bash
# 1. managed moda geç
sudo iw dev wlan0 set type managed
sudo ip link set wlan0 up
sleep 1

# 2. S22 PLAS'ı bul
sudo iw dev wlan0 scan 2>&1 | grep -A10 'SSID: S22 PLAS\|SSID: S 22 PLAS'
# Çıktı: BSSID, signal: -XX dBm, freq: 24XX, SSID: S 22 PLAS
```

**Sinyal kodları:**
- `-20 dBm` — çok yakın (~1 metre)
- `-27 dBm` — yanında
- `-48 dBm` — ~5 metre
- `-52 dBm` — ~10 metre (duvar arkası)

### Yöntem 2: airodump-ng ile canlı takip (monitor mod) ✓

Sürekli sinyal takibi için — CSV çıktı + timeout kullanılır.

**Adımlar:**
```bash
# 1. Monitor moda geç
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up

# 2. Canlı takip (60 sn timeout, 5 sn write-interval)
sudo timeout 60 airodump-ng wlan0 --bssid <BULUNAN_MAC> --channel <CH> \
  -w /tmp/s22_takip --output-format csv --write-interval 5 2>/dev/null

# 3. PWR değişimini oku
cat /tmp/s22_takip-01.csv | grep '<BULUNAN_MAC>' | awk -F',' '{print $1, $4, $9}'

# 4. Temizle
sudo pkill airodump-ng
sudo iw dev wlan0 set type managed
sudo ip link set wlan0 up
```

### Yöntem 3: `iwlist wlan0 scanning` (eski API) — YEDEK ✓

`iw` çalışmazsa denenebilir. Aynı sonucu verir, biraz daha yavaş.

## Notlar

- **Managed modda iw scan:** wlan0 managed moddayken `iw dev wlan0 scan` tüm
  kanalları tarar (passive scanning). Sonuç 2-5 sn içinde gelir.
- **Monitor modda iw scan:** `Operation not supported (-95)` hatası verir.
  monitor modda sadece airodump-ng kullanılabilir.
- **Her taramada önce managed moda geç** — eğer son kullanım monitor moddaydıysa
  wlan0 monitor modda kalmış olabilir. managed'a geçmeden scan çalışmaz.
- **USB WiFi adaptör (Ralink RT2501/RT2573):** Sadece 2.4 GHz (802.11 b/g).
  Kanal 1-13 arası tarar. Sinyal doğruluğu ±3 dBm.
- **PWR stabilitesi:** Ardışık taramalarda sinyal değişimi:
  - Tarama 1: -52 dBm
  - Tarama 2: -50 dBm
  - Tarama 3: -51 dBm
  (±2 dBm aralık, normal. Cihaz hareket etmiyorsa stabil.)

## Test Sonuçları (Oturum 2026-06-07)

| Test | Süre | Sonuç |
|------|------|-------|
| iw scan → tespit | ~2 sn | S22 PLAS bulundu (4 kez) |
| airodump managed mod | Hata | -95 (monitor gerekir) |
| airodump monitor + CSV | ~60 sn | S22 PLAS PWR -50 dBm |
| MAC değişikliği tespiti | ~15 dk | 4 farklı BSSID |
| managed↔monitor geçişi | ~2 sn | Sorunsuz |
| help-first metodolojisi | Tüm adımlar | iw --help → çözüm bulundu |
