# Entwicklung

[← Zurück zur Übersicht](../README.md)

## Releases automatisch erstellen (nur für Entwicklung/Maintenance)

Zwei GitHub-Actions-Dateien im `.github`-Ordner automatisieren das
Release-Management dieses Repositories:

- **`.github/release.yml`**: Kategorisiert die Release Notes anhand von
  PR-Labels (🚀 Neue Funktionen, 🐛 Fehlerbehebungen, 📚 Dokumentation,
  🧹 Sonstiges).
- **`.github/workflows/auto-release.yml`**: Erstellt bei jeder Änderung an
  der Versionsnummer in `custom_components/ha_smart_ventilation/manifest.json`
  auf dem `main`-Branch automatisch einen passenden Git-Tag (`vX.Y.Z`) und
  ein GitHub-Release mit automatisch generierten Notes - nutzt dabei die
  Kategorisierung aus `release.yml`. Existiert der Tag bereits, passiert
  nichts (kein doppeltes Release).

Der Ablauf bei einer neuen Version ist damit: Code ändern → Version in
`manifest.json` hochzählen → auf `main` pushen. Tag und Release entstehen
automatisch, ohne manuellen Schritt auf GitHub.

**Pre-Releases (Beta-Versionen):** Enthält die Versionsnummer einen
Bindestrich nach dem semver-Schema (z. B. `0.33.0-beta.1`), markiert der
Workflow das erzeugte GitHub-Release automatisch als **Pre-Release** und
setzt es nicht als "Latest Release". HACS zeigt Pre-Releases nur Nutzern
an, die für diese Integration in HACS unter "Beta-Versionen anzeigen"
zugestimmt haben - alle anderen bleiben unverändert auf der letzten
regulären (nicht-Pre-Release-)Version. Sobald eine Beta-Version bestätigt
ist, wird sie durch eine reguläre Versionsnummer ohne Bindestrich (z. B.
`0.33.0`) abgelöst, die dann ganz normal für alle sichtbar wird.
