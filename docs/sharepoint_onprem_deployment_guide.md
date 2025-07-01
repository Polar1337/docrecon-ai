# DocRecon AI - SharePoint 2019 On-Premise Deployment Guide

**Autor:** Manus AI  
**Version:** 1.0  
**Datum:** Januar 2024  
**Zielgruppe:** IT-Administratoren, System-Integratoren

## Inhaltsverzeichnis

1. [Einführung](#einführung)
2. [Systemvoraussetzungen](#systemvoraussetzungen)
3. [Zugangsdaten und Berechtigungen](#zugangsdaten-und-berechtigungen)
4. [Installation und Konfiguration](#installation-und-konfiguration)
5. [SharePoint 2019 Konfiguration](#sharepoint-2019-konfiguration)
6. [OneNote Integration](#onenote-integration)
7. [Sicherheitseinstellungen](#sicherheitseinstellungen)
8. [Erste Analyse durchführen](#erste-analyse-durchführen)
9. [Fehlerbehebung](#fehlerbehebung)
10. [Best Practices](#best-practices)

---

## Einführung

Dieser umfassende Leitfaden führt Sie durch die komplette Einrichtung von DocRecon AI für SharePoint 2019 On-Premise Umgebungen. DocRecon AI ist ein intelligentes Dokumentenanalyse-Tool, das speziell für Unternehmensumgebungen entwickelt wurde und eine nahtlose Integration mit SharePoint 2019 On-Premise sowie OneNote-Dokumenten bietet.

Die Implementierung von DocRecon AI in einer SharePoint 2019 On-Premise Umgebung erfordert sorgfältige Planung und Konfiguration verschiedener Komponenten. Dieser Guide stellt sicher, dass Sie alle notwendigen Schritte verstehen und korrekt ausführen, um eine erfolgreiche Deployment zu gewährleisten.

SharePoint 2019 On-Premise unterscheidet sich erheblich von SharePoint Online in Bezug auf Authentifizierung, API-Zugriff und Sicherheitsmodell. Während SharePoint Online moderne OAuth2-Authentifizierung und REST APIs nutzt, basiert SharePoint 2019 On-Premise auf traditionellen Windows-Authentifizierungsmethoden wie NTLM und Kerberos. Diese Unterschiede erfordern spezielle Konfigurationsansätze, die in diesem Guide detailliert behandelt werden.

---

## Systemvoraussetzungen

### Hardware-Anforderungen

Für eine optimale Performance von DocRecon AI in einer SharePoint 2019 On-Premise Umgebung sollten folgende Mindestanforderungen erfüllt sein:

**Minimale Systemanforderungen:**
- **CPU:** 4 Kerne, 2.5 GHz oder höher
- **RAM:** 8 GB (16 GB empfohlen für große Dokumentensammlungen)
- **Speicherplatz:** 50 GB freier Speicherplatz für Anwendung und temporäre Dateien
- **Netzwerk:** Gigabit-Ethernet-Verbindung zum SharePoint-Server

**Empfohlene Systemanforderungen:**
- **CPU:** 8 Kerne, 3.0 GHz oder höher
- **RAM:** 32 GB für optimale Performance bei großen Datenmengen
- **Speicherplatz:** 200 GB SSD-Speicher für bessere I/O-Performance
- **Netzwerk:** Dedizierte Netzwerkverbindung mit niedriger Latenz

### Software-Anforderungen

**Betriebssystem:**
- Windows Server 2016 oder höher (empfohlen)
- Windows 10/11 Professional oder Enterprise
- Linux (Ubuntu 20.04 LTS oder höher, CentOS 8+)

**Python-Umgebung:**
- Python 3.8 oder höher (Python 3.10 empfohlen)
- pip Package Manager
- Virtual Environment Support

**Netzwerk-Zugriff:**
- Zugriff auf SharePoint 2019 Server über HTTP/HTTPS
- Zugriff auf SQL Server (falls direkte Datenbankabfragen erforderlich)
- DNS-Auflösung für SharePoint-Server
- Firewall-Regeln für Ports 80, 443, und ggf. 1433 (SQL Server)

### SharePoint 2019 Voraussetzungen

**SharePoint-Version:**
- SharePoint Server 2019 mit aktuellen Updates
- SharePoint Foundation 2019 (eingeschränkte Funktionalität)

**Aktivierte Features:**
- REST API Services
- Search Service Application
- User Profile Service (für erweiterte Metadaten)

**Authentifizierung:**
- Windows Authentication (NTLM/Kerberos)
- Forms-Based Authentication (optional)
- Claims-Based Authentication (empfohlen)

---

## Zugangsdaten und Berechtigungen

### Erforderliche Anmeldedaten

Für die erfolgreiche Konfiguration von DocRecon AI benötigen Sie folgende Zugangsdaten und Informationen:

#### 1. SharePoint Server-Informationen

**Server-URL:**
```
https://sharepoint.ihrefirma.de
```
*Ersetzen Sie "ihrefirma.de" durch Ihre tatsächliche Domain*

**Alternative Formate:**
- `http://sharepoint-server:port` (für HTTP-Verbindungen)
- `https://sharepoint.domain.local` (für interne Domains)

#### 2. Authentifizierungsdaten

**Service Account (Empfohlen):**
```
Benutzername: DOMAIN\svc-docrecon
Passwort: [Ihr sicheres Service-Account-Passwort]
Domain: IHREDOMAIN
```

**Persönlicher Account (Entwicklung/Test):**
```
Benutzername: DOMAIN\ihr.benutzername
Passwort: [Ihr Passwort]
Domain: IHREDOMAIN
```

#### 3. Site Collections und Document Libraries

**Site Collections (Beispiele):**
```
/sites/dokumente
/sites/projekte
/sites/teams
/sites/archiv
/sites/qualitaet
```

**Document Libraries (Beispiele):**
```
Shared Documents
Documents
Dokumente
Project Files
Archive
Templates
Policies
```

### Berechtigungen konfigurieren

#### SharePoint-Berechtigungen

Der verwendete Account benötigt mindestens folgende Berechtigungen:

**Site Collection Level:**
- **Read:** Vollzugriff auf alle Site Collections
- **View Only:** Minimale Berechtigung für reine Lesezugriffe

**Web Application Level:**
- **Full Read:** Zugriff auf alle Webs in der Web Application
- **Restricted Read:** Eingeschränkter Zugriff (falls Sicherheitsrichtlinien dies erfordern)

**Document Library Level:**
- **Read:** Zugriff auf alle Dokumente
- **View Items:** Berechtigung zum Anzeigen von Listenelementen
- **Open Items:** Berechtigung zum Öffnen von Dokumenten

#### Windows-Berechtigungen

**Lokale Berechtigungen:**
- **Log on as a service:** Für Service-Accounts
- **Access this computer from the network:** Für Netzwerkzugriff
- **Read:** Auf SharePoint-Installationsverzeichnisse (falls lokaler Zugriff erforderlich)

**Active Directory-Berechtigungen:**
- Mitgliedschaft in entsprechenden SharePoint-Gruppen
- Kein Ablaufdatum für Service-Accounts
- Starke Passwort-Richtlinien befolgen

### Umgebungsvariablen einrichten

Für maximale Sicherheit sollten alle sensiblen Daten als Umgebungsvariablen gespeichert werden:

**Windows PowerShell:**
```powershell
# SharePoint-Konfiguration
[Environment]::SetEnvironmentVariable("SHAREPOINT_SERVER_URL", "https://sharepoint.ihrefirma.de", "User")
[Environment]::SetEnvironmentVariable("SHAREPOINT_USERNAME", "DOMAIN\svc-docrecon", "User")
[Environment]::SetEnvironmentVariable("SHAREPOINT_PASSWORD", "IhrSicheresPasswort", "User")
[Environment]::SetEnvironmentVariable("SHAREPOINT_DOMAIN", "IHREDOMAIN", "User")

# SMB/Netzlaufwerk-Konfiguration
[Environment]::SetEnvironmentVariable("SMB_USERNAME", "DOMAIN\svc-docrecon", "User")
[Environment]::SetEnvironmentVariable("SMB_PASSWORD", "IhrSicheresPasswort", "User")
[Environment]::SetEnvironmentVariable("SMB_DOMAIN", "IHREDOMAIN", "User")
```

**Linux/macOS Bash:**
```bash
# SharePoint-Konfiguration
export SHAREPOINT_SERVER_URL="https://sharepoint.ihrefirma.de"
export SHAREPOINT_USERNAME="DOMAIN\\svc-docrecon"
export SHAREPOINT_PASSWORD="IhrSicheresPasswort"
export SHAREPOINT_DOMAIN="IHREDOMAIN"

# SMB/Netzlaufwerk-Konfiguration
export SMB_USERNAME="DOMAIN\\svc-docrecon"
export SMB_PASSWORD="IhrSicheresPasswort"
export SMB_DOMAIN="IHREDOMAIN"

# Persistent machen (in ~/.bashrc oder ~/.profile)
echo 'export SHAREPOINT_SERVER_URL="https://sharepoint.ihrefirma.de"' >> ~/.bashrc
echo 'export SHAREPOINT_USERNAME="DOMAIN\\svc-docrecon"' >> ~/.bashrc
# ... weitere Variablen
```

---

## Installation und Konfiguration

### Schritt 1: Python-Umgebung vorbereiten

#### Virtual Environment erstellen

```bash
# Virtual Environment erstellen
python -m venv docrecon_env

# Aktivieren (Windows)
docrecon_env\Scripts\activate

# Aktivieren (Linux/macOS)
source docrecon_env/bin/activate
```

#### DocRecon AI installieren

```bash
# Aus GitHub Repository installieren
git clone https://github.com/Polar1337/docrecon-ai.git
cd docrecon-ai

# Abhängigkeiten installieren
pip install -r requirements.txt

# DocRecon AI installieren
pip install -e .
```

#### Zusätzliche Abhängigkeiten für SharePoint

```bash
# SharePoint-spezifische Pakete
pip install requests-ntlm

# Windows-spezifische Pakete (nur auf Windows)
pip install pywin32

# Optionale NLP-Erweiterungen
pip install spacy
python -m spacy download de_core_news_sm  # Deutsches Sprachmodell
```

### Schritt 2: Konfigurationsdatei anpassen

#### Basis-Konfiguration kopieren

```bash
# Konfigurationsvorlage kopieren
cp config/sharepoint_onprem.yaml config/ihre_umgebung.yaml
```

#### Konfigurationsdatei bearbeiten

Öffnen Sie `config/ihre_umgebung.yaml` und passen Sie folgende Bereiche an:

**SharePoint-Server-Konfiguration:**
```yaml
crawler:
  sharepoint_onprem:
    enabled: true
    server_url: "${SHAREPOINT_SERVER_URL}"
    authentication_method: "ntlm"
    username: "${SHAREPOINT_USERNAME}"
    password: "${SHAREPOINT_PASSWORD}"
    domain: "${SHAREPOINT_DOMAIN}"
```

**Site Collections anpassen:**
```yaml
    site_collections:
      - "/sites/dokumente"        # Ihre Haupt-Dokumentensammlung
      - "/sites/projekte"         # Projektdokumente
      - "/sites/teams"            # Team-Sites
      - "/sites/archiv"           # Archivierte Dokumente
      - "/sites/qualitaet"        # QM-Dokumente
      - "/sites/personal"         # Personal-Sites (optional)
```

**Document Libraries anpassen:**
```yaml
    document_libraries:
      - "Shared Documents"        # Standard-Bibliothek
      - "Documents"               # Alternative Bezeichnung
      - "Dokumente"               # Deutsche Bezeichnung
      - "Project Files"           # Projektdateien
      - "Archive"                 # Archiv
      - "Templates"               # Vorlagen
      - "Policies"                # Richtlinien
      - "Procedures"              # Verfahren
```

### Schritt 3: Verbindung testen

#### Konfiguration validieren

```bash
# Konfiguration testen
docrecon_ai validate-config --config config/ihre_umgebung.yaml
```

#### SharePoint-Verbindung testen

```bash
# Verbindungstest durchführen
docrecon_ai test-connection --config config/ihre_umgebung.yaml --crawler sharepoint_onprem
```

**Erwartete Ausgabe bei erfolgreicher Verbindung:**
```
INFO - SharePoint On-Premise crawler initialized
INFO - Successfully connected to SharePoint site: Ihre Firmen-SharePoint
INFO - sharepoint_onprem connection test: PASS
```

**Bei Verbindungsproblemen:**
```
ERROR - Authentication failed for URL: https://sharepoint.ihrefirma.de/_api/web
ERROR - sharepoint_onprem connection test: FAIL
```

---

## SharePoint 2019 Konfiguration

### REST API aktivieren und konfigurieren

SharePoint 2019 On-Premise erfordert spezielle Konfigurationen für den REST API-Zugriff:

#### Central Administration Einstellungen

**Web Application Settings:**
1. Öffnen Sie die SharePoint Central Administration
2. Navigieren Sie zu "Application Management" → "Manage web applications"
3. Wählen Sie Ihre Web Application aus
4. Klicken Sie auf "Authentication Providers"
5. Stellen Sie sicher, dass "Enable client integration" aktiviert ist

**Service Applications:**
1. Überprüfen Sie, dass folgende Service Applications laufen:
   - Search Service Application
   - User Profile Service Application
   - Managed Metadata Service

#### IIS-Konfiguration

**Authentication Settings:**
```xml
<!-- web.config Anpassungen für REST API -->
<system.webServer>
  <security>
    <authentication>
      <windowsAuthentication enabled="true" />
      <anonymousAuthentication enabled="false" />
    </authentication>
  </security>
</system.webServer>
```

**CORS-Einstellungen (falls erforderlich):**
```xml
<system.webServer>
  <httpProtocol>
    <customHeaders>
      <add name="Access-Control-Allow-Origin" value="*" />
      <add name="Access-Control-Allow-Methods" value="GET, POST, OPTIONS" />
      <add name="Access-Control-Allow-Headers" value="Content-Type, Authorization" />
    </customHeaders>
  </httpProtocol>
</system.webServer>
```

### PowerShell-Konfiguration

#### SharePoint Management Shell

```powershell
# SharePoint PowerShell Snap-in laden
Add-PSSnapin Microsoft.SharePoint.PowerShell -ErrorAction SilentlyContinue

# Web Application für REST API konfigurieren
$webApp = Get-SPWebApplication "https://sharepoint.ihrefirma.de"
$webApp.ClientCallableSettings.MaxObjectPaths = 1000
$webApp.Update()

# Site Collection Features aktivieren
$site = Get-SPSite "https://sharepoint.ihrefirma.de/sites/dokumente"
Enable-SPFeature -Identity "SharePoint Server Publishing Infrastructure" -Url $site.Url
```

#### Berechtigungen über PowerShell setzen

```powershell
# Service Account Berechtigungen setzen
$web = Get-SPWeb "https://sharepoint.ihrefirma.de/sites/dokumente"
$user = $web.EnsureUser("DOMAIN\svc-docrecon")
$web.RoleAssignments.Add($user, $web.RoleDefinitions["Read"])
$web.Update()
```

### Erweiterte SharePoint-Konfiguration

#### Custom Permission Levels

Für DocRecon AI können Sie einen speziellen Permission Level erstellen:

```powershell
# Custom Permission Level für DocRecon AI
$web = Get-SPWeb "https://sharepoint.ihrefirma.de"
$roleDefinition = $web.RoleDefinitions.Add("DocRecon Reader", "Read access for DocRecon AI", 0)

# Spezifische Berechtigungen hinzufügen
$roleDefinition.BasePermissions = [Microsoft.SharePoint.SPBasePermissions]::ViewListItems -bor
                                  [Microsoft.SharePoint.SPBasePermissions]::OpenItems -bor
                                  [Microsoft.SharePoint.SPBasePermissions]::ViewVersions -bor
                                  [Microsoft.SharePoint.SPBasePermissions]::ViewFormPages -bor
                                  [Microsoft.SharePoint.SPBasePermissions]::Open -bor
                                  [Microsoft.SharePoint.SPBasePermissions]::ViewPages -bor
                                  [Microsoft.SharePoint.SPBasePermissions]::BrowseDirectories

$roleDefinition.Update()
$web.Update()
```

#### Throttling-Einstellungen anpassen

```powershell
# Request Throttling für API-Zugriffe anpassen
$webApp = Get-SPWebApplication "https://sharepoint.ihrefirma.de"
$webApp.MaxItemsPerThrottledOperation = 5000
$webApp.MaxItemsPerThrottledOperationOverride = 20000
$webApp.Update()
```

---

## OneNote Integration

### OneNote-Zugriffsmethoden

DocRecon AI unterstützt drei verschiedene Methoden für den OneNote-Zugriff:

#### 1. SharePoint-basierter Zugriff (Empfohlen)

Wenn OneNote-Notizbücher in SharePoint gespeichert sind:

```yaml
crawler:
  onenote:
    enabled: true
    access_method: "sharepoint"
    include_sections: true
    include_pages: true
    extract_text: true
```

**Vorteile:**
- Nutzt bestehende SharePoint-Authentifizierung
- Keine zusätzliche Software erforderlich
- Zentrale Verwaltung über SharePoint

**Konfiguration:**
OneNote-Dateien werden automatisch über den SharePoint-Crawler erfasst, wenn sie in Document Libraries gespeichert sind.

#### 2. Lokaler COM-Interface-Zugriff (Windows)

Für lokal installierte OneNote-Anwendungen:

```yaml
crawler:
  onenote:
    enabled: true
    access_method: "local_com"
    include_sections: true
    include_pages: true
    extract_text: true
```

**Voraussetzungen:**
- Microsoft OneNote 2016 oder höher installiert
- Windows-Betriebssystem
- pywin32 Python-Paket installiert

**Installation der Abhängigkeiten:**
```bash
pip install pywin32
```

#### 3. Lokaler Dateizugriff

Für OneNote-Dateien im Dateisystem:

```yaml
crawler:
  onenote:
    enabled: true
    access_method: "local_files"
    include_sections: true
    include_pages: true
    extract_text: true
```

### OneNote-Dateiformate

DocRecon AI unterstützt folgende OneNote-Dateiformate:

**Unterstützte Formate:**
- `.one` - OneNote Section Files
- `.onetoc2` - OneNote Table of Contents
- `.onepkg` - OneNote Package Files

**Konfiguration der Dateierweiterungen:**
```yaml
crawler:
  file_extensions:
    - .one
    - .onetoc2
    - .onepkg
```

### OneNote-Textextraktion

#### Erweiterte Textextraktion konfigurieren

```yaml
nlp:
  onenote_extraction:
    extract_handwriting: false    # OCR für handschriftliche Notizen
    extract_drawings: false       # Bildinhalte extrahieren
    extract_tables: true          # Tabelleninhalte extrahieren
    extract_links: true           # Hyperlinks extrahieren
    preserve_formatting: false    # Formatierung beibehalten
```

#### OneNote-spezifische Metadaten

DocRecon AI extrahiert folgende Metadaten aus OneNote-Dokumenten:

- **Notebook-Name:** Name des Notizbuchs
- **Section-Name:** Name der Sektion
- **Page-Title:** Titel der Seite
- **Creation-Date:** Erstellungsdatum
- **Last-Modified:** Letzte Änderung
- **Author:** Ersteller (falls verfügbar)
- **Tags:** OneNote-Tags

---

## Sicherheitseinstellungen

### Authentifizierung absichern

#### Service Account Best Practices

**Service Account Konfiguration:**
```powershell
# Service Account erstellen
New-ADUser -Name "svc-docrecon" -UserPrincipalName "svc-docrecon@ihredomain.de" -AccountPassword (ConvertTo-SecureString "KomplexesPasswort123!" -AsPlainText -Force) -Enabled $true

# Passwort läuft nie ab
Set-ADUser -Identity "svc-docrecon" -PasswordNeverExpires $true

# Konto kann nicht interaktiv anmelden
Set-ADUser -Identity "svc-docrecon" -CannotChangePassword $true
```

**Minimale Berechtigungen:**
- Nur Lesezugriff auf SharePoint
- Keine lokalen Anmelderechte
- Keine Administratorrechte
- Regelmäßige Passwort-Rotation

#### Netzwerk-Sicherheit

**Firewall-Regeln:**
```bash
# Windows Firewall (PowerShell als Administrator)
New-NetFirewallRule -DisplayName "DocRecon AI SharePoint Access" -Direction Outbound -Protocol TCP -RemotePort 443 -Action Allow
New-NetFirewallRule -DisplayName "DocRecon AI SharePoint HTTP" -Direction Outbound -Protocol TCP -RemotePort 80 -Action Allow
```

**SSL/TLS-Konfiguration:**
```yaml
security:
  ssl_verification: true
  min_tls_version: "1.2"
  cipher_suites:
    - "ECDHE-RSA-AES256-GCM-SHA384"
    - "ECDHE-RSA-AES128-GCM-SHA256"
```

### Datenverarbeitung absichern

#### Lokale Verarbeitung

```yaml
security:
  local_processing_only: true
  no_cloud_services: true
  encrypt_temp_files: true
  secure_delete_temp_files: true
```

#### Logging-Sicherheit

```yaml
logging:
  mask_credentials: true
  mask_personal_data: true
  log_retention_days: 30
  secure_log_storage: true
```

### Compliance-Einstellungen

#### DSGVO-Konformität

```yaml
compliance:
  gdpr_mode: true
  anonymize_personal_data: true
  data_retention_policy: "30_days"
  audit_logging: true
```

#### Audit-Trail

```yaml
audit:
  log_all_access: true
  log_file_access: true
  log_user_actions: true
  export_audit_logs: true
```

---

## Erste Analyse durchführen

### Schritt 1: Konfiguration final prüfen

```bash
# Vollständige Konfigurationsprüfung
docrecon_ai validate-config --config config/ihre_umgebung.yaml --verbose

# Alle Verbindungen testen
docrecon_ai test-connections --config config/ihre_umgebung.yaml
```

### Schritt 2: Testlauf mit begrenztem Umfang

```bash
# Kleine Testanalyse durchführen
docrecon_ai analyze \
  --config config/ihre_umgebung.yaml \
  --sharepoint-site "/sites/dokumente" \
  --max-files 100 \
  --output ./test_results \
  --log-level DEBUG
```

### Schritt 3: Vollständige Analyse

```bash
# Vollständige Analyse aller konfigurierten Quellen
docrecon_ai analyze \
  --config config/ihre_umgebung.yaml \
  --output ./full_analysis_$(date +%Y%m%d) \
  --include-nlp \
  --parallel-workers 4
```

### Schritt 4: Ergebnisse prüfen

```bash
# Dashboard starten
docrecon_ai dashboard \
  --results ./full_analysis_*/analysis_results.json \
  --port 8501

# Berichte generieren
docrecon_ai report \
  ./full_analysis_*/analysis_results.json \
  --output ./reports \
  --formats html csv json \
  --title "SharePoint Dokumentenanalyse $(date +%Y-%m-%d)"
```

---

## Fehlerbehebung

### Häufige Authentifizierungsprobleme

#### NTLM-Authentifizierung schlägt fehl

**Problem:** `401 Unauthorized` Fehler bei SharePoint-Zugriff

**Lösung:**
```bash
# Kerberos-Konfiguration prüfen
klist

# NTLM-Hash prüfen
nltest /sc_query:IHREDOMAIN

# Alternative: Basic Authentication testen
```

**Konfiguration anpassen:**
```yaml
crawler:
  sharepoint_onprem:
    authentication_method: "basic"  # Fallback auf Basic Auth
    timeout_seconds: 60             # Timeout erhöhen
```

#### Domain-Probleme

**Problem:** Domain kann nicht aufgelöst werden

**Lösung:**
```bash
# DNS-Auflösung testen
nslookup sharepoint.ihrefirma.de

# Hosts-Datei prüfen (Windows: C:\Windows\System32\drivers\etc\hosts)
echo "192.168.1.100 sharepoint.ihrefirma.de" >> /etc/hosts
```

### SharePoint-spezifische Probleme

#### REST API nicht verfügbar

**Problem:** `404 Not Found` für `/_api/web` Endpunkt

**Lösung:**
```powershell
# SharePoint Features prüfen
Get-SPFeature -Site "https://sharepoint.ihrefirma.de" | Where-Object {$_.DisplayName -like "*Publishing*"}

# REST API Feature aktivieren
Enable-SPFeature -Identity "SharePoint Server Publishing Infrastructure" -Url "https://sharepoint.ihrefirma.de"
```

#### Throttling-Probleme

**Problem:** `429 Too Many Requests` oder langsame Antworten

**Lösung:**
```yaml
crawler:
  sharepoint_onprem:
    batch_size: 50              # Kleinere Batches
    retry_attempts: 5           # Mehr Wiederholungen
    timeout_seconds: 120        # Längere Timeouts
```

```powershell
# SharePoint Throttling anpassen
$webApp = Get-SPWebApplication "https://sharepoint.ihrefirma.de"
$webApp.MaxItemsPerThrottledOperation = 2000
$webApp.Update()
```

### OneNote-spezifische Probleme

#### COM-Interface nicht verfügbar

**Problem:** OneNote COM-Interface kann nicht initialisiert werden

**Lösung:**
```bash
# pywin32 neu installieren
pip uninstall pywin32
pip install pywin32
python Scripts/pywin32_postinstall.py -install

# OneNote-Installation prüfen
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Office\16.0\OneNote"
```

#### OneNote-Dateien nicht gefunden

**Problem:** OneNote-Dateien werden nicht erkannt

**Lösung:**
```yaml
crawler:
  file_extensions:
    - .one
    - .onetoc2
    - .onepkg
  include_hidden_files: true    # Versteckte OneNote-Dateien einschließen
```

### Performance-Probleme

#### Langsame Analyse

**Problem:** Analyse dauert sehr lange

**Optimierungen:**
```yaml
performance:
  max_workers: 8                # Mehr parallele Worker
  chunk_size: 1000             # Größere Chunks
  memory_limit_mb: 8192        # Mehr Speicher
  enable_caching: true         # Caching aktivieren

crawler:
  sharepoint_onprem:
    batch_size: 200            # Größere API-Batches
    parallel_connections: 4     # Parallele Verbindungen
```

#### Speicher-Probleme

**Problem:** Out of Memory Fehler

**Lösung:**
```yaml
performance:
  memory_limit_mb: 4096        # Speicherlimit setzen
  chunk_size: 100              # Kleinere Chunks
  process_files_individually: true  # Einzelverarbeitung

crawler:
  max_file_size_mb: 50         # Große Dateien ausschließen
```

---

## Best Practices

### Deployment-Strategien

#### Phasenweise Einführung

**Phase 1: Pilotprojekt**
- Einzelne Site Collection analysieren
- Kleine Benutzergruppe einbeziehen
- Konfiguration optimieren

**Phase 2: Abteilungsweise Ausrollung**
- Schrittweise Erweiterung auf weitere Site Collections
- Feedback sammeln und Anpassungen vornehmen
- Performance-Monitoring

**Phase 3: Vollständige Implementierung**
- Alle konfigurierten Quellen einbeziehen
- Automatisierte Analysen einrichten
- Regelmäßige Berichte etablieren

#### Automatisierung

**Scheduled Tasks (Windows):**
```powershell
# Tägliche Analyse um 2:00 Uhr
$action = New-ScheduledTaskAction -Execute "python" -Argument "-m docrecon_ai analyze --config config/ihre_umgebung.yaml --output ./daily_analysis"
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
Register-ScheduledTask -TaskName "DocRecon Daily Analysis" -Action $action -Trigger $trigger
```

**Cron Jobs (Linux):**
```bash
# Crontab-Eintrag für tägliche Analyse
0 2 * * * /path/to/docrecon_env/bin/python -m docrecon_ai analyze --config /path/to/config/ihre_umgebung.yaml --output /path/to/daily_analysis
```

### Monitoring und Wartung

#### Log-Monitoring

```yaml
logging:
  level: "INFO"
  file: "/var/log/docrecon_ai/application.log"
  max_size_mb: 100
  backup_count: 10
  
monitoring:
  enable_metrics: true
  metrics_endpoint: "http://localhost:9090/metrics"
  alert_on_errors: true
  alert_email: "admin@ihrefirma.de"
```

#### Performance-Monitoring

```bash
# Performance-Metriken sammeln
docrecon_ai analyze \
  --config config/ihre_umgebung.yaml \
  --output ./analysis \
  --enable-profiling \
  --metrics-output ./metrics.json
```

### Sicherheits-Best-Practices

#### Regelmäßige Sicherheitsupdates

```bash
# Abhängigkeiten aktualisieren
pip list --outdated
pip install --upgrade -r requirements.txt

# Sicherheitsscan durchführen
pip install safety
safety check
```

#### Credential-Rotation

```powershell
# Service Account Passwort ändern (alle 90 Tage)
$newPassword = ConvertTo-SecureString "NeuesKomplexesPasswort456!" -AsPlainText -Force
Set-ADAccountPassword -Identity "svc-docrecon" -NewPassword $newPassword

# Umgebungsvariablen aktualisieren
[Environment]::SetEnvironmentVariable("SHAREPOINT_PASSWORD", "NeuesKomplexesPasswort456!", "User")
```

### Backup und Disaster Recovery

#### Konfiguration sichern

```bash
# Konfigurationsdateien sichern
tar -czf docrecon_config_backup_$(date +%Y%m%d).tar.gz config/

# Analyseergebnisse archivieren
tar -czf analysis_results_$(date +%Y%m%d).tar.gz ./analysis_*
```

#### Wiederherstellung

```bash
# Konfiguration wiederherstellen
tar -xzf docrecon_config_backup_YYYYMMDD.tar.gz

# Umgebung neu aufsetzen
python -m venv docrecon_env_restore
source docrecon_env_restore/bin/activate
pip install -r requirements.txt
pip install -e .
```

---

## Anhang

### Konfigurationsreferenz

Eine vollständige Referenz aller Konfigurationsoptionen finden Sie in der Datei `config/sharepoint_onprem.yaml`.

### API-Referenz

Detaillierte Informationen zur SharePoint 2019 REST API finden Sie in der Microsoft-Dokumentation.

### Support und Community

- **GitHub Issues:** https://github.com/Polar1337/docrecon-ai/issues
- **Dokumentation:** https://github.com/Polar1337/docrecon-ai/docs
- **Community Forum:** [Link zur Community]

### Lizenz

DocRecon AI ist unter der MIT-Lizenz veröffentlicht. Weitere Informationen finden Sie in der LICENSE-Datei.

---

*Dieser Guide wird regelmäßig aktualisiert. Für die neuesten Informationen besuchen Sie das GitHub-Repository.*

