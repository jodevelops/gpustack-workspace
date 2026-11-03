# GPUStack Arbeitsraum

Ein persönlicher KI-Arbeitsraum für Gespräche, eigene Quellen und Sammlungsarbeit.
Die deutsche Oberfläche läuft lokal im Browser; die Modelle werden über deinen
GPUStack- oder OpenAI-kompatiblen Endpunkt angesprochen.

**Version 0.1.10 · Proof of Concept · Stand 3. November 2026**

## 1. Auf einen Blick

| Bereich | Was du damit machen kannst |
|---|---|
| **Chats & Projekte** | Gespräche, Projektnotizen und Verlauf zusammenhalten; Antworten exportieren. |
| **Eigene Quellen** | Dokumente hochladen, Bilder/PDFs ansehen und ausgewählte Quellen im Chat befragen. |
| **Prompts & Skills** | Arbeitsanweisungen wiederverwenden und Modelle sowie Antwortbudgets einstellen. |
| **Recherche** | Fachquellen durchsuchen; allgemeine Websuche optional über SearXNG oder Brave ergänzen. |
| **Audio & Transkripte** | Aufnehmen oder hochladen, transkribieren, Text bearbeiten und Ergebnisse exportieren. |
| **Routinen & Datenlabor** | Wiederkehrende Modellaufträge planen; Tabellen und Office-Ausgaben optional im Docker-Runner berechnen. |

**Ablage lokal, Modellanfragen an deinen Endpunkt.** Projekte, Chats und Dateien
bleiben auf deinem Rechner. Ausgewählte Inhalte gehen bei einer Modellanfrage
an den von dir eingerichteten Dienst.

[Installation](#2-lokal-starten) · [GPUStack verbinden](#3-gpustack-verbinden) ·
[Erster Arbeitsablauf](#4-der-erste-vollständige-arbeitsablauf)

## 2. Lokal starten

Das Repository enthält das vollständige Installationspaket einschließlich
`start.py`, `start.cmd`, grafischem Starter `desktop.pyw`, Abhängigkeitslisten, Beispieldateien und optionalem
Docker-Bauplan. Oberfläche und Ablage benötigen keinen Cloud-Dienst.
Eure GPUStack-URL und ein API-Schlüssel werden erst vor Ort eingetragen.
Die mitgelieferten Beispieldaten sind frei erfunden.

Das vollständige Paket über **Code → Download ZIP** aus
[jodevelops/gpustack-workspace](https://github.com/jodevelops/gpustack-workspace)
herunterladen und entpacken. Für Änderungen siehe [Änderungsprotokoll](CHANGELOG.md).

Voraussetzungen: Python 3.11 oder neuer, empfohlen 3.12/3.13, und ein aktueller
Browser. Für die Grundanwendung werden weder Node.js noch Docker oder
Administratorrechte benötigt. Der Arbeitsraum ist für ein Betriebssystemkonto
auf einem persönlichen Rechner vorgesehen.

### Windows: per Doppelklick starten

1. Das vollständige Repository-ZIP herunterladen und **vollständig entpacken**.
   Den Programmordner an einem beschreibbaren, dauerhaften Ort behalten.
2. **`start.cmd` doppelklicken.** Ein kleines Startfenster öffnet sich.
3. Falls Pakete fehlen, einmal **Einrichten und starten** anklicken. Die
   Einrichtung lädt die benötigten Python-Pakete; Fortschritt und Fehler sind
   im Fenster sichtbar. Es müssen keine Terminalbefehle eingegeben werden.
4. Sobald der Dienst bereit ist, öffnet sich der Arbeitsraum. Unter Windows
   wird ein eigenes Edge-/Chrome-App-Fenster verwendet, wenn der Browser an
   einem üblichen Installationsort gefunden wird; andernfalls der Standardbrowser.
5. Bei Bedarf im Startfenster **Desktop-Verknüpfung** anklicken. Danach lässt
   sich der Arbeitsraum direkt über das Desktop-Symbol öffnen.

Bei weiteren Starts entfallen die Einrichtungsschritte. Das Programm läuft im
Hintergrund ohne dauerhaft offenes Konsolenfenster; beim Aufruf von `start.cmd`
kann kurz ein Konsolenfenster erscheinen. Das Startfenster bleibt für Status
und **Beenden** verfügbar. Dieses Fenster zu schließen beendet den selbst
gestarteten lokalen Dienst. Ein weiterer Aufruf öffnet eine bereits laufende
Instanz mit demselben Datenordner erneut.

Voraussetzung bleibt ein vorhandenes **Python 3.11 oder neuer mit Tcl/Tk**;
die reguläre Windows-Installation einschließlich Microsoft-Store-Python bringt
Tcl/Tk üblicherweise mit. In einer virtuellen Umgebung werden Pakete dort
installiert, sonst für das aktuelle Benutzerkonto. Institutionell gesperrte
Paketinstallationen müssen weiterhin von der IT bereitgestellt werden.

`desktop.pyw` kann bei eingerichteter Python-Dateizuordnung auch direkt
gedoppelklickt werden. Für Fehlerdiagnosen gibt es **`start-debug.cmd`**, das
den bisherigen Konsolenstart beibehält. Die folgenden PowerShell-Wege sind
Alternativen zum grafischen Start.

### Windows / PowerShell: mit vorhandenem Python

Zuerst das **vollständige Repository-ZIP** über **Code → Download ZIP**
herunterladen und in einen neuen Ordner entpacken. Das ältere
`GPUStack-Arbeitsraum-Update-v0.1.8` ist ein Ergänzungspaket und enthält weder
`start.py` noch `requirements.txt`. Änderungen auf GitHub ergänzen einen schon
entpackten Downloadordner nicht automatisch.

PowerShell in dem entpackten Ordner öffnen, in dem `start.py`, `start.cmd`
und `requirements.txt` direkt liegen. Je nach gewähltem Entpackziel kann
`gpustack-workspace-main` eine Ordnerebene tiefer liegen. Zuerst prüfen:

```powershell
Get-Item -LiteralPath '.\start.py', '.\requirements.txt' | Select-Object Name
python --version
```

Wenn beide Dateien angezeigt werden und Python mindestens Version 3.11 hat,
die folgenden Befehle **einzeln** ausführen und bei einem Fehler anhalten:

```powershell
python -m pip install --user -r .\requirements.txt
python .\start.py --check
python .\start.py
```

Wenn die IT die benötigten Pakete bereits für diesen Interpreter bereitstellt,
entfällt der Installationsbefehl. Ist die Benutzerinstallation gesperrt, die
Abhängigkeitsliste der IT geben. Für diesen Startweg wird keine virtuelle
Umgebung angelegt. Der zusätzliche Python-Launcher `py` wird nicht benötigt;
entscheidend ist der bereits funktionierende Aufruf `python`.

Nach erfolgreicher Einrichtung genügt auch ein Doppelklick auf `start.cmd`.
Der Starter verwendet zuerst `.venv\Scripts\python.exe`, sonst `python` und
danach `py -3`. Fehlende Pakete werden erst nach Klick auf **Einrichten und
starten** installiert.

### Windows / PowerShell: optional mit virtueller Umgebung

Wenn virtuelle Umgebungen auf dem Rechner erlaubt sind, im selben vollständigen
Programmordner stattdessen diese Variante verwenden. Jeden Befehl erst nach
erfolgreichem Abschluss des vorherigen ausführen:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe .\start.py --check
.\.venv\Scripts\python.exe .\start.py
```

Schlägt das Anlegen fehl, existiert auch `.venv\Scripts\python.exe` nicht.
PowerShell benötigt bei diesem relativen Programmpfad das führende `.\`.
Die Umgebung muss für diese Aufrufe nicht aktiviert werden.

Der Browser öffnet `http://127.0.0.1:8765` erst, wenn der lokale Server erfolgreich
gestartet ist. Im Terminal erscheint **Arbeitsraum bereit**.
Beim Start über das Terminal muss dessen Fenster während der Nutzung geöffnet
bleiben. Zum Beenden **Strg+C** drücken. Beim grafischen Start stattdessen im
Startfenster **Beenden** wählen. Ein laufender Chat wird beim Beenden unterbrochen.
Die Installation lädt Python-Pakete aus dem eingestellten Paketindex. In einem
abgeschotteten Netz kann die IT die Pakete über einen internen Mirror oder ein
passendes Wheel-Paket bereitstellen.

### Linux / macOS

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python start.py
```

Der Starter wählt den Datenordner in dieser Reihenfolge:

1. Explizite Angabe mit `--data-dir`.
2. Umgebungsvariable `WORKROOM_DATA_DIR`.
3. Ein vorhandenes `data` neben `start.py`, wenn es bereits eine
   `workspace.sqlite3` enthält. Bestehende Installationen bleiben dadurch erhalten.
4. Für neue Installationen ein fester Benutzerordner: unter Windows
   `%LOCALAPPDATA%\GPUStack-Arbeitsraum`, unter macOS
   `~/Library/Application Support/GPUStack-Arbeitsraum`, unter Linux
   `$XDG_DATA_HOME/GPUStack-Arbeitsraum` bzw.
   `~/.local/share/GPUStack-Arbeitsraum`.

Damit bleiben neue Datenbestände auch bei einem neuen Downloadordner erhalten.
Der tatsächlich gewählte Pfad erscheint beim Start und in den Einstellungen.
Es werden keine alten Datenbestände automatisch verschoben oder zusammengeführt.
Ein selbst gewählter Ordner muss lokal und außerhalb automatisch
synchronisierter Cloud-Ordner liegen:

```bat
.venv\Scripts\python.exe start.py --data-dir "C:\Users\DEINNAME\AppData\Local\GPUStack-Arbeitsraum"
```

Weitere Optionen: `--port 8766` und `--no-browser`.
`--check` prüft Python-Pakete, SQLite-FTS5 und den Datenordner, ohne Serverstart
oder Modellanfrage. `--version` zeigt die Programmversion.
Eine zweite Instanz mit demselben Datenordner wird abgewiesen; ein belegter
Port führt zu einer verständlichen Fehlermeldung.
Das Startprogramm bindet ausschließlich an `127.0.0.1`.
**Nicht mit `0.0.0.0`, mehreren Workern oder einem öffentlichen Reverse-Proxy
betreiben:** Diese PoC-Version hat keine Benutzeranmeldung und keine
Mehrbenutzerberechtigungen.

## 3. GPUStack verbinden

1. Institutionelles VPN verbinden.
2. Im Arbeitsraum **Einstellungen** öffnen.
3. Als API-Basis-URL **`https://gpustack.unibe.ch/v1`** eintragen.
   Diese vom Nutzer bestätigte UniBE-Adresse ist bei einer neuen Einrichtung
   vorbelegt. Bereits gespeicherte Einstellungen bleiben erhalten.
4. Persönlichen API-Schlüssel einsetzen. Standard: nur im Arbeitsspeicher des
   laufenden Python-Dienstes. Optional: Betriebssystem-Schlüsselspeicher.
5. **Speichern & testen**. Die Anwendung ruft die Modellliste ab.
6. Unter **Modellprofile** Aufgaben und Bildfähigkeit prüfen.

„In Modellliste“ bestätigt nur, dass `/models` die Deployment-ID zurückliefert.
Das ist kein erfolgreicher Inferenztest und kein Nachweis sämtlicher
Modellfähigkeiten. Starte mit einer kurzen, nicht vertraulichen Testfrage.
Die acht Profile aus der bereitgestellten MD-Datei sind vorbefüllt.

**SSO und API-Schlüssel sind unterschiedliche Dinge.** Deine Anmeldung an der
GPUStack-Weboberfläche wird nicht automatisch an diese Anwendung weitergegeben.
Für den PoC wird ein API-Schlüssel genutzt; eine eigene OIDC-Anmeldung ist als
Ausbaustufe beschrieben, aber nicht implementiert.

TLS-Zertifikate werden geprüft; Zertifikatsprüfung kann nicht im UI abgeschaltet
werden. Für eine interne Zertifizierungsstelle kann die IT `SSL_CERT_FILE` auf
eine vertrauenswürdige PEM-Datei setzen. HTTPS ist außerhalb von localhost Pflicht.
Systemweite HTTP-Proxy-Variablen werden bewusst nicht übernommen.

Optionaler, von der IT verwalteter Start: `GPUSTACK_BASE_URL` und
`GPUSTACK_API_KEY` als Prozessumgebung bereitstellen. Bei einem Umgebungsschlüssel
kann der Endpunkt im UI nicht geändert werden. Schlüssel niemals in Git, Skripte,
Screenshots oder das vorliegende Startpaket schreiben.

## 4. Der erste vollständige Arbeitsablauf

1. In **Projekte** ein Vorhaben anlegen, etwa „Metadatenprüfung“.
2. Projekt-Systemprompt und feste Projektnotizen eingeben. Diese Notizen bilden
   das sichtbare, ausdrücklich gepflegte Gedächtnis.
3. In **Library** `examples/beispielquelle.md` und bei Bedarf
   `examples/beispieldaten.csv` hochladen. Der Upload selbst bleibt lokal.
4. Im **Chat** die gewünschten Quellen rechts ankreuzen.
5. Ein Chatmodell und bei Bedarf den Skill „Metadaten extrahieren“ wählen.
6. Fragen: „Welche Ortsangaben sind belegt? Nenne die jeweilige Quelle.“
7. Die Quellenchips unter der Antwort öffnen und die ausgewählten Textstellen
   prüfen. Ein Quellenchip belegt, welche Stelle übergeben wurde; er beweist
   nicht automatisch, dass die Modellantwort korrekt ist.
8. Antwort oder gesamten Chat herunterladen. Unter **Verlauf** lassen sich
   auch ältere Gespräche anhand von Titel und Nachrichtentext wiederfinden.

Ein Bild wird nur einem als bildfähig freigegebenen Chatmodell übergeben.
Im Startprofil ist dies `internvl3-8b-instruct`. Weitere Bildmodelle lassen sich
nach einem Test im Modellprofil freigeben. Eine reine Scan-PDF wird nicht
automatisch in Bildseiten zerlegt: zuerst lokal OCR durchführen oder einzelne
Seiten als PNG/JPEG/WebP hochladen.

## 5. Funktionsumfang

| Bereich | In diesem PoC | Grenze / Voraussetzung |
|---|---|---|
| Modellauswahl | Profile und Abgleich mit /models | Kein automatischer Fähigkeitstest |
| Parameter | Temperatur, Top P, Ausgabetokens, optionale Zeichenprüfung; Modellreferenzen mit Quelle | Deployment-Kontext / Outputlimit eintragbar; keine exakte lokale Tokenzählung |
| Modellbegründung / CoT | Gelieferter Reasoning-Text separat anzeigen, speichern und optional exportieren | Nur was der Endpunkt tatsächlich ausgibt; standardmässig nicht im Chat-Export |
| Chat | Streaming, Stoppen, Verlauf, Suche, Umbenennen, Löschen | Ein persönlicher Arbeitsraum; keine Teamkonten |
| Gedächtnis | Projektanweisungen, Projektnotizen, Chat-Systemprompt | Kein unsichtbares automatisches Erinnern |
| Prompts / Skills | Anlegen, ändern, anwenden, löschen | Skills sind Anweisungen, keine ausführbaren Plugins |
| Library | Originale, grosse Bild-/PDF-Vorschau auch im Chat, Projektzuordnung oder gemeinsame Ablage | Projektübergreifend bedeutet nicht Mehrbenutzerfreigabe |
| Dateien | TXT, MD, JSON, CSV, TSV, Text-PDF, DOCX, XLSX | 100 MiB Original, 20 Mio. Textzeichen; einstellbar; grosse Originale ohne Textindex ablegen |
| Bilder | PNG, JPEG, WebP an Vision-Chatmodell | 50 MP je Bild; 8 Bilder/32 MiB pro Anfrage; einstellbar |
| Audio | Aufnahme zuerst auf Festplatte speichern, dann importieren; freigegebene Whisper-Modelle wählen | Mikrofon / Dateipicker browserabhängig; alternativ Download und erneute Dateiauswahl |
| Transkripte | Original erhalten, Arbeitsfassung bearbeiten, Zeitsegmente / Sprecherlabels prüfen und importieren | Automatische Diarisierung benötigt separaten lokalen Dienst; Zeiten vom Backend oder Import |
| Meeting-Protokoll | Vollständiges Transkript an Chatmodell; Entwurf bearbeiten und alles als MD bündeln | Kontext muss ausreichen; Angaben und Entwurf am Audio prüfen |
| Notebook / RAG | FTS5-Textsuche, Quellenstellen, hybride semantische Suche | Ausschnitte, keine garantierte vollständige Dokumentauswertung |
| Embeddings | Indexierung über beide vorgegebenen Embedding-Modelle | Nach Wechsel von Modell oder Endpunkt neu indexieren |
| Reranking | Optional über GPUStacks Jina-kompatible Schnittstelle | Nur bei aktivierter semantischer Suche |
| Recherche | Allgemeine Websuche über SearXNG/Brave; Crossref, Wikidata, GND/lobid, DataCite | Suchanbieter einmalig konfigurieren; Suchauszüge und eingelesenen Webtext unterscheiden |
| Websuche im Chat | Separater sichtbarer Suchtext, optional Trefferseiten lesen; Webquellen mit URL und Abrufzeit | Je Nachricht einschalten; kein unbegrenzter Rechercheagent |
| Lokaler Konnektor | Dateien aus einem freigegebenen Ordner importieren | Nur lesender Import; keine Anwendungssteuerung |
| Routinen | Wiederkehrender Prompt, Aktiv/Pause, sofort ausführen | Nur bei laufendem Dienst; kein Internet, keine Quellenauswahl |
| Downloads | Originale, Antworten, Chats als MD/JSON, Arbeitsraum-Backup | Backup ohne Schlüssel und Datenlabor-Artefakte |
| Datenlabor | Python-Aufträge in separatem Docker-Container | Docker/Image erforderlich; hier nicht end-to-end getestet |
| OpenCode | Download einer vorbereiteten Provider-Konfiguration | Kein eingebetteter Agent oder automatisches Starten |
| SSO | Architektur und Einführungsweg dokumentiert | Nicht implementiert |

## 4a. Neue Medien- und Audiofunktionen

Bilder/PDFs im Entwurf und Chat anklicken, um das Original gross anzusehen.
CoT/Reasoning steht separat unter der Antwort, sofern der Endpunkt es liefert.
Beim Chat- und Antwort-Download **Begründungen einschliessen** bewusst auswählen;
Standard ist aus. Eine vollständige Datensicherung enthält dagegen alle
gespeicherten Reasoning-Daten.

Unter **Kontext → Parameter** erscheinen Herstellerreferenz und separat
eingetragene Deployment-Limits. **Eingabe lokal prüfen** schätzt Texttokens;
exakter Verbrauch nur, wenn der Server Usage-Daten liefert. Die optionale
lokale Zeichenprüfung kann mit **0** deaktiviert werden.

**Audio & Transkripte** führt von Aufnahme/Speicherung über explizite
Transkription bis zum bearbeitbaren Meeting-Protokoll. Originale bleiben
unverändert. Zeit- und Sprecherangaben benötigen Prüfung. Automatische
Diarisierung ist ein vorgeschlagener separater lokaler WhisperX-Dienst,
nicht Bestandteil dieses Python-Pakets.

**Korrekturen in 0.1.6:** Transkriptänderungen, die während einer Speicherung
hinzukommen, werden anschliessend mit der neuen Version gespeichert. MD-/JSON-
Downloads speichern die sichtbare Arbeitsfassung zuerst und prüfen ihre Version.
Bei einem Konflikt mit einem anderen Fenster bleibt der lokale Entwurf erhalten:
**Entwurf sichern** lädt ihn als JSON herunter, **Gespeicherte Fassung laden**
öffnet nach ausdrücklicher Auswahl den aktuellen Stand. Die Entwurfsdatei dient
zum manuellen Vergleich; ein automatischer Entwurfsimport ist nicht eingebaut.
Beim Öffnen eines Chats aus einem anderen Projekt wird auch der Audio-Editor
gewechselt. Die lokale Token-Schätzung wird bei Änderungen verworfen und kann
mit **Eingabe lokal prüfen** erneut berechnet werden.

Ausführlicher Ablauf, Modellquellen, JSON-Importformat und Browserhinweise:
**[Medien, Tokens und Audio](docs/MEDIEN_AUDIO.md)**.

## 6. Dokumentensuche verstehen

**Ohne Index:** Die lokale Volltextsuche findet passende Wörter in den
ausgewählten Dateien. Es gehen nur die für den Chat gewählten Auszüge an das
Chatmodell, nicht die gesamte Ablage.

**Mit semantischem Index:** In der Library bei einer Datei **Indexieren**
wählen. Nach ausdrücklicher Freigabe gehen ihre Textabschnitte an das
konfigurierte Embedding-Modell auf GPUStack. Vektoren bleiben lokal. Im Chat
„Semantische Suche“ aktivieren. Die Suche kombiniert Vektor- und Texttreffer.
Optional ordnet der gewählte Reranker Kandidaten neu.

Die Anwendung verwendet für neue Dokumente standardmässig überlappende
Abschnitte von höchstens 1.800 Zeichen und übergibt bis zu zwölf Treffer pro
Anfrage. Beide Werte sind unter Einstellungen → Ressourcengrenzen änderbar.
Bestehende Abschnitte behalten ihre Länge bis zum erneuten Einlesen.
Diese Zeichenbegrenzung ist kein modellgenauer Tokenizer. Embedding-Limits deshalb am konkreten Modell testen.
Fehlt ein Index, meldet die Oberfläche den Rückfall auf Textsuche. Erfolgreiche
Embedding-Pakete bleiben nach einem Verbindungsfehler erhalten; erneutes
Indexieren setzt fort. Die Suche lädt nicht mehr den gesamten Textindex in den RAM.
Bei fehlenden Texttreffern werden ausgewählte Dokumentanfänge ausdrücklich als solche gezeigt.

Quellenauszüge aus früheren Nachrichten bleiben im Verlauf. Sie können daher
bei Folgefragen erneut im Modellkontext enthalten sein, auch wenn die Datei für
die nächste Nachricht abgewählt wird. Für eine neue, klar getrennte Quellenauswahl
einen **neuen Chat** beginnen. Das gespeicherte JSON-Protokoll enthält pro
Nachricht Quellen, Modell, Parameter und den wirksamen Systemprompt.

Das Eingabebudget ist eine lokale Grenze in **Zeichen**, keine Behauptung zur
Kontextlänge des Modells. Bei Überschreitung wird die Anfrage abgelehnt; der
Verlauf wird nicht automatisch abgeschnitten. Bildtokens werden dabei nicht
geschätzt und müssen im Deployment zusätzlich berücksichtigt werden.

### Externe Recherche: Wikidata und weitere Quellen

Unter **Einstellungen** die externe Recherche ausdrücklich freigeben.
Für **Wikidata** zusätzlich im Feld **Recherchekontakt für externe APIs**
eine echte E-Mail-Adresse oder HTTPS-Kontaktseite hinterlegen und speichern.
Diese Kontaktangabe wird als Teil der Anwendungskennung an den ausgewählten
Anbieter übermittelt. Keine GPUStack-Zugangsdaten, Chats oder Projektdateien
werden für die Recherche verwendet.

In **Recherche** einen öffentlichen Suchtext und genau eine Quelle wählen:

| Quelle | Inhalt | Besonders geeignet für |
|---|---|---|
| Crossref | Publikationsmetadaten, vorhandene Abstracts | Literatur- und DOI-Recherche |
| Wikidata | Entitätskennungen, Labels, kurze Beschreibungen | Personen, Orte und Verknüpfung von Kennungen; keine automatische Tatsachenprüfung |
| GND / lobid | Gemeinsame Normdatei über das hbz | Personen, Geografika, Körperschaften und Schlagwörter |
| DataCite | DOI-Metadaten von Forschungsobjekten | Forschungsdaten, Repositorien und andere zitierbare Forschungsobjekte |

Alle vier Adapter sind ohne Anbieter-API-Schlüssel implementiert.
Ein Recherchekontakt ist für Wikidata erforderlich und kann auch von den
anderen Quellen zur Kontaktaufnahme verwendet werden.
Die vier Fachquellen liefern höchstens acht Treffer. Es gibt keinen automatischen
Quellenwechsel. Allgemeine Websuche und gezielter Webseitenabruf sind separat
verfügbar; siehe den folgenden Abschnitt.

Die frühere Meldung „Die externe Datenquelle ist derzeit nicht erreichbar“
war zu ungenau. Version 0.1.3 unterscheidet fehlenden Recherchekontakt,
HTTP 401/403, HTTP 429, Serverfehler, Zeitüberschreitung, TLS-/Verbindungsfehler,
HTML-Zugriffsschutz und ungültige API-Antworten. Auch API-Fehler in einer
HTTP-200-Antwort werden als Fehler behandelt. Ein gültiges leeres Suchergebnis
bleibt dagegen ein erfolgreicher Aufruf ohne Treffer.

Beim Speichern eines Treffers werden die tatsächlich verwendete Quelle,
der Suchtext und der Abrufzeitpunkt festgehalten. Eine danach geänderte
Quellenauswahl benennt alte Treffer nicht um.

Systemweite Proxy-Variablen werden nicht automatisch übernommen.
Bei institutionellen Netzsperren muss die IT den konkreten Quellendienst
freigeben. Zertifikate werden geprüft; `SSL_CERT_FILE` unterstützt eine
von der IT bereitgestellte vertrauenswürdige Zertifikatskette.
Ein clientseitiges Update kann eine externe Netzsperre nicht aufheben.

Weitere geprüfte Kandidaten, Schnittstellen und Einschränkungen:
[Recherchequellen und Einbindung](docs/RECHERCHE.md).

### Aktive Websuche und Webseiten einlesen (0.1.7)

Unter **Einstellungen → Websuche** eine eigene SearXNG-Basis-URL oder einen
separaten Brave Search API-Schlüssel hinterlegen. Externe Recherche ausdrücklich
freigeben. Eine SearXNG-Instanz braucht JSON-Freigabe; sie wird nicht mitinstalliert.
Kein Suchanbieter wird ohne Konfiguration automatisch angesprochen.
**Einrichtung Schritt für Schritt** öffnet die Anleitung direkt in der App;
**Anleitung herunterladen** liefert sie als Markdown. Beide Funktionen sind
auch ohne externe Recherchefreigabe verfügbar. Die Anleitung erklärt Brave-
Registrierung, Tarif/Schlüssel, Speicherung, SearXNG/IT-Einrichtung und Fehler.
**Brave und gespeicherte Quellen:** Ein Vertrag mit passenden Speicherrechten
ist erforderlich; die App speichert Belege in Chats und Projektquellen und
prüft keine Anbieter-Verträge.

Unter **Recherche → Websuche** allgemein suchen, Treffer prüfen und gezielt
**Seite einlesen**. Über **Eine Webseite direkt einlesen** ist der öffentliche
HTTPS-Textabruf auch ohne Suchschlüssel verfügbar. Vorschau, MD-Download und
bewusstes Speichern als Projektquelle sind enthalten.

Im Chat **Websuche für diese Nachricht** einschalten und einen separaten
öffentlichen Suchtext eingeben. Optional Trefferseiten einlesen lassen. Nur
Suchtext und gewählte Seitenadressen gehen an externe Dienste; keine komplette
Chat-/Projektübergabe an den Suchanbieter. Webauszüge gehen anschliessend an das
gewählte GPUStack-Modell. **[Wn]**-Quellen zeigen URL, Textart und Abrufzeit und
bleiben in Chat-/Antwortdownloads erhalten. Vorhandene Webbelege im Verlauf
können in Folgeanfragen enthalten sein; neue Websuche ist wieder ausgeschaltet.

Kein JavaScript, Browser-Cookie-Import oder Umgehen von Anmeldungen/Paywalls.
Private IP-Adressen und Weiterleitungen darauf sind gesperrt; robots.txt wird
geprüft. Eine Suche ist kein Nachweis für korrekte Modellantworten.
Einrichtung, Datenwege, Grenzen und Abnahme: **[Websuche](docs/WEBSUCHE.md)**.

### Grosse Dokumente und Update auf 0.1.10

Version 0.1.8 lag nur als Ergänzungspaket ohne Starter und Abhängigkeitslisten
vor. Das GitHub-Repository ab 0.1.9 enthält wieder das vollständige Paket.
Ab 0.1.10 ergänzt der grafische Starter die Einrichtung und den alltäglichen
Start per Doppelklick.
Für ein Update den Dienst beenden und den in den Einstellungen angezeigten
Datenordner sichern. Das neue Repository-ZIP separat entpacken. Eigene
Startargumente, insbesondere `--data-dir`, für den neuen Starter übernehmen.
Ein bestehender `data`-Ordner neben dem alten Starter kann entweder am selben
Ort weiterverwendet oder mit `--data-dir` ausdrücklich angegeben werden.

Über `start.cmd` die Einrichtung im Startfenster ausführen oder mit dem
verwendeten Python die Abhängigkeiten aus `requirements.txt` installieren
und die Einrichtung mit `start.py --check` prüfen.
Das Paket enthält keine Nutzerdaten und keine persönlichen Schlüssel.

Anschließend wie bisher starten, die Browserseite mit **Strg+F5** neu laden,
den zuvor gescheiterten Upload wiederholen. Bei Bedarf unter **Einstellungen →
Ressourcengrenzen** höhere Werte setzen. Für Wikidata weiterhin einen echten
Recherchekontakt hinterlegen und einen öffentlichen Begriff testen.
Den Datenpfad vor der ersten Modellanfrage in den Einstellungen kontrollieren.
Bei einem unerwartet leeren Arbeitsraum zuerst den bisherigen Datenordner
angeben; keinen neuen Datenbestand mit einem Backup vermischen.

Die frühere 1-Mio.-Zeichen-Grenze war ein fester lokaler PoC-Schutz, unabhängig
vom Modell. Neu: **100 MiB pro Original, 20 Mio. Textzeichen, keine pauschale
PDF-Seiten- oder Excel-Zeilengrenze**, längere und einstellbare Parserlaufzeit.
Bei einer Einlesegrenze bleibt das vollständige Original im Projekt gespeichert,
ohne gekürzten Teilindex. In der Library lässt es sich später **erneut einlesen**
oder direkt als vollständige Datenlabor-Eingabe verwenden. Mit **Nur Original
ablegen** kann die Textextraktion bewusst übersprungen werden.

Projekt- und gemeinsame Ablage verwenden dieselben Uploadgrenzen.
Mehr gespeicherter Text erhöht nicht das Modellkontextfenster: RAG übergibt
Ausschnitte. Für Summen und Vollständigkeitsprüfungen die ganze Tabelle mit
pandas/openpyxl berechnen. Neue Chats starten mit 8.192 Ausgabetokens (bzw. einem kleineren eingetragenen Deployment-Limit) und 48.000 Zeichen als optionaler Eingabeprüfung; **0 deaktiviert die Zeichenprüfung**;
bestehende Chats behalten ihre Werte. Höhere Budgets im Chat müssen zum
Deployment passen. Neue Routinen speichern ihr eigenes Budget und Ausgabetokens.

Die vollständige Prüfung aller Grenzwerte mit Einstellbereichen und Alternativen
steht in **[Grosse Dokumente und Ressourcengrenzen](docs/GRENZEN.md)**.

## 7. Datenlabor optional einrichten

Der Kern-PoC funktioniert ohne Docker. Für Berechnungen und echte XLSX/PPTX-Dateien
ist eine getrennte Ausführungsumgebung vorgesehen. Auf einem verwalteten
Windows-Rechner ist hierfür in der Regel die IT zuständig.

```bat
docker build -t gpustack-workroom-runner:local runner
set WORKROOM_ENABLE_RUNNER=1
.venv\Scripts\python.exe start.py
```

Beim Image-Bau werden Python und Pakete heruntergeladen. **Zur Laufzeit** ist der
Container netzlos. Es werden keine Zugangsdaten übergeben. Eingabedateien sind
schreibgeschützt unter `/input`, Ausgaben unter `/output`. Jede Ausführung
benötigt eine Checkbox-Freigabe im UI. Das Chatmodell kann keine Jobs selbst starten.

Vorgaben: 300 Sekunden, 2.048 MiB RAM, 512 MiB Temporärspeicher, 100 MiB
Ausgabedateien. Diese vier Werte sind unter Ressourcengrenzen einstellbar.
Eine CPU, 64 Prozesse, kein privilegierter
Container, Dateisystem schreibgeschützt außer temporärem Bereich und
Ergebnisordner. Docker-Socket und Rechnerverzeichnisse werden nicht
in den Container eingebunden. Das Runner-Image wird beim Ausführen nicht
automatisch heruntergeladen. Es gibt keinen Rückfall auf Host-Python.

Enthaltene Vorlagen: CSV → Excel-Prüfbericht; editierbare PowerPoint-Datei mit
python-pptx. Die PPTX-Vorlage ist ein einfacher Funktionstest, kein fertiges
Corporate-Design-System. Ergebnisdateien separat herunterladen.

Der Runner ist eine PoC-Isolation, keine zertifizierte Sandbox: Insbesondere
braucht ein institutioneller Betrieb eine Festplattenquote, eine gepflegte
Containerbasis und gegebenenfalls stärkere Isolation in einer eigenen VM.
Hier konnten Docker und der Containerlauf nicht getestet werden.

## 8. Lokaler Importordner

In cmd.exe vor dem Start:

```bat
set WORKROOM_IMPORT_ROOT=Z:\DCB Collections\Freigegebener-KI-Import
.venv\Scripts\python.exe start.py
```

Unter **Datenlabor → Lokaler Ordner** Dateien einzeln auswählen. Die Anwendung
kopiert die gewählte Datei in die Library. Der Ursprungsbestand bleibt
unverändert. Pfade und symbolische Links außerhalb des freigegebenen Ordners
werden abgewiesen. Keine automatische Überwachung, kein Schreiben zurück ins
Quellsystem, keine umfassende Suche über Netzlaufwerke.

Für easydb/fylr, SharePoint, lokale Office-Anwendungen oder weitere Datenquellen
sind später jeweils eigene, eng berechtigte Konnektoren sinnvoll.

## 9. Sichern und löschen

**Einstellungen → Arbeitsraum sichern** erzeugt einen konsistenten SQLite-
Snapshot einschließlich Originaldateien. Die Schlüsselverwaltung wird nicht
exportiert. Datenlabor-Ergebnisse sind separat zu sichern. Die frühere
150-MiB-Grenze ist entfernt: ZIP und Snapshot entstehen temporär auf Festplatte
statt vollständig im RAM. Dafür genügend freien Speicher vorhalten.

Für eine vollständige Sicherung einschließlich Datenlabor den Dienst beenden
und den gesamten Datenordner mit einem institutionell freigegebenen,
verschlüsselten Backupverfahren sichern. SQLite nicht live auf ein
Netzlaufwerk oder in einen synchronisierten Ordner verlagern.

Wiederherstellen: Dienst beenden, bisherigen Datenordner separat sichern,
gesicherten `data`-Inhalt an dessen Stelle kopieren und den Dienst neu starten.
API-Schlüssel erneut hinterlegen. Nicht in einen laufenden Datenbestand mischen.
Der Restore ist bewusst ein Dateivorgang, kein automatischer ZIP-Import im UI.

Eine Datei zu löschen entfernt Original und Suchindex. Bereits im Chat
gespeicherte Belege bleiben erhalten. Für die Entfernung dieser Inhalte auch
die betroffenen Chats, Projektnotizen, Exporte und Backups beachten. Die App
verspricht keine forensisch sichere Löschung auf SSDs.

## 10. Erweiterung und Prüfung

- [Grosse Dokumente und Ressourcengrenzen](docs/GRENZEN.md)
- [Architektur und Ausbau](docs/ARCHITEKTUR.md)
- [Modellprofile und Grenzen der Quelldatei](docs/MODELLPROFILE.md)
- [Recherchequellen und Einbindung](docs/RECHERCHE.md)
- [Websuche: Einrichtung und Verwendung](docs/WEBSUCHE.md)
- [Prüfprotokoll und Abnahme vor Ort](docs/PRUEFPROTOKOLL.md)

Die Abhängigkeiten in `requirements.txt` sind auf die im Test verwendeten
Hauptpaketversionen festgelegt. Das ist kein vollständig gehashter Lock aller
transitiven Abhängigkeiten. Für einen institutionellen Rollout einen geprüften
Lock/Wheel-Satz und einen geregelten Updateprozess ergänzen.

Backend-Tests:

```bat
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

Die optionale DOM-Prüfung braucht zusätzlich Node.js und `jsdom`:

```sh
npm ci
PYTHON=.venv/bin/python npm test
```

Unter Windows vor `npm test` stattdessen
`set "PYTHON=.venv\Scripts\python.exe"` verwenden.
Benötigt wird eine von `package.json` unterstützte Node.js-Version
(22 ab 22.22.2 oder 24 ab 24.15.0; außerdem 26 und neuer).

Diese Testabhängigkeiten gehören nicht zum normalen Start. Die Tests verwenden
synthetische Daten und simulierte Modellantworten.

## 11. Häufige Probleme

### Upload meldet `'charmap' codec can't encode character`

Bis einschließlich Version 0.1.1 konnte die Ausgabe des Datei-Parserprozesses
unter Windows-1252 bei Unicode-Zeichen wie dem mathematischen Minus `−`
scheitern. Auch gültige UTF-8-Dateien waren betroffen.
Version 0.1.2 übergibt Parserergebnisse als ASCII-kompatibles JSON. Ab 0.1.4
wird ein grosses Ergebnis direkt in eine temporäre UTF-8-Datei geschrieben.
Beide Wege erhalten sämtliche Unicode-Zeichen.
Originaldateien und Dokumentinhalte werden nicht verändert.

Für die aktuelle Version das vollständige **Repository-ZIP** verwenden,
wie oben beschrieben. `app/extract.py` arbeitet mit `app/limits.py` und
`app/documents.py` zusammen; nicht nur diese eine neue Datei in eine alte
Installation kopieren. Abhängigkeiten aus `requirements.txt` installieren
und anschließend den Upload wiederholen.

### Lokaler Browser meldet ERR_CONNECTION_REFUSED

Die Adresse `http://127.0.0.1:8765` gehört zum lokalen Python-Dienst.
Die GPUStack-Adresse `https://gpustack.unibe.ch/v1` wird erst innerhalb der
Anwendung für Modellanfragen verwendet. Die Oberfläche muss auch ohne VPN
oder API-Schlüssel starten.

Version 0.1.0 öffnete den Browser nach festen 1,5 Sekunden und gab die Adresse
bereits vor dem tatsächlichen Serverstart aus. Version 0.1.1 wartet auf den
erfolgreichen Start und zeigt die Startmeldungen des Servers.

1. Den alten Startprozess mit **Strg+C** beenden.
2. Für diese Korrektur genügt es, `start.py` durch die neue Datei zu ersetzen.
   Der vorhandene Ordner `data` mit Chats und Dokumenten bleibt bestehen.
3. Mit demselben Python-Interpreter erneut starten. Auf **Arbeitsraum bereit**
   warten und das Terminal geöffnet lassen.
4. Erscheint stattdessen ein Fehler, die vollständige Terminalausgabe prüfen.
   Bei belegtem Port mit `--port 8766` starten und die ausgegebene Adresse
   verwenden.
5. Wird der Server als bereit gemeldet, aber der Browser verweigert weiterhin
   die Verbindung, in PowerShell lokal prüfen:
   `Test-NetConnection 127.0.0.1 -Port 8765`.
   Die Ausgabe und die Startmeldungen helfen der IT, Dienst und Browserzugriff
   getrennt zu prüfen.

| Meldung / Beobachtung | Nächster Schritt |
|---|---|
| Grafisches Startfenster öffnet sich nicht | `start-debug.cmd` doppelklicken; vollständiges Paket und Python mit Tcl/Tk prüfen. |
| Grafische Einrichtung schlägt fehl | Im Startfenster **Details** öffnen bzw. **Protokoll kopieren**; Paketquelle, Internetzugriff und institutionelle Installationsrechte prüfen. |
| `start.py` / `requirements.txt` nicht gefunden | Vollständiges Repository-ZIP neu entpacken; in den Ordner mit diesen Dateien wechseln. Das Updatepaket 0.1.8 enthält sie nicht. |
| `py` nicht erkannt | Den bereits vorhandenen Interpreter mit `python` aufrufen. |
| PowerShell meldet ein Modul `.venv` | Die Umgebung muss zuerst erfolgreich angelegt sein. Anschließend `.\.venv\Scripts\python.exe` mit führendem `.\` verwenden. |
| GPUStack nicht erreichbar | VPN auf dem Rechner prüfen, Basis-URL und internes Zertifikat kontrollieren |
| HTTP 401 / 403 | API-Schlüssel, Ablaufdatum und Modellberechtigungen prüfen |
| HTTP 404 | /v1 bzw. /v1-openai und Modell-Deployment prüfen |
| Modell in Liste, keine Antwort | Kurzen Text ohne Quellen senden; Parameter und Inferenzlogs prüfen |
| Keine Textebene | Scan vorab lokal OCR-verarbeiten oder Seiten als Bilder übergeben |
| Datei überschreitet eine Einlesegrenze | Original bleibt gespeichert; Ressourcengrenzen anpassen und Text erneut einlesen, oder Datenlabor verwenden |
| Falsche / unvollständige Zahlen | Vollständige CSV/XLSX im Datenlabor berechnen; RAG zeigt nur Ausschnitte |
| Kein freigegebener Schlüsselspeicher | Sitzungsspeicher wählen; OS-Schlüsselspeicher einrichten lassen |
| Semantische Suche ohne Index | Datei explizit indexieren; nach Modell-/Endpunktwechsel neu indexieren |
| Routine läuft nicht | Dienst, VPN und Schlüssel müssen verfügbar sein |
| Oberfläche über file:// geöffnet | start.py starten und die localhost-Adresse verwenden |
| Port bereits belegt | Mit --port 8766 starten |

**Einordnung:** Die Anwendung bietet technische Begrenzungen der Datenwege,
aber keine pauschale Garantie rechtlicher Datenschutzkonformität. Speicherort,
Laufwerksverschlüsselung, Berechtigungen, GPUStack-Logging, Aufbewahrung,
Backups und freigegebene Datenarten müssen institutionell geklärt sein.
