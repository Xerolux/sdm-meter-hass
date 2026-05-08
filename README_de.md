[**English**](README.md) | **Deutsch**

# SDM Meter (Modbus RTU-over-TCP) für Home Assistant

Benutzerdefinierte Home Assistant Integration für Eastron SDM-Stromzähler über Modbus RTU-over-TCP oder Modbus TCP.

## Funktionen
- Einrichtung über den Konfigurations-Assistenten direkt in der Home Assistant-Oberfläche
- Unterstützung für 3-phasige und 1-phasige SDM-Modelle
- Abfrageintervall in den Integrations-Optionen konfigurierbar
- Energie-Sensoren sind kompatibel mit dem Home Assistant Energie-Dashboard
- HACS-kompatible Repository-Struktur
- Diagnose-Endpunkt zur einfacheren Fehlerbehebung

## Unterstützte Modelle
- `SDM630 / SDM72` (3-phasig): vollständige Messungen auf Phasen- und Gesamtebene
- `SDM120 / SDM230` (1-phasig): automatische Filterung nicht unterstützter 3-phasiger Register

## Installation

### Option 1: HACS (empfohlen)
1. HACS in Home Assistant öffnen.
2. Zu `Integrationen` wechseln.
3. Das Menü oben rechts öffnen und `Benutzerdefinierte Repositories` auswählen.
4. Die URL dieses Repositories hinzufügen und `Integration` als Kategorie wählen.
5. Nach `SDM Meter` suchen und installieren.
6. Home Assistant neu starten.

### Option 2: Manuelle Installation
1. Den Ordner `custom_components/sdm_meter` in das Home Assistant `custom_components`-Verzeichnis kopieren.
2. Home Assistant neu starten.

## Konfiguration
1. `Einstellungen -> Geräte & Dienste` öffnen.
2. Auf `Integration hinzufügen` klicken und `SDM Meter` auswählen.
3. Host/IP, Port, Slave-ID, Verbindungstyp und Aktualisierungsintervall eingeben.
4. Das Formular absenden.

## Empfohlene Abfrageintervalle
- Mit `10` Sekunden für die meisten RS485-zu-TCP-Gateways beginnen.
- `5` Sekunden nur bei stabilen und schnellen Verbindungen verwenden.
- Auf `15-30` Sekunden erhöhen, wenn Timeouts oder zeitweise nicht verfügbare Sensoren auftreten.

## Typische Entitäten
Die Integration kann Spannung, Strom, Wirk-/Blind-/Scheinleistung, Frequenz, Leistungsfaktor, Phasenwinkel und mehrere Energiezähler bereitstellen.

## Fehlerbehebung
- Sicherstellen, dass Konverter und Stromzähler dieselben Serielleinstellungen verwenden (Baudrate, Parität, Stoppbits).
- Überprüfen, ob `Host`, `Port` und `Slave-ID` mit dem Konverter-/Zähler-Setup übereinstimmen.
- Wenn keine Daten angezeigt werden, ein langsameres Abfrageintervall testen (z. B. `10-15` Sekunden).
- Home Assistant-Protokolle auf `sdm_meter`- und `pymodbus`-Meldungen prüfen.

## Bekannte Einschränkungen
- Einige SDM-Varianten stellen weniger Register bereit als andere; nicht unterstützte Werte werden where possible gefiltert.
- Die Qualität der Gateways variiert: günstige Konverter können bei hohen Abfrageintervallen Anfragen verwerfen.
- Die Register-Byte-Reihenfolge ist derzeit auf Big-Endian-Float-Dekodierung festgelegt.

## Entwicklung
- Syntaxprüfung: `python3 -m compileall custom_components/sdm_meter`
- Tests: `pytest -q -o cache_dir=/tmp/pytest_cache`
- Lint: `ruff check --no-cache custom_components tests`
    - Typprüfung: `mypy custom_components/sdm_meter/flow_helpers.py custom_components/sdm_meter/register_map.py tests`

## Lizenz
MIT (siehe [LICENSE](LICENSE)).
