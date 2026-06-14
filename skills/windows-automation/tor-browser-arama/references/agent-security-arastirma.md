# Agent Güvenlik Açıkları Araştırma Referansı

Haziran 2026 itibarıyla hack forumlarında en çok konuşulan konu:
**AI Agent güvenlik açıkları** (Agentjacking, LangGraph RCE, OpenClaw).

## Anahtar Kaynaklar (Tor ile erişilir)

| Kaynak | URL | Ne İçin |
|--------|-----|---------|
| TheHackerNews | https://thehackernews.com/ | Güncel güvenlik haberleri, 0-day, exploit |
| BleepingComputer | https://www.bleepingcomputer.com/ | Teknik detay, yama bilgisi |
| DDG HTML | https://html.duckduckgo.com/html/ | Genel arama (Tor üzerinden) |

## Agentjacking — Teknik Özet

**Kaynak:** Tenet Security araştırması, TheHackerNews
**Hedef:** Claude Code, Cursor gibi AI kodlama asistanları
**Vektör:** Sentry DSN + MCP protokolü

**Zincir:**
1. Saldırgan Sentry event ingestion API'sine sahte hata + kötü niyetli "resolution" enjekte eder
2. Geliştirici "şu hatayı düzelt" der
3. AI ajanı Sentry MCP sunucusundan "çözüm"ü okur (trusted system output sanır)
4. Saldırganın kodunu çalıştırır (developer yetkileriyle, developer makinesinde)

**Etki:** EDR/WAF/IAM/VPN/Cloudflare/firewall bypass
**Boyut:** 2.388+ organizasyon açık, %85 exploit başarı oranı
**Sentry:** "Teknik olarak savunulamaz" — düzeltmeyi reddetti, global content filter koydu

## İlgili Diğer Açıklar (Haziran 2026)

- **LangGraph RCE** — Self-hosted AI agent'larda uzaktan kod çalıştırma
- **OpenClaw Attack** — AI agent'lardan kod + secret sızdırma
- **Salesforce LLM Agent** — LLM ile Salesforce hack

## Araştırma Akışı

1. TheHackerNews ana sayfa → `<h2 class="home-title">` regex ile başlıklar
2. Makale linkini bul → regex ile href çek
3. Makale içeriği → `<p>` etiketlerinden metin çek
4. BleepingComputer → `<h4>` başlıkları
5. Bulguları özetle: en sıcak konu → teknik detay → etki/istatistik
