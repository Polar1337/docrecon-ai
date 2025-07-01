# 🔐 DocRecon AI - Zugangsdaten Checkliste für SharePoint 2019 On-Premise

## ✅ Was Sie von mir benötigen

### 1. SharePoint Server-Informationen

**Server-URL:**
```
https://ihr-sharepoint-server.domain.de
```
*Beispiel: https://sharepoint.firma.de oder http://sp2019:8080*

### 2. Anmeldedaten

**Service Account (empfohlen):**
```
Benutzername: DOMAIN\service-account-name
Passwort: [Ihr Service Account Passwort]
Domain: IHRE_DOMAIN
```

**Oder Ihr persönlicher Account:**
```
Benutzername: DOMAIN\ihr.benutzername
Passwort: [Ihr Passwort]
Domain: IHRE_DOMAIN
```

### 3. Site Collections

**Welche Site Collections sollen durchsucht werden?**
```
/sites/dokumente
/sites/projekte
/sites/teams
/sites/archiv
[Weitere Site Collections...]
```

### 4. Document Libraries

**Welche Document Libraries in den Sites?**
```
Shared Documents
Documents
Dokumente
Project Files
Archive
[Weitere Libraries...]
```

### 5. Netzlaufwerke (optional)

**SMB/CIFS Shares:**
```
\\fileserver01\dokumente
\\nas01\projekte
[Weitere Netzlaufwerke...]
```

**Anmeldedaten für Netzlaufwerke:**
```
Benutzername: DOMAIN\username
Passwort: [Passwort]
Domain: DOMAIN
```

## 🛠️ Wo Sie diese Werte eintragen müssen

### Umgebungsvariablen setzen (empfohlen)

**Windows PowerShell:**
```powershell
[Environment]::SetEnvironmentVariable("SHAREPOINT_SERVER_URL", "https://ihr-server.domain.de", "User")
[Environment]::SetEnvironmentVariable("SHAREPOINT_USERNAME", "DOMAIN\username", "User")
[Environment]::SetEnvironmentVariable("SHAREPOINT_PASSWORD", "IhrPasswort", "User")
[Environment]::SetEnvironmentVariable("SHAREPOINT_DOMAIN", "DOMAIN", "User")
```

**Linux/macOS:**
```bash
export SHAREPOINT_SERVER_URL="https://ihr-server.domain.de"
export SHAREPOINT_USERNAME="DOMAIN\\username"
export SHAREPOINT_PASSWORD="IhrPasswort"
export SHAREPOINT_DOMAIN="DOMAIN"
```

### Konfigurationsdatei anpassen

**Datei:** `config/sharepoint_onprem.yaml`

**Bereiche zum Anpassen:**
1. **server_url** - Ihre SharePoint-URL
2. **site_collections** - Ihre Site Collections
3. **document_libraries** - Ihre Document Libraries
4. **smb shares** - Ihre Netzlaufwerke

## 🚀 Schnellstart nach Konfiguration

```bash
# 1. Verbindung testen
docrecon_ai test-connection --config config/sharepoint_onprem.yaml

# 2. Erste Analyse starten
docrecon_ai analyze \
  --config config/sharepoint_onprem.yaml \
  --output ./erste_analyse \
  --max-files 100

# 3. Ergebnisse anzeigen
docrecon_ai dashboard --results ./erste_analyse/analysis_results.json
```

## 📞 Bei Problemen

**Häufige Fehler:**
- **401 Unauthorized:** Benutzername/Passwort falsch
- **404 Not Found:** SharePoint-URL falsch oder REST API nicht aktiviert
- **Connection timeout:** Netzwerkproblem oder Firewall

**Hilfe erhalten:**
- Detaillierte Anleitung: `docs/sharepoint_onprem_deployment_guide.md`
- GitHub Issues: https://github.com/Polar1337/docrecon-ai/issues

## 🔒 Sicherheitshinweise

- **Niemals** Passwörter in Konfigurationsdateien speichern
- **Immer** Umgebungsvariablen verwenden
- **Service Account** mit minimalen Berechtigungen erstellen
- **Regelmäßig** Passwörter ändern

