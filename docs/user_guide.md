# DocRecon AI - Benutzeranleitung

## Inhaltsverzeichnis

1. [Einführung](#einführung)
2. [Installation](#installation)
3. [Erste Schritte](#erste-schritte)
4. [Kommandozeilen-Interface](#kommandozeilen-interface)
5. [Konfiguration](#konfiguration)
6. [Dashboard verwenden](#dashboard-verwenden)
7. [Berichte verstehen](#berichte-verstehen)
8. [Häufige Anwendungsfälle](#häufige-anwendungsfälle)
9. [Tipps und Best Practices](#tipps-und-best-practices)
10. [Fehlerbehebung](#fehlerbehebung)

## Einführung

DocRecon AI ist ein intelligentes Tool zur Analyse und Konsolidierung von Unternehmensdokumentationen. Es hilft dabei, Duplikate zu identifizieren, ähnliche Inhalte zu finden und Empfehlungen zur Bereinigung Ihrer Dokumentensammlung zu geben.

### Was kann DocRecon AI?

- **Duplikate finden**: Erkennt exakte Duplikate durch Hash-Vergleich
- **Ähnliche Inhalte identifizieren**: Nutzt KI zur semantischen Ähnlichkeitsanalyse
- **Versionserkennung**: Identifiziert verschiedene Versionen desselben Dokuments
- **Speicherplatz analysieren**: Berechnet potenzielle Einsparungen
- **Berichte generieren**: Erstellt detaillierte HTML-, CSV- und JSON-Berichte
- **Interaktives Dashboard**: Bietet eine benutzerfreundliche Web-Oberfläche

### Unterstützte Quellen

- Lokale Dateisysteme
- Windows-Netzlaufwerke (SMB/CIFS)
- SharePoint Online
- OneDrive for Business
- OneNote-Notizbücher (über Microsoft Graph API)

### Unterstützte Dateiformate

- PDF-Dokumente
- Microsoft Office (Word, Excel, PowerPoint)
- Textdateien
- HTML-Dateien
- Und viele weitere...

## Installation

### Systemanforderungen

- Python 3.8 oder höher
- Mindestens 4 GB RAM (8 GB empfohlen für große Dokumentensammlungen)
- Ausreichend Speicherplatz für Berichte und Cache

### Installation über pip

```bash
pip install docrecon-ai
```

### Installation aus dem Quellcode

```bash
git clone https://github.com/your-org/docrecon-ai.git
cd docrecon-ai
pip install -e .
```

### Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### Optionale Abhängigkeiten

Für erweiterte Funktionen installieren Sie zusätzliche Pakete:

```bash
# Für Dashboard-Funktionalität
pip install streamlit

# Für Microsoft Graph API
pip install msal requests

# Für erweiterte NLP-Features
pip install spacy transformers
```

## Erste Schritte

### Schnellstart

1. **Einfache Analyse starten**:
```bash
docrecon_ai analyze /pfad/zu/dokumenten --output ./ergebnisse
```

2. **Ergebnisse anzeigen**:
```bash
# HTML-Bericht öffnen
open ./ergebnisse/report.html

# Dashboard starten
docrecon_ai dashboard --results ./ergebnisse/analysis_results.json
```

### Ihr erstes Projekt

Lassen Sie uns eine einfache Analyse Ihrer Dokumente durchführen:

1. **Verzeichnis vorbereiten**: Stellen Sie sicher, dass Sie Lesezugriff auf die zu analysierenden Dokumente haben.

2. **Analyse starten**:
```bash
docrecon_ai analyze "C:\Meine Dokumente" --output ./meine_analyse --include-nlp
```

3. **Ergebnisse prüfen**: Nach Abschluss der Analyse finden Sie in `./meine_analyse/` verschiedene Berichte.

4. **Dashboard öffnen**:
```bash
docrecon_ai dashboard --results ./meine_analyse/analysis_results.json
```

## Kommandozeilen-Interface

### Hauptbefehle

#### analyze - Dokumente analysieren

```bash
docrecon_ai analyze [PFADE] --output AUSGABE [OPTIONEN]
```

**Beispiele**:
```bash
# Einfache Analyse
docrecon_ai analyze /dokumente --output ./ergebnisse

# Mit NLP-Analyse
docrecon_ai analyze /dokumente --output ./ergebnisse --include-nlp

# Bestimmte Dateitypen
docrecon_ai analyze /dokumente --output ./ergebnisse --file-types .pdf .docx

# Maximale Anzahl Dateien
docrecon_ai analyze /dokumente --output ./ergebnisse --max-files 1000
```

**Optionen**:
- `--include-nlp`: Aktiviert semantische Analyse (langsamer, aber detaillierter)
- `--skip-similarity`: Überspringt Ähnlichkeitsanalyse (schneller)
- `--max-files N`: Begrenzt die Anzahl der zu analysierenden Dateien
- `--file-types`: Beschränkt auf bestimmte Dateierweiterungen
- `--config`: Verwendet eine benutzerdefinierte Konfigurationsdatei

#### report - Berichte generieren

```bash
docrecon_ai report ERGEBNISSE --output AUSGABE [OPTIONEN]
```

**Beispiele**:
```bash
# HTML und CSV Berichte
docrecon_ai report ./ergebnisse/analysis_results.json --output ./berichte

# Nur HTML-Bericht
docrecon_ai report ./ergebnisse/analysis_results.json --output ./berichte --formats html

# Mit benutzerdefiniertem Titel
docrecon_ai report ./ergebnisse/analysis_results.json --output ./berichte --title "Meine Dokumentenanalyse"
```

#### dashboard - Interaktives Dashboard

```bash
docrecon_ai dashboard [OPTIONEN]
```

**Beispiele**:
```bash
# Dashboard mit Ergebnissen starten
docrecon_ai dashboard --results ./ergebnisse/analysis_results.json

# Auf anderem Port
docrecon_ai dashboard --results ./ergebnisse/analysis_results.json --port 8080
```

#### export - Daten exportieren

```bash
docrecon_ai export ERGEBNISSE --format FORMAT --output AUSGABE [OPTIONEN]
```

**Beispiele**:
```bash
# CSV-Export
docrecon_ai export ./ergebnisse/analysis_results.json --format csv --output ./export.csv

# JSON-Export
docrecon_ai export ./ergebnisse/analysis_results.json --format json --output ./export.json

# Nur Duplikate exportieren
docrecon_ai export ./ergebnisse/analysis_results.json --format csv --output ./duplikate.csv --component duplicates
```

### Globale Optionen

- `--config, -c`: Pfad zur Konfigurationsdatei
- `--log-level`: Logging-Level (DEBUG, INFO, WARNING, ERROR)
- `--log-file`: Pfad zur Log-Datei
- `--verbose, -v`: Ausführliche Ausgabe

## Konfiguration

### Konfigurationsdatei erstellen

Erstellen Sie eine YAML-Datei für Ihre Einstellungen:

```yaml
# config.yaml
crawler:
  max_file_size_mb: 100
  include_hidden_files: false
  file_extensions:
    - .pdf
    - .docx
    - .txt
    - .xlsx
    - .pptx

nlp:
  enable_embeddings: true
  similarity_threshold: 0.8

detection:
  hash_algorithm: sha256
  similarity_threshold: 0.9

reporting:
  output_formats:
    - html
    - csv
  include_charts: true
```

### Konfiguration verwenden

```bash
docrecon_ai analyze /dokumente --output ./ergebnisse --config config.yaml
```

### Umgebungsvariablen

Überschreiben Sie Einstellungen mit Umgebungsvariablen:

```bash
export DOCRECON_CRAWLER_MAX_FILE_SIZE_MB=200
export DOCRECON_NLP_SIMILARITY_THRESHOLD=0.85
docrecon_ai analyze /dokumente --output ./ergebnisse
```

## Dashboard verwenden

### Dashboard starten

```bash
docrecon_ai dashboard --results ./ergebnisse/analysis_results.json --port 8501
```

Öffnen Sie dann Ihren Browser und navigieren Sie zu `http://localhost:8501`.

### Dashboard-Features

#### Übersichtsseite
- Zusammenfassung der Analyseergebnisse
- Wichtige Kennzahlen und Statistiken
- Empfehlungen mit hoher Priorität

#### Dokumenten-Explorer
- Durchsuchen Sie alle analysierten Dokumente
- Filtern nach Dateityp, Größe, Datum
- Sortieren nach verschiedenen Kriterien

#### Duplikat-Analyse
- Detaillierte Ansicht aller gefundenen Duplikate
- Gruppierung nach Duplikattyp
- Interaktive Tabellen mit Aktionsmöglichkeiten

#### Ähnlichkeits-Analyse
- Semantisch ähnliche Dokumente
- Ähnlichkeits-Scores und Visualisierungen
- Cluster-Ansicht verwandter Dokumente

#### Empfehlungen
- Priorisierte Handlungsempfehlungen
- Geschätzte Speicherplatzeinsparungen
- Exportmöglichkeiten für Aktionslisten

### Dashboard-Navigation

- **Seitenleiste**: Hauptnavigation zwischen verschiedenen Ansichten
- **Filter**: Dynamische Filter für alle Datenansichten
- **Export**: Download-Buttons für Daten und Berichte
- **Aktualisierung**: Automatische oder manuelle Datenaktualisierung

## Berichte verstehen

### HTML-Bericht

Der HTML-Bericht ist die umfassendste Darstellung Ihrer Analyseergebnisse:

#### Executive Summary
- Gesamtanzahl analysierter Dokumente
- Gefundene Duplikate und ähnliche Dokumente
- Potenzielle Speicherplatzeinsparungen
- Wichtigste Empfehlungen

#### Detailanalyse
- **Dokumenteninventar**: Vollständige Liste aller Dokumente
- **Duplikatgruppen**: Exakte Duplikate nach Hash-Werten
- **Ähnliche Dokumente**: Semantisch verwandte Inhalte
- **Versionserkennung**: Identifizierte Dokumentversionen

#### Visualisierungen
- Diagramme zur Dateityp-Verteilung
- Größenanalyse und Speichernutzung
- Zeitlinien für Dokumenterstellung
- Ähnlichkeits-Heatmaps

### CSV-Export

CSV-Dateien eignen sich für weitere Datenanalyse:

- `documents.csv`: Vollständiges Dokumenteninventar
- `duplicates.csv`: Alle gefundenen Duplikate
- `recommendations.csv`: Handlungsempfehlungen
- `statistics.csv`: Zusammenfassende Statistiken

### JSON-Export

JSON-Format für programmatischen Zugriff:

```json
{
  "metadata": {
    "analysis_timestamp": "2023-12-01T10:00:00Z",
    "total_documents": 1500,
    "analysis_duration": 45.2
  },
  "documents": [...],
  "duplicates": {...},
  "recommendations": {...}
}
```

## Häufige Anwendungsfälle

### 1. Speicherplatz freigeben

**Ziel**: Identifizieren und entfernen von Duplikaten zur Speicherplatzoptimierung.

**Vorgehen**:
```bash
# Analyse mit Fokus auf Duplikate
docrecon_ai analyze /dokumente --output ./cleanup --skip-similarity

# Empfehlungen exportieren
docrecon_ai export ./cleanup/analysis_results.json --format csv --output ./zu_loeschen.csv --component duplicates
```

**Nachbearbeitung**: Prüfen Sie die Empfehlungen und löschen Sie bestätigte Duplikate.

### 2. Dokumentenkonsolidierung

**Ziel**: Ähnliche Dokumente finden und zusammenführen.

**Vorgehen**:
```bash
# Vollständige Analyse mit NLP
docrecon_ai analyze /dokumente --output ./konsolidierung --include-nlp

# Dashboard für interaktive Analyse
docrecon_ai dashboard --results ./konsolidierung/analysis_results.json
```

**Nachbearbeitung**: Nutzen Sie das Dashboard zur Identifikation von Konsolidierungsmöglichkeiten.

### 3. Compliance-Audit

**Ziel**: Vollständige Dokumentation der Dokumentenlandschaft.

**Vorgehen**:
```bash
# Umfassende Analyse
docrecon_ai analyze /alle_dokumente --output ./audit --include-nlp --config audit_config.yaml

# Detaillierte Berichte
docrecon_ai report ./audit/analysis_results.json --output ./audit_berichte --formats html csv json
```

### 4. Migration vorbereiten

**Ziel**: Dokumentensammlung vor Migration bereinigen.

**Vorgehen**:
```bash
# Analyse der Quellsysteme
docrecon_ai analyze /altes_system --output ./migration_prep

# Empfehlungen für Bereinigung
docrecon_ai export ./migration_prep/analysis_results.json --format csv --output ./migration_aktionen.csv
```

### 5. Regelmäßige Wartung

**Ziel**: Kontinuierliche Überwachung der Dokumentenqualität.

**Vorgehen**:
```bash
# Wöchentliche Analyse
docrecon_ai analyze /dokumente --output ./wartung_$(date +%Y%m%d) --config wartung_config.yaml

# Trend-Analyse durch Vergleich mit vorherigen Ergebnissen
```

## Tipps und Best Practices

### Performance-Optimierung

1. **Dateitypen begrenzen**: Analysieren Sie nur relevante Dateiformate
```bash
docrecon_ai analyze /dokumente --file-types .pdf .docx .xlsx --output ./ergebnisse
```

2. **Batch-Größe anpassen**: Für große Sammlungen die Konfiguration optimieren
```yaml
performance:
  max_workers: 8
  chunk_size: 500
```

3. **Caching nutzen**: Aktivieren Sie Caching für wiederholte Analysen
```yaml
performance:
  enable_caching: true
  cache_ttl_hours: 24
```

### Genauigkeit verbessern

1. **NLP für wichtige Analysen**: Nutzen Sie `--include-nlp` für kritische Projekte
2. **Schwellenwerte anpassen**: Feintuning der Ähnlichkeitsschwellen
```yaml
nlp:
  similarity_threshold: 0.85  # Höher = strenger
detection:
  similarity_threshold: 0.95
```

3. **Ausschlussmuster definieren**: Vermeiden Sie irrelevante Dateien
```yaml
crawler:
  exclude_patterns:
    - "*.tmp"
    - "~$*"
    - ".git/*"
    - "node_modules/*"
```

### Sicherheit und Datenschutz

1. **Lokale Verarbeitung**: Standardmäßig werden alle Daten lokal verarbeitet
2. **Zugriffsrechte prüfen**: Stellen Sie sicher, dass nur autorisierte Personen Zugriff haben
3. **Temporäre Dateien**: Werden automatisch nach der Analyse gelöscht
4. **Logs bereinigen**: Entfernen Sie sensible Informationen aus Log-Dateien

### Workflow-Integration

1. **Automatisierung**: Integrieren Sie DocRecon AI in Ihre bestehenden Workflows
```bash
#!/bin/bash
# Automatisches Cleanup-Script
docrecon_ai analyze /dokumente --output ./daily_check
if [ -f ./daily_check/recommendations.csv ]; then
    # Weitere Verarbeitung...
fi
```

2. **API-Integration**: Nutzen Sie JSON-Export für Systemintegration
3. **Berichterstattung**: Automatische Berichte für Management

## Fehlerbehebung

### Häufige Probleme

#### "Speicher nicht ausreichend"

**Symptom**: Fehler bei der Verarbeitung großer Dateien
**Lösung**:
```yaml
performance:
  memory_limit_mb: 4096
  chunk_size: 100
```

#### "Zugriff verweigert"

**Symptom**: Kann nicht auf Netzlaufwerke zugreifen
**Lösung**:
- Prüfen Sie Ihre Anmeldedaten
- Stellen Sie sicher, dass Sie Lesezugriff haben
- Verwenden Sie UNC-Pfade für Windows-Freigaben

#### "Dashboard startet nicht"

**Symptom**: Streamlit-Dashboard funktioniert nicht
**Lösung**:
```bash
pip install streamlit
docrecon_ai dashboard --port 8080  # Anderen Port versuchen
```

#### "NLP-Analyse schlägt fehl"

**Symptom**: Fehler bei semantischer Analyse
**Lösung**:
```bash
pip install sentence-transformers
# Oder ohne NLP-Features:
docrecon_ai analyze /dokumente --output ./ergebnisse --skip-similarity
```

### Logging und Diagnose

#### Debug-Modus aktivieren

```bash
docrecon_ai analyze /dokumente --output ./ergebnisse --log-level DEBUG --log-file debug.log
```

#### Häufige Log-Meldungen

- `INFO: Found X documents`: Normale Fortschrittsmeldung
- `WARNING: File too large`: Datei überschreitet Größenlimit
- `ERROR: Permission denied`: Zugriffsproblem
- `DEBUG: Processing file`: Detaillierte Verarbeitungsinfo

### Support erhalten

1. **Dokumentation prüfen**: Konsultieren Sie die technische Dokumentation
2. **GitHub Issues**: Suchen Sie nach ähnlichen Problemen
3. **Community Forum**: Stellen Sie Fragen in der Community
4. **Issue erstellen**: Erstellen Sie ein neues Issue mit:
   - Systeminformationen
   - Fehlermeldungen
   - Schritte zur Reproduktion
   - Konfigurationsdateien (ohne sensible Daten)

### Systemanforderungen prüfen

```bash
# Python-Version prüfen
python --version

# Verfügbaren Speicher prüfen
free -h  # Linux
wmic OS get TotalVisibleMemorySize /value  # Windows

# Festplattenspeicher prüfen
df -h  # Linux
dir  # Windows
```

---

*Diese Benutzeranleitung wird regelmäßig aktualisiert. Für die neuesten Informationen besuchen Sie das Projekt-Repository.*

