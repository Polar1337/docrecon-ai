# DocRecon AI 🧠📄

**AI-powered Document Consolidation and Duplicate Detection Tool**

DocRecon AI ist ein intelligentes Python-Tool zur Analyse, Kategorisierung und Duplikaterkennung historisch gewachsener Unternehmensdokumentation. Es hilft dabei, Ordnung in chaotische Dokumentenlandschaften zu bringen und unnötige Duplikate zu identifizieren.

## 🎯 Hauptfunktionen

- **Intelligenter Crawler**: Durchsucht lokale Ordner, Windows-Netzlaufwerke (SMB) und optional SharePoint/OneNote
- **KI-basierte Analyse**: Nutzt NLP und Machine Learning für semantische Dokumentenanalyse
- **Duplikaterkennung**: Erkennt identische und ähnliche Dokumente durch Hash-Vergleich und Embedding-Analyse
- **Automatische Kategorisierung**: Gruppiert Dokumente nach Themen und Inhalten
- **Interaktive Berichte**: Generiert detaillierte HTML-, CSV- und JSON-Berichte
- **Dashboard**: Optionale Streamlit-Weboberfläche für interaktive Analyse

## 🚀 Installation

### Voraussetzungen
- Python 3.10 oder höher
- Windows oder Linux
- Mindestens 4GB RAM (empfohlen: 8GB+)

### Installation via pip
```bash
pip install docrecon-ai
```

### Installation aus dem Quellcode
```bash
git clone https://github.com/your-username/docrecon-ai.git
cd docrecon-ai
pip install -e .
```

### Entwicklungsumgebung
```bash
git clone https://github.com/your-username/docrecon-ai.git
cd docrecon-ai
pip install -e ".[dev,dashboard,graph]"
```

## 📖 Schnellstart

### 1. Grundlegende Dokumentenanalyse
```bash
# Analysiere lokalen Ordner
docrecon scan /path/to/documents --output results.html

# Analysiere Windows-Netzlaufwerk
docrecon scan "\\\\server\\share\\documents" --output network_analysis.html

# Mit erweiterten Optionen
docrecon scan /path/to/docs --duplicates --nlp --output detailed_report.html
```

### 2. Python API verwenden
```python
from docrecon_ai import DocumentCrawler, DuplicateDetector, NLPAnalyzer

# Crawler initialisieren
crawler = DocumentCrawler()
documents = crawler.scan_directory("/path/to/documents")

# Duplikate finden
detector = DuplicateDetector()
duplicates = detector.find_duplicates(documents)

# NLP-Analyse
analyzer = NLPAnalyzer()
clusters = analyzer.cluster_documents(documents)

# Bericht generieren
from docrecon_ai.reporting import HTMLReporter
reporter = HTMLReporter()
reporter.generate_report(documents, duplicates, clusters, "report.html")
```

### 3. Dashboard starten
```bash
docrecon-dashboard --port 8501
```

## 🔧 Konfiguration

Erstellen Sie eine `config.yaml` Datei:

```yaml
# Crawler-Einstellungen
crawler:
  max_file_size: 100MB
  supported_extensions: ['.pdf', '.docx', '.txt', '.md', '.xlsx']
  ignore_patterns: ['~$*', '.tmp', 'Thumbs.db']
  
# NLP-Einstellungen
nlp:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  similarity_threshold: 0.85
  language: "de"  # oder "en"
  
# Duplikaterkennung
duplicates:
  hash_algorithm: "sha256"
  content_similarity_threshold: 0.9
  filename_similarity_threshold: 0.8

# Microsoft Graph (optional)
graph:
  tenant_id: "your-tenant-id"
  client_id: "your-client-id"
  client_secret: "your-client-secret"
```

## 📊 Unterstützte Dateiformate

| Format | Erweiterung | Text-Extraktion | Metadaten |
|--------|-------------|------------------|-----------|
| PDF | .pdf | ✅ | ✅ |
| Word | .docx, .doc | ✅ | ✅ |
| Excel | .xlsx, .xls | ✅ | ✅ |
| PowerPoint | .pptx, .ppt | ✅ | ✅ |
| Text | .txt, .md | ✅ | ✅ |
| HTML | .html, .htm | ✅ | ✅ |
| RTF | .rtf | ✅ | ✅ |
| OpenOffice | .odt, .ods | ✅ | ✅ |

## 🎛️ Kommandozeilen-Interface

```bash
# Hilfe anzeigen
docrecon --help

# Verzeichnis scannen
docrecon scan [PATH] [OPTIONS]

# Optionen:
  --output, -o          Output-Datei (HTML, CSV, JSON)
  --format, -f          Output-Format (html, csv, json)
  --duplicates, -d      Duplikaterkennung aktivieren
  --nlp, -n             NLP-Analyse aktivieren
  --config, -c          Konfigurationsdatei
  --recursive, -r       Rekursiv scannen
  --threads, -t         Anzahl Threads (Standard: 4)
  --verbose, -v         Verbose-Modus

# Beispiele:
docrecon scan /home/docs --duplicates --nlp --output report.html
docrecon scan "C:\\Documents" --format csv --threads 8
docrecon scan //server/share --config custom.yaml --verbose
```

## 🏗️ Architektur

```
docrecon_ai/
├── src/docrecon_ai/
│   ├── __init__.py
│   ├── cli.py              # Kommandozeilen-Interface
│   ├── config.py           # Konfigurationsmanagement
│   ├── crawler/            # Dokumenten-Crawler
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── local.py        # Lokale Dateien
│   │   ├── smb.py          # SMB/CIFS Shares
│   │   └── graph.py        # Microsoft Graph API
│   ├── nlp/                # NLP-Analyse
│   │   ├── __init__.py
│   │   ├── extractor.py    # Text-Extraktion
│   │   ├── embeddings.py   # Embedding-Generierung
│   │   ├── clustering.py   # Dokumenten-Clustering
│   │   └── entities.py     # Named Entity Recognition
│   ├── detection/          # Duplikaterkennung
│   │   ├── __init__.py
│   │   ├── hash.py         # Hash-basierte Erkennung
│   │   ├── similarity.py   # Semantische Ähnlichkeit
│   │   └── versioning.py   # Versionserkennung
│   ├── reporting/          # Berichtserstellung
│   │   ├── __init__.py
│   │   ├── html.py         # HTML-Reports
│   │   ├── csv.py          # CSV-Export
│   │   └── json.py         # JSON-Export
│   ├── dashboard/          # Streamlit Dashboard
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── components/
│   └── utils/              # Hilfsfunktionen
│       ├── __init__.py
│       ├── file_utils.py
│       └── text_utils.py
├── tests/                  # Unit Tests
├── docs/                   # Dokumentation
├── examples/               # Beispiele
└── config/                 # Konfigurationsdateien
```

## 🔍 Funktionsweise

### 1. Crawler-Phase
- Durchsucht rekursiv alle angegebenen Verzeichnisse
- Extrahiert Metadaten (Größe, Datum, Pfad)
- Berechnet SHA256-Hashes für Duplikaterkennung
- Unterstützt lokale Pfade, UNC-Pfade und SMB-Shares

### 2. Text-Extraktion
- Extrahiert Text aus verschiedenen Dateiformaten
- Bereinigt und normalisiert Textinhalte
- Erkennt Sprache und Encoding automatisch

### 3. NLP-Analyse
- Generiert Embeddings mit Sentence Transformers
- Führt Named Entity Recognition durch
- Extrahiert Schlüsselwörter und Themen
- Clustert semantisch ähnliche Dokumente

### 4. Duplikaterkennung
- **Exakte Duplikate**: SHA256-Hash-Vergleich
- **Ähnliche Inhalte**: Cosine-Similarity der Embeddings
- **Versionserkennung**: Analyse von Dateinamen-Mustern

### 5. Berichtserstellung
- Generiert interaktive HTML-Berichte
- Exportiert strukturierte CSV-Daten
- Erstellt JSON für Weiterverarbeitung
- Schlägt Archivierungs-/Löschaktionen vor

## 🎨 Dashboard-Features

Das optionale Streamlit-Dashboard bietet:

- **Übersichtsdashboard**: Statistiken und Kennzahlen
- **Dokumentenbrowser**: Durchsuchen und Filtern
- **Duplikatansicht**: Gruppierte Duplikate mit Vorschau
- **Themen-Explorer**: Semantische Cluster visualisieren
- **Aktionsplaner**: Lösch- und Archivierungsvorschläge

## 🔐 Sicherheit und Datenschutz

- **Lokale Verarbeitung**: Alle Daten bleiben auf Ihrem System
- **Keine Cloud-Übertragung**: Optional lokale NLP-Modelle
- **Verschlüsselung**: Sichere Übertragung bei SMB-Zugriff
- **Audit-Log**: Vollständige Protokollierung aller Aktionen

## 🤝 Beitragen

Wir freuen uns über Beiträge! Bitte lesen Sie unsere [Contribution Guidelines](CONTRIBUTING.md).

### Entwicklung
```bash
# Repository klonen
git clone https://github.com/your-username/docrecon-ai.git
cd docrecon-ai

# Entwicklungsumgebung einrichten
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\\Scripts\\activate  # Windows

# Dependencies installieren
pip install -e ".[dev,dashboard,graph]"

# Tests ausführen
pytest

# Code formatieren
black src/ tests/
flake8 src/ tests/
```

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe [LICENSE](LICENSE) für Details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/docrecon-ai/issues)
- **Diskussionen**: [GitHub Discussions](https://github.com/your-username/docrecon-ai/discussions)
- **Wiki**: [Dokumentation](https://github.com/your-username/docrecon-ai/wiki)

## 🏆 Roadmap

- [ ] **v1.1**: Outlook PST/OST Unterstützung
- [ ] **v1.2**: OCR für gescannte Dokumente
- [ ] **v1.3**: Automatische Ordnerstruktur-Vorschläge
- [ ] **v1.4**: Integration mit DMS-Systemen
- [ ] **v1.5**: Machine Learning für Klassifizierung

---

**Entwickelt mit ❤️ von Manus AI**

