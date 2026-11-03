# Architektur und Ausbau

## Entscheidung

**Browseroberfläche + lokaler Python-Dienst + institutionelles GPUStack.**
Die Grafikprozessoren und der GPUStack-Inferenzdienst müssen keine Notebooks,
Dokumentarchive oder persönlichen Chatverläufe übernehmen. Diese Aufgaben liegen
in einer eigenen Anwendungsschicht.

Ein reines HTML-Frontend ist für den gewünschten Umfang zu wenig:
Schlüsselverwaltung, persistente Dateien, Suchindex, Zeitpläne und Codeausführung
brauchen einen vertrauenswürdigen Dienst. Im PoC läuft dieser auf dem
Arbeitsrechner. Der Browser spricht nur mit diesem Dienst.

| Vertrauensbereich | Komponenten |
|---|---|
| Persönlicher Rechner | Browser, Python-Dienst, SQLite, Originaldateien und OS-Schlüsselspeicher |
| Institutionelles Netz | GPUStack-Inferenz, über VPN und HTTPS erreichbar |
| Explizit freigegebenes Internet | Gewählte Recherchequelle, bewusster Suchtext und ggf. hinterlegter Recherchekontakt |
| Getrennte Ausführung | Optionaler Python-Container ohne Netzwerk und API-Schlüssel |

Die App ist aktuell **ein persönlicher Arbeitsplatz**, kein Mandantensystem.
„Gemeinsame Library“ bedeutet lediglich: Quellen sind innerhalb dieses
Arbeitsplatzes in mehreren Projekten auswählbar.

## Datenwege

| Aktion | Gesendete Daten | Empfänger | Persistenz |
|---|---|---|---|
| Datei hochladen | Datei vom Browser | Lokaler Dienst | Original + Textabschnitte lokal; bei Einlesegrenze nur Original |
| Chat senden | Systemanweisungen, Projektnotizen, Verlauf, gewählte Quellenauszüge und Bilder | Konfigurierter GPUStack-Endpunkt | Frage, Antwort, Quellen und Parameter lokal |
| Dokument indexieren | Textabschnitte der ausdrücklich gewählten Datei | Embedding-Modell auf GPUStack | Vektoren lokal |
| Semantisch suchen | Frage als Embedding-Eingabe | Embedding-Modell auf GPUStack | Kein eigenständiges Suchprotokoll; Chat protokolliert Kontext |
| Reranking | Frage + Trefferauszüge | Reranker auf GPUStack | Ausgewählte Treffer im Chat |
| Transkribieren | Gewählte Audiodatei | Gewähltes Audio-Modell auf GPUStack | Originalantwort, TXT und versionierte Arbeitsfassung lokal |
| Internet recherchieren | Bewusster Suchtext und ggf. Recherchekontakt in der Clientkennung | Ausgewählte öffentliche Datenquelle | Treffer mit Quelle, Suchtext und Abrufzeitpunkt erst nach „Als Projektquelle speichern“ |
| Lokalen Ordner importieren | Gewählte Datei | Lokaler Dienst | Kopie, kein Rückschreiben |
| Routine ausführen | Gespeicherter Prompt + aktuelle Projektanweisungen | GPUStack | Neuer Chat lokal |
| Code ausführen | Geprüfter Code + explizit ausgewählte Eingabekopien | Netzloser Docker-Container | Ausgabe im lokalen Jobordner |

**Abwählen ist kein Vergessen:** In einem bestehenden Chat bleiben früher
verwendete Quellenauszüge im Gesprächskontext. Für einen neuen Kontext einen neuen
Chat beginnen. Löschen von Originalen löscht keine früheren Zitate oder Exporte.

GPUStack kann seinerseits Inferenzanfragen und Metadaten protokollieren.
Das Verhalten des institutionellen Dienstes wird durch dieses Frontend nicht
überschrieben. Auch Vektoren können Informationen über Dokumentinhalte tragen
und sind entsprechend zu schützen.

## Umsetzung

| Datei / Modul | Verantwortung |
|---|---|
| `start.py`, `start.cmd` | Start nur auf localhost, eine Instanz |
| `web/index.html`, `web/style.css`, `web/app.js` | Deutsche Oberfläche ohne CDN oder Build-Schritt |
| `app/main.py` | Lokale API, Datenflüsse, Streaming, Zeitpläne |
| `app/research.py` | Quellenkatalog, explizite Recherche, Anbieteradapter und Fehlerdiagnose; kein GPUStack-Schlüssel |
| `app/limits.py` | Persistente, validierte Ressourcengrenzen und UI-Katalog; unabhängig von Modelllimits |
| `app/store.py` | SQLite-Schema, Datenzugriff, FTS5, Persistenz |
| `app/catalog.py` | Typisierte, editierbare Deployment-Profile |
| `app/gpu.py` | GPUStack-Adapter, TLS, Schlüsselspeicher, verständliche Fehler |
| `app/documents.py`, `app/extract.py` | Uploads auf Festplatte, UTF-8-Parserdatei, Originalablage bei Limits, atomisches erneutes Einlesen |
| `app/retrieval.py` | Treffersuche ohne Gesamtladen, Vektorscan in Batches, wiederaufnehmbare Embeddings, Reranker |
| `app/execution.py`, `runner/Dockerfile` | Explizit freigegebene Containerjobs |
| `tests/` | API-Integration und DOM-Abläufe mit synthetischen Daten |

Diese Trennung erlaubt weitere Datenquellen, zusätzliche Dokumentparser oder
andere Ausführungsdienste ohne Neuentwurf der Oberfläche. Für einen
umfangreicheren Ausbau sollten die Routen in `main.py` in Router je
Funktionsbereich aufgeteilt und Schemaänderungen als Migrationen versioniert
werden. Der aktuelle Stand legt Schema v1 an; es gibt noch keinen
Versionsmigrationsmechanismus für künftige Änderungen.

## Bewusste Sicherheitsentscheidungen

- Keine API-Schlüssel im Browser-Speicher, SQLite, Projektdateien oder Backup.
  Zugangsdaten werden vom Browser einmal an den lokalen Dienst übergeben und
  anschließend im Eingabefeld geleert. Der Dienst gibt sie nicht zurück.
- Sitzungsschlüssel bleiben im Prozessspeicher. Persistente Speicherung ist
  ausschließlich über freigegebene OS-Keyring-Backends vorgesehen: Windows,
  macOS, Secret Service oder KWallet. Unbekannte und Klartext-Backends werden
  abgelehnt.
- Bindung an localhost; Host-Prüfung gegen DNS-Rebinding; keine offenen
  CORS-Freigaben; CSRF-Token und Herkunftsprüfung für Änderungen.
- Externes HTTP für GPUStack ist gesperrt. TLS-Prüfung bleibt aktiviert.
  Redirects und implizite Proxy-Variablen sind deaktiviert.
- Keine externen Schriften, Skripte, Analytics oder automatisch geladenen
  Bilder. Modellantworten werden als maskierter Text mit begrenzter
  Markdown-Darstellung ausgegeben. Fremdes HTML wird nicht ausgeführt.
- Quellen sind Daten, keine Handlungsanweisungen. Der Chat darf keine Tools
  selbst aufrufen. Prompt-Injection lässt sich damit begrenzen, nicht als
  Modellphänomen vollständig beseitigen.
- Text-Extraktion läuft mit Zeitlimit in einem Unterprozess. Unter Linux
  zusätzlich RAM-/CPU-Limits. Auf Windows ist dies keine vollständige
  Parser-Sandbox; im institutionellen Betrieb Parser weiter isolieren.
- Upload- und Kontextgrenzen, explizite Projektprüfung bei Quellenauswahl,
  Downloadpfade anhand interner IDs und begrenzter Importordner.
- Keine Chatinhalte in eigenen Anwendungslogs. HTTP-Zugriffslogs sind im
  regulären Start deaktiviert. Unbehandelte Frameworkfehler können technische
  Fehlermeldungen auf der Konsole erzeugen.
- Datenbank und Originale werden nicht von der App verschlüsselt.
  Dateirechte, Laufwerksverschlüsselung und ein institutionelles Backupkonzept
  bleiben Betriebsaufgaben.

## Warum GitHub Pages allein nicht genügt

GitHub Pages hostet statisches HTML/CSS/JavaScript. Es stellt den benötigten
Python-Dienst, seine Geheimnisse, Dateipersistenz und Jobs nicht bereit.
Ein öffentlich ausgeliefertes Frontend würde außerdem eine zusätzliche
Vertrauensgrenze schaffen: Der ausgelieferte JavaScript-Code könnte
Eingaben und Schlüssel lesen. Private Repository-Sichtbarkeit allein löst
diese Laufzeitfragen nicht.

Für eine gemanagte Umgebung ist eine **institutionell betriebene Anwendung**
sinnvoll: Frontend und Backend auf derselben HTTPS-Origin, Backend mit
Netzzugang zu GPUStack, definierter Speicherort, kontrollierte Updates und SSO.
GitHub kann für Quellcode, Review und CI/CD dienen. Die vertraulichen
Laufzeitdaten gehören nicht ins Repository.

Die jetzige Anwendung nicht einfach ins Netz stellen. Insbesondere
`WORKROOM_ALLOWED_HOSTS` ist eine Entwicklungsoption, keine Anmeldung.

## SSO: konkrete nächste Ausbaustufe

1. Einen eigenen OIDC-Client für den Arbeitsraum beim institutionellen
   Identity Provider registrieren. GPUStack unterstützt OIDC und weitere
   Anmeldeverfahren, aber seine Browsersitzung ist kein allgemeines API-Ticket.
2. Authorization Code Flow mit PKCE, State und Nonce; Tokens serverseitig;
   Browser erhält eine sichere HttpOnly-/Secure-Sitzung. Issuer, Audience,
   Signaturen, Ablauf und Logout werden geprüft.
3. Tabellen um Benutzer-/Mandantenbesitz ergänzen. Zugriffsrechte auf
   Projekte, Dokumente, Chats, Jobs und Suchtreffer **serverseitig** prüfen.
   Vor der Suche muss derselbe Berechtigungsfilter gelten wie beim Download.
4. GPUStack-Zugriff klären: persönliche Credentials oder ein eng berechtigter
   Dienstzugang. Identitätsweitergabe darf nicht stillschweigend vorausgesetzt
   werden. Abrechenbarkeit, Ratenlimits und Modellberechtigungen festlegen.
5. Routinen und Jobs mit Benutzeridentität und Widerruf von Berechtigungen
   verbinden. Ein ausscheidender Benutzer darf keine aktiven Hintergrundjobs
   zurücklassen.

Ohne euren Identity Provider und dessen Clientregistrierung ist dieser Schritt
nicht end-to-end abnehmbar. Im PoC gibt es deshalb keinen irreführenden
„SSO anmelden“-Knopf.

## OpenCode und Ausführungsumgebung

OpenCode ist eine Agenten-/Werkzeugschicht, keine automatische
Datenschutzgarantie und keine Container-Sandbox. Im UI lässt sich eine
**OpenCode-1.x-Konfiguration** herunterladen: eigener OpenAI-kompatibler
GPUStack-Provider, Haupt- und Hilfsmodell auf GPUStack, Provider-Allowlist,
Sharing und automatische Updates aus, externe Webwerkzeuge blockiert,
übrige Aktionen mit Rückfrage. Das Secret wird als Umgebungsreferenz
eingetragen.

Globale Einstellungen, Plugins und Versionsunterschiede können das Verhalten
ändern. Die Konfiguration wurde nicht mit einer installierten OpenCode-Version
ausgeführt. Bei OpenCode 2.x die geänderten Konfigurations- und
Berechtigungsschemata beachten. Updates/Provider-Metadaten sind zusätzlich
über Netzregeln kontrollierbar zu machen.

Eine nächste Integration kann OpenCode in einem **separaten, pro Auftrag
begrenzten Arbeitsverzeichnis** betreiben und Ergebnisse über einen Jobadapter
in die Library übernehmen. Werkzeuge müssen eine eng definierte Schnittstelle
mit Dateifreigabe, Freigabe vor Ausführung und Artefakt-Download erhalten.
Kein Zugriff des Modells auf den Docker-Socket oder den vollständigen
Benutzerdatenträger. Der aktuelle Python-Runner ist bereits so getrennt,
arbeitet aber ohne eingebetteten OpenCode-Agenten.

## Empfohlene Ausbaufolge

| Stufe | Lieferumfang | Abnahmekriterium |
|---|---|---|
| 1 · Lokaler PoC | Vorliegendes Paket; nicht vertrauliche Testdokumente | GPUStack-API, Modellparameter, Bildinput und RAG vor Ort geprüft |
| 2 · Einzelplatz freigeben | Datenarten, Speicherort, Verschlüsselung, Löschung, Keyring, Backup | IT-/Datenschutzfreigabe für konkreten Betrieb |
| 3 · Dokumentarbeit vertiefen | Lokale OCR, Tokenizer, größere Dateien, Jobqueue, Qualitätsstichproben | Belege und Trefferqualität für echte Sammlungsaufgaben gemessen |
| 4 · Institutioneller Dienst | SSO, Benutzerrechte, serverseitiger Speicher, zentrale Jobs | Keine Zugriffe zwischen unberechtigten Projekten |
| 5 · Werkzeuge/Konnektoren | Isolierter Runner, ggf. OpenCode, gezielte Fachsystem-Adapter | Freigaben, Netzgrenzen und Artefakte nachvollziehbar |

RAG lässt sich später auf einen separaten Vektorindex umstellen. Im lokalen PoC
sind SQLite und im Prozess berechnete Ähnlichkeiten nachvollziehbar und
betriebsarm. Für große Bestände braucht es gemessene Größen-/Latenzgrenzen,
einen geeigneten Index und einen Hintergrunddienst für Indexierung.

## Primärquellen

Abgerufen am 5. Oktober 2026. Die lokal installierte Produktversion bleibt
maßgeblich.

- GPUStack, Inference APIs:
  https://docs.gpustack.ai/latest/integrations/inference-apis/
- GPUStack, API Key Management:
  https://docs.gpustack.ai/latest/user-guide/api-key-management/
- GPUStack, Single Sign-On:
  https://docs.gpustack.ai/latest/user-guide/sso/
- GitHub, What is GitHub Pages?:
  https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
- OpenCode, Providers:
  https://opencode.ai/docs/providers/
- OpenCode, Permissions:
  https://opencode.ai/docs/permissions/
- OpenCode, Config:
  https://opencode.ai/docs/config/
- Docker, Resource constraints:
  https://docs.docker.com/engine/containers/resource_constraints/
- Docker, None network driver:
  https://docs.docker.com/engine/network/drivers/none/
- Python keyring:
  https://keyring.readthedocs.io/en/latest/

## Stand 0.1.4: grosse Dokumente

Dateiablage, Textextraktion und Modellkontext haben getrennte Budgets.
Ein Überschreiten der Extraktionsgrenze führt zur vollständig erhaltenen
Originalablage; keine gekürzten Teilindizes. Grenzwerte und geeignete
Arbeitsweisen stehen in [GRENZEN.md](GRENZEN.md). Neue Routinen speichern
Modellbudget und Ausgabetokens; SQLite-Schema 2 ergänzt diese Spalte additiv.
Das Backup ist festplattenbasiert; Originale und Datenbank bleiben dieselben.

## Stand 0.1.5: Medien und Transkripte

SQLite-Schema 3 ergänzt transcripts mit unverändertem original und versioniertem working. Projektlöschung entfernt Transkripte; Audio-/TXT-Löschung setzt den jeweiligen Verweis auf NULL. Bearbeitung und Protokollgenerierung prüfen Versionsstände atomar. app/transcripts.py kapselt Transkription, Validierung, Protokollauftrag und Export; web/audio.js kapselt Aufnahme und Editor.

Bilder/PDFs werden vom lokalen Originalendpunkt inline bereitgestellt. Same-origin Frames und Audio sind in CSP erlaubt, HTML-Originale werden weiterhin nicht inline angezeigt. Chatmetadaten speichern Anhangreferenzen getrennt von RAG-Auszügen und tatsächlich gesendeten Bildern. Scan-PDF-Vorschauen ohne Text gelangen nicht als Modellquelle in den Payload.

Reasoning aus expliziten Endpunktfeldern / think-Blöcken wird separat gespeichert, nicht erneut als History gesendet. Export bereinigt diese Metadaten standardmässig. Eine vollständige Datensicherung enthält weiterhin alle lokal gespeicherten Daten.

Browseraufnahme ruft nach explizitem Klick Dateipicker, Schreibstream und Mikrofon auf. Datei wird fertig geschlossen, bevor ein eigener Importbutton den lokalen Upload erlaubt. Fehlt der Dateipicker, muss ein Download erst lokal gespeichert und erneut gewählt werden. Erst der Transkriptionsbutton sendet Audio an GPUStack.

## Korrekturen 0.1.6: Fassungen und Frontendzustand

Der Audio-Editor serialisiert Speichervorgänge über eine gemeinsame Promise.
Jeder Request erhält eine Kopie der Arbeitsfassung und ihre Editierrevision.
Kam während des Requests eine Eingabe hinzu, wird nur die serverseitige Version
aktualisiert; der neue lokale Entwurf folgt in einem weiteren PUT. Navigation
wartet auf diese Kette. Downloads, Quellenerstellung und Modellaufträge sperren
den Editor während der Vorbereitung und verwenden den zurückgegebenen Stand.

Transkript-Exports akzeptieren optional `version` als Queryparameter,
Projektquellen optional `{ "version": N }` im Body. Eine Abweichung ergibt 409.
Die Antwort verwendet die beim Check gelesene Fassung. Alte Aufrufe ohne Version
bleiben kompatibel. Ein Konflikt erhält den Editor; ein separater JSON-Entwurf
kann vor dem bewussten Neuladen gesichert werden. Keine automatische Fusion.

Projektwechsel durch Chatnavigation verwendet dieselben Audioguards wie die
Projektwahl und setzt den Editor zurück. Budgetanzeigen tragen eine lokale
Revision; bei Kontextänderungen werden sie invalidiert. Verspätete Antworten
mit einer überholten Revision werden nicht angezeigt.

## Stand 0.1.7: Websuche

`app/websearch.py` trennt SearXNG/Brave-Konfiguration und Brave-Credential vom
GPUStack-Adapter. Speichern löst keine Netzabfrage aus. `internet_enabled` ist
für jede externe Suche/jeden Webseitenabruf erforderlich. `web_search` liegt
als nicht geheime Konfiguration in den bestehenden Settings, Schlüssel nur
in Umgebung, Serversitzung oder freigegebenem OS-Keyring. Keine DB-Migration.

`web/websearch.js` verwaltet die per Nachricht ausgeschaltete Weboption,
öffentlichen Suchtext, Quellenarten, Vorschau und separate Einrichtung. Die
App führt eine Suchanfrage aus; optional liest sie eine begrenzte Zahl Treffer.
Sie benötigt keine Modell-Tool-Aufrufe. `assemble` prüft den Modellkontext nach
Hinzufügen der Quellen erneut; [Wn]-Labels bleiben wie [Qn] über den Verlauf
hinweg eindeutig. Web-Metadaten und übergebener Text bleiben in Nachricht/Export.
Die Budgetvorschau bleibt lokal. Vor dem Streaming erkannter Clientabbruch
bricht die Recherchevorbereitung ab und gibt den Thread frei.

Der native HTTPS-Leser prüft öffentliche IP-Adressen und verbindet die geprüfte
numerische Adresse. TLS/Host/SNI behalten den ursprünglichen Domainnamen. Keine
zweite Namensauflösung der Domain für die Verbindung, keine Cookies, Auth-
Weitergabe, Umgebungsproxies, JS oder ungeprüften Redirects. Jeder Zielpfad wird
mit robots.txt geprüft. HTML-Auszüge sind ungeprüftes Material, keine garantierte
Abbildung des sichtbaren Browserinhalts. Native Reader laufen im Thread mit
Zeit-/Bytegrenzen; ein bereits laufender Request kann bei Abbruch auslaufen.

Noch nicht gespeicherte Recherche-Ergebnisse liegen in maximal 20 flüchtigen
Snapshots für 30 Minuten. `/api/web/source` übernimmt einen serverseitigen Stand,
keinen vom Browser behaupteten Webtext. Gespeicherte Projektquellen aktualisieren
sich nicht von selbst. Details und Netzfreigaben: `WEBSUCHE.md`.
