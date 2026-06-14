# MCP Filesystem Sınırlamaları

MCP filesystem tool'u sadece **izin verilen dizinler** altında çalışır.
Hermes Agent'da bu şu anlama gelir:

## İzin Verilen
- `C:\Users\marko\OneDrive\Belgeler\Obsidian Vault\Hermes` — skill dosyaları, indeksler

## İzin Verilmeyen
- Vault'un geri kalanı (`Notlar/`, `Gunluk/`, diğer klasörler)
- `C:\Users\marko\AppData\Local\hermes\skills\` — Hermes skill'leri (MCP ile okunamaz)
- `C:\Users\marko\hermes-ai\` — proje dosyaları
- Herhangi bir sistem dizini

## Pratik Etkisi

| İşlem | Araç | Çalışır mı? |
|-------|------|-------------|
| `Obsidian Vault\Hermes\Skills\` altını oku | mcp_filesystem | ✓ Evet |
| `Obsidian Vault\Hermes\Skills\` altına yaz | mcp_filesystem | ✓ Evet |
| `Obsidian Vault\Notlar\` altını oku | mcp_filesystem | ✗ Hayır |
| `skills\` altındaki SKILL.md'leri oku | mcp_filesystem | ✗ Hayır |
| `skills\` altındaki dosyaları sil/yeniden adlandır | mcp_filesystem | ✗ Hayır |
| `skills\` altındaki dosyaları yönet | terminal (bash) | ✓ Evet |
| Obsidian vault dışı herhangi bir işlem | mcp_filesystem | ✗ Hayır |

## Çözüm

- **Obsidian dosyaları için:** MCP filesystem kullan (izinli)
- **Hermes skills dizini için:** `terminal` (bash) veya `read_file`/`write_file`/`patch` kullan
- **Root seviyesinde .md temizliği:** `terminal` ile `mv <file> <file>.obsolete` yap (rm kullanma, approval gerekir)
