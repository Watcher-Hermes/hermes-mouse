#!/usr/bin/env python3
"""
Hermes Iz Temizleme (Tor Trace Cleanup)
- Tor Browser cache, history, session, cookies
- Windows Prefetch (firefox.exe)
- Windows Recent Items (jump lists)

Kullanim: python hermes_iz_temizle.py
En iyi sonuc: Tor Browser KAPALIYKEN calistir.
"""
import os, shutil, glob, time
from pathlib import Path

# ── YOLLAR ──────────────────────────────────────────────
TOR_PROFILE  = r"C:\Users\marko\OneDrive\Desktop\Tor Browser\Browser\TorBrowser\Data\Browser\profile.default"
TOR_CACHES   = r"C:\Users\marko\OneDrive\Desktop\Tor Browser\Browser\TorBrowser\Data\Browser\Caches\profile.default"
PREFETCH_DIR = r"C:\Windows\Prefetch"
RECENT_DIR   = r"C:\Users\marko\AppData\Roaming\Microsoft\Windows\Recent"

def log(msg):
    print(f"  [{msg}]")

def clean_tor_profile():
    """Tor Browser gecmis, cerez, onbellek, oturum dosyalarini temizle"""
    profile = Path(TOR_PROFILE)
    if not profile.exists():
        log(f"ATLA: Profil bulunamadi -> {TOR_PROFILE}")
        return

    targets = [
        ("cache2",        "Onbellek"),
        ("startupCache",  "Baslangic onbellek"),
        ("sessionstore-backups",  "Oturum geri yukleme"),
        ("safebrowsing", "Guvenli gezinti"),
        ("datareporting","Veri raporlama"),
        ("OfflineCache", "Cevrimdisi onbellek"),
        ("thumbnails",   "Kucuk resimler"),
        ("security_state","Guvenlik durumu"),
    ]

    for folder, label in targets:
        p = profile / folder
        if p.exists():
            try:
                shutil.rmtree(p)
                log(f"SILINDI: {label}")
            except PermissionError:
                log(f"ATLA: {label} (kilitli, Tor kapali degil)")

    # SQLite dosyalari (gecmis, cookie, form verisi, site ayarlari)
    sqlite_files = [
        "places.sqlite", "places.sqlite-wal", "places.sqlite-shm",
        "cookies.sqlite", "cookies.sqlite-wal",
        "signons.sqlite",  # kayitli sifreler
        "formhistory.sqlite",
        "permissions.sqlite",
        "content-prefs.sqlite",
        "webappsstore.sqlite",
        "favicons.sqlite", "favicons.sqlite-wal",
        "storage.sqlite",
        "extensions.json",  # eklenti verisi
        "addons.json",
        "addons.sqlite",
        "protections.sqlite",
        "SiteSecurityServiceState.txt",
        "revocations.txt",
        "cert_override.txt",
        "Session.json",     # sekmeler
        "sessionCheckpoints.json",
    ]

    for fname in sqlite_files:
        fp = profile / fname
        if fp.exists():
            try:
                fp.unlink()
                log(f"SILINDI: {fname}")
            except PermissionError:
                log(f"ATLA: {fname} (kilitli)")

    # localStorage / indexedDB
    webapps = profile / "storage" / "default"
    if webapps.exists():
        try:
            shutil.rmtree(webapps)
            log(f"SILINDI: localStorage / indexedDB")
        except PermissionError:
            log(f"ATLA: localStorage (kilitli)")

    print(f"  ✓ Tor profil temizligi tamamlandi")

def clean_tor_caches():
    """Cache klasorunu temizle"""
    caches = Path(TOR_CACHES)
    if caches.exists():
        for item in caches.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            except PermissionError:
                log(f"ATLA: {item.name} (kilitli)")
        leftover = list(caches.iterdir())
        if not [x for x in leftover if x.name != "." and x.name != ".."] or len(leftover) == 0:
            log(f"SILINDI: Tor caches")
        else:
            log(f"Caches kismen temizlendi ({len(leftover)} dosya kaldi - Tor acik olabilir)")
    else:
        log(f"ATLA: Caches bulunamadi")

def clean_prefetch():
    """Windows Prefetch'ten firefox.exe izlerini sil"""
    prefetch = Path(PREFETCH_DIR)
    if not prefetch.exists():
        log(f"ATLA: Prefetch bulunamadi (yetki gerekebilir)")
        return
    count = 0
    for f in prefetch.glob("FIREFOX.EXE-*.pf"):
        try:
            f.unlink()
            count += 1
        except PermissionError:
            log(f"ATLA: {f.name} (yetki yok)")
    if count:
        log(f"SILINDI: {count} prefetch dosyasi")
    else:
        log(f"Prefetch'te firefox.exe izi yok")

def clean_recent_items():
    """Windows Recent Items temizle"""
    recent = Path(RECENT_DIR)
    if not recent.exists():
        log(f"ATLA: Recent Items bulunamadi")
        return
    count = 0
    for f in recent.iterdir():
        if f.is_file():
            try:
                f.unlink()
                count += 1
            except PermissionError:
                pass
    if count:
        log(f"SILINDI: {count} recent items")
    else:
        log(f"Recent Items zaten bos")

def clean_pagefile_hint():
    """Pagefile temizligi icin uyari"""
    print("\n  [BILGI] Pagefile (RAM takasi) icin:")
    print("          regedit -> HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Memory Management")
    print("          ClearPageFileAtShutdown = 1")

# ── ANA ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n--- Hermes Iz Temizleme ---")
    print("  Tor Browser kullanimi sonrasi izler siliniyor...\n")

    clean_tor_profile()
    clean_tor_caches()
    clean_prefetch()
    clean_recent_items()
    clean_pagefile_hint()

    print("\n--- Tamamlandi ---")
