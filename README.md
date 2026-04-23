# Aerex PHK180 – Home Assistant Integration

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

Inoffizielle Home Assistant Integration für das **Aerex PHK180** Passivhaus-Kompaktgerät (Lüftung + Wärmepumpe + Warmwasser).

## Funktionen

### Sensoren (read-only)
| Sensor | Einheit | Beschreibung |
|---|---|---|
| Raumtemperatur | °C | Isttemperatur Referenzraum |
| Raumsolltemperatur | °C | Aktueller Sollwert |
| Absenktemperatur | °C | Nachtabsenkung |
| T-Lufteintritt | °C | Außenluft am Geräteeintritt |
| T-Zuluft | °C | Zuluft nach WRG/WP |
| T-Abluft | °C | Abluft aus dem Haus |
| Warmwasserspeicher oben/unten | °C | Speichertemperaturen |
| T-Verdampfer | °C | Verdampfertemperatur WP |
| Drehzahl Zu-/Abluft | rpm | Ventilatordrehzahlen |
| Volumenstrom | m³/h | Aktueller Luftvolumenstrom |
| CO₂ Sensor 1–3 | ppm | CO₂-Werte (Wohnzimmer, WC, Küche) |
| Relative Feuchte | % | Feuchtemessung |
| Filter Restlaufzeit | Tage | Geräte- und Außenfilter |
| Betriebsstunden | h | WP und Lüftung gesamt |
| Betriebsart | Text | Aktuelle Betriebsart |
| Lüftungsstufe | Text | Aus/Feuchteschutz/Reduziert/Nenn/Intensiv |
| Bypass | Text | zu/auf |

### Steuerung (read-write)
- **Climate Entity**: Raumsolltemperatur einstellen (+/- 0.5°C Schritte)
- **Switch Stoßlüftung**: Intensivlüftung an/aus
- **Switch Sommerbetrieb**: Jahreszeit Winter/Sommer umschalten

### Binärsensoren
- Wärmepumpe läuft
- Elektroheizstab aktiv
- Stoßlüftung aktiv
- Filterwechsel fällig (Gerät / Außen)
- Störung vorhanden

## Voraussetzungen

- Aerex PHK180 mit aktiviertem Webserver und fester IP im Heimnetz
- Home Assistant 2024.1.0 oder neuer

## Installation via HACS

1. HACS → Integrations → ⋮ → Custom repositories
2. URL: `https://github.com/DEIN_GITHUB/ha-aerex-phk180`
3. Kategorie: Integration
4. Download → Neustart HA
5. Einstellungen → Geräte & Dienste → Integration hinzufügen → "Aerex PHK180"
6. IP-Adresse eingeben

## Protokoll

Das Gerät kommuniziert über einen eingebauten Webserver (entwickelt von Hermes Electronic).
Daten werden über CGX-Endpunkte (XML-Format) abgerufen:
- `GET /index.cgx` – Grundzustand (alle 30s)
- `GET /details.cgx` – Detailwerte
- `GET /settings.cgx` – Einstellungen

Schreibzugriffe erfolgen via HTTP GET mit Parametern:
- `C[register][kanal][richtung]` – Wert inkrementell ändern
- `S[register][kanal]` – Wert setzen/umschalten

## Disclaimer

Inoffizielle Integration, nicht von Aerex unterstützt. Nutzung auf eigene Gefahr.
