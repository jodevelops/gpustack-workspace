# Prüfprotokoll

**Stand: 8. Oktober 2026 · Version 0.1.8**

## Tatsächlich durchgeführt

Testumgebung: Linux, Python 3.12, Node.js 24. Die Python-Hauptpakete sind in
requirements.txt mit den verwendeten Versionen festgehalten.

**Letzter vollständiger Python-Lauf (0.1.7): 126 API-/Datei-Integrationstests und 4 Starttests bestanden (130 insgesamt).**

Für 0.1.8 wurde der erweiterte DOM/API-Test erneut ausgeführt; die Änderung betrifft
Einrichtungshilfe, Dokumentation und Versionsanzeige.
Ein lokaler Testclient spricht die tatsächliche FastAPI-Anwendung und eine
temporäre SQLite-Datenbank an. GPUStack wird über einen HTTPX-Testtransport
simuliert. Es wurden keine institutionellen Daten und keine echten API-Schlüssel
verwendet.

| Prüffeld | Ergebnis |
|---|---|
| Host-, Herkunfts- und CSRF-Prüfungen | Fremde Hosts/Ursprünge und fehlendes Token werden zurückgewiesen |
| Schlüssel | Kein Schlüssel in Bootstrap-Antwort, SQLite oder Validierungsfehlern; Endpunktwechsel entfernt Sitzungsschlüssel |
| Speicherung | Projekte/Chats/Dokumente überstehen erneute Initialisierung; Backup enthält Datenbank und Originale |
| Löschen | Projektkaskade entfernt Dokumenteinträge, Textabschnitte und FTS-Einträge |
| Chat und Quellen | Streaming, Historie, wirksamer Systemprompt, eindeutige Quellenlabels und Export geprüft |
| Projektgrenzen | Quellenauswahl aus einem anderen Projekt wird zurückgewiesen |
| Modalitäten | Embedding nicht als Chatmodell; Bild an Textmodell abgewiesen; Vision-Format korrekt aufgebaut |
| RAG | Indexierung, hybride Suche, Reranker und Erkennung eines veralteten Index geprüft |
| Fehlerbehandlung | Abgebrochene/incomplete Streams werden nicht als erfolgreiche Antworten protokolliert |
| Kontextbudget | Zu große Eingabe wird ohne stilles Kürzen und ohne neue Nachricht abgewiesen |
| Recherche/Code | Ohne Freigabe bzw. Runner keine externen Such-/Ausführungsaktionen |
| Modelle/Prompts | Profile abgleichen, unbekannte IDs zuordnen, Vorlagen ändern und löschen |
| Routinen | Anlegen, unmittelbare Ausführung, Aktivierung/Pause, Ergebnis-Chat und Löschen |
| Lokaler Import | Traversal und Symlink außerhalb des freigegebenen Ordners blockiert |
| Dateiparser | DOCX, XLSX, Textdateien und Scan-PDF-Erkennung mit synthetischen Dateien |
| Audio | Erst expliziter Transkriptionsaufruf löst die Anfrage aus |
| Verlaufssuche | Nachrichtentext aus einem älteren Chat jenseits der letzten zwölf Gespräche gefunden |
| Endpunktvorgabe | UniBE-Adresse vorbelegt; gespeicherte/geleerte Konfiguration bleibt erhalten; Öffnen der Oberfläche löst keine GPUStack-Anfrage aus |
| Unicode-Import | Parserausgabe unter erzwungenem CP1252 und ASCII; TXT/DOCX/XLSX mit Minus, Emoji, griechischen und chinesischen Zeichen unverändert eingelesen; Originaldownload, Quellenablage und Modellpayload geprüft |

**4 Starttests bestanden (in den 130 Python-Tests enthalten).**
Ein verzögerter Start öffnet den Browser erst nach Serverbereitschaft. Ein
abgebrochener Start öffnet keinen Browser. Ein eigener Python-Prozess mit dem
tatsächlichen `start.py` wurde gestartet; nach der Bereitschaftsmeldung lieferte
die lokale Oberfläche HTTP 200 und die Datenbank war vorhanden. Bei einem
bereits belegten Port endet der Prozess mit Fehlerstatus, zeigt den Bindefehler
und meldet den Arbeitsraum nicht als bereit. Die Browseröffnung wurde dabei
simuliert; die HTTP-Prüfung lief über einen echten lokalen Socket unter Linux.

**Unicode-Fehler mit der beigefügten Datei reproduziert und behoben.**
Vor der Korrektur erzeugte der Parser für `html-tool-partial.txt` bei
`PYTHONIOENCODING=cp1252` exakt den gemeldeten Fehler für `\u2212` an Position 2009.
Die Datei selbst war gültiges UTF-8. Nach der Korrektur war der vollständige
extrahierte Text identisch mit dem UTF-8-dekodierten Original. Die Datei wird
nicht mit dem Quellcodepaket ausgeliefert. Ein tatsächlicher Windows-Lauf
steht weiterhin aus; die problematische Pipe-Kodierung wurde unter Linux
gezielt erzwungen.

**Rechercheadapter und Diagnose geprüft.**
Synthetische, dokumentationskonforme Antworten für Crossref, Wikidata,
GND/lobid und DataCite wurden durch den tatsächlichen Rechercheadapter
verarbeitet. Geprüft wurden erfolgreiche und leere Treffer, HTTP 403/429/503/400,
HTML statt JSON, ungültiges JSON/Schema, MediaWiki-Fehler bei HTTP 200,
Timeout, Verbindungs- und TLS-Fehler. Nur freigegebene HTTPS-Weiterleitungen
beim selben Anbieter werden verfolgt. Fehlende Freigabe, unbekannte Quelle
und fehlender Wikidata-Kontakt lösen keine externe Anfrage aus.
Kontaktvalidierung verhindert Steuerzeichen und Zugangsdaten im Kontaktlink.
Anfragen enthalten weder GPUStack-Authorization noch Cookies oder Projektdateien.

**Oberflächenabläufe im DOM-Test bestanden.**
Der tatsächliche Frontendcode läuft in jsdom; API-Aufrufe gehen über eine
Prozessbrücke an die lokale Anwendung. Geprüft wurden Navigation, Projekt- und
Promptformulare, Konfigurationsspeicherung, geleertes Schlüsselfeld nach dem
Speichern, ein kompletter Chat, Verlaufssuche, gesperrte Internetrecherche,
Routineanlage, deaktivierter Runner und OpenCode-Konfigurationsdialog.
Fremder HTML-Inhalt bleibt maskierter Text.
Neu geprüft: Recherchekontakt über das Formular speichern, vier Quellen
anzeigen, einen Wikidata-Treffer abrufen und als Projektdokument ablegen.
Ein Wechsel der Quellenauswahl nach dem Abruf verändert Quelle, Suchtext
und Abrufzeitpunkt des gespeicherten Treffers nicht.

Die optionale WebMCP-Funktion wurde in einem simulierten Registry-Kontext auf
gültige und ungültige Eingaben geprüft. Sie kann lediglich einen sichtbaren
Entwurf vorbereiten, keine Modellanfrage senden. Ein echter Browser mit
WebMCP-Unterstützung wurde nicht geprüft.

JavaScript-Syntaxprüfung und Python-Import/Kompilierung waren erfolgreich.

## Grosse Dokumente und Grenzen: zusätzliche Prüfungen

Echte lokale Parserläufe: CSV, TXT und XLSX mit mehr als 31.000 Zeilen und
1 Mio. Textzeichen; spätere Fundstelle über RAG an ein simuliertes Chatmodell
übergeben. 301-seitiges PDF ohne Textebene erfolgreich importiert. Ein bewusst
engerer PDF-/Text-/Office-Grenzwert archiviert das exakte Original ohne Teilindex.
Upload von 25 MiB + 1 Byte im Originalmodus erfolgreich; zu grosser Upload
bei 1-MiB-Vorgabe abgelehnt, temporäre Uploaddateien entfernt.

Parserzeitüberschreitung gezielt simuliert; Original bleibt erhalten.
Erneutes Einlesen nach Grenzänderung behält ID/Hash/Download; ein späterer
Fehler erhält den bestehenden Index. UTF-16/UTF-32 mit BOM und die bisherigen
UTF-8-/Unicode-Regressionen bestehen. Einstellungen sind nach erneuter
Initialisierung unverändert; ungültige Werte und Änderungen während eines
Dateivorgangs werden abgewiesen.

Indexierung nach einem simulierten Netzabbruch: erste 16 Abschnitte bleiben
indexiert, erneuter Aufruf sendet nur fehlende Pakete. Trefferanzahl und Hinweis
auf die Teilmenge werden geprüft. Dokumentvorschau und Importordner lassen
sich über die bisherigen Gesamtgrenzen hinaus durchblättern und durchsuchen.

Ein synthetisches, dünn belegtes 151-MiB-Original wurde durch den tatsächlichen
festplattenbasierten Backupweg gesichert; ZIP-Inhalt und anschliessende Entfernung
der temporären Sicherung geprüft. Lange Promptvorlage und Chatnachricht über
90.000 Zeichen funktionieren mit ausdrücklich höherem Chatbudget. Routinen
behalten ihr eigenes Budget; alte Schema-1-Routinen migrieren ohne Inhaltsverlust.
Recherchetexte über 2.000 Zeichen bleiben erhalten; die neue 20.000-Zeichen-Grenze
wird ausdrücklich gekennzeichnet.

Erweiterter DOM/API-Test: Grenzen über das Formular speichern, grosse Datei
im Chat automatisch als Original ablegen, Auswahl deaktiviert, nach Anpassung
in der Library erneut einlesen, Vorschauseite ab Abschnitt 101 öffnen, bewusst
nur ein Original hochladen. Diese Prüfungen sind keine visuelle Browser-Abnahme.

Die hohen konfigurierbaren Maximalwerte (z.B. 2 GiB Upload, 200 Mio. Textzeichen)
wurden nicht als Belastungsbenchmark auf einem Windows-Arbeitsplatz getestet.
Docker-Ressourcenwerte sind konfiguriert; weiterhin kein realer Containerlauf.

## Nicht als getestet ausgeben

- **Kein realer GPUStack-/VPN-Test.** Adresse, Schlüssel, Zertifikatskette und
  tatsächliche Modell-Deployment-Fähigkeiten waren nicht verfügbar.
- **Keine visuelle Browser-/Layout-Abnahme.** Die bereitgestellte Vorschauumgebung
  konnte den Python-Dienst nicht starten. DOM-Prüfungen sind kein Ersatz für
  einen gerenderten Browser-Test bei unterschiedlichen Fensterbreiten.
- **Kein Windows-/DPAPI-Test.** Der Windows-Startweg und Keyring-Anschluss sind
  implementiert, aber hier nur unter Linux untersucht.
- **Kein Docker-Containerlauf.** Docker ist hier nicht verfügbar. Der Aufruf und
  seine Grenzen sind implementiert; die reale Isolation und Artefakterzeugung
  brauchen einen Lauf in eurer Umgebung.
- **Keine reale Audioerkennung und keine gemessene RAG-Qualität.** Tests prüfen
  Transport/Format und Persistenz, nicht die Qualität eines Modells.
- **Kein erfolgreicher Live-Recherchetest aus dieser Ausführungsumgebung.**
  Direkte öffentliche Testanfragen an Wikidata, Crossref und lobid liefen hier
  in Zeitüberschreitungen. Die Schnittstellendokumentation wurde über Websuche
  geprüft; lobid lieferte dort eine Zugriffsschutzseite. Das ist kein Nachweis
  einer allgemeinen Störung oder der konkreten Ursache im institutionellen Netz.
  Die Adaptertests verwenden simulierte Antworten. Live-Zugang vor Ort prüfen.
- **Keine echte OpenCode-Ausführung.** Es handelt sich um einen
  Konfigurationsexport, keinen integrierten Agenten.
- **SSO ist nicht implementiert.** Keine SSO- oder Mehrbenutzerabnahme möglich.
- **Keine formelle Datenschutz-, Sicherheits- oder Barrierefreiheitszertifizierung.**

## Kurze Abnahme vor Ort

1. Anwendung unter Windows starten, dann mit 100 % und 200 % Zoom bedienen.
   Navigation, Dialoge, Quellenpanel und Downloads auch bei schmalem Fenster
   prüfen. Durchgehend per Tastatur testen.
2. Nicht vertrauliche Testdatei hochladen, Dienst beenden und neu starten.
   Chat, Datei und Projektnotizen müssen erhalten bleiben.
3. VPN verbinden, gültigen API-Schlüssel setzen, Modellliste laden und eine
   kurze Inferenz je verwendetem Chatmodell ausführen.
4. VPN gezielt trennen: nachvollziehbare Fehlermeldung, kein Verlust des
   Eingabetextes und kein vorgetäuschter Erfolg.
5. Ein bekanntes Bild mit dem Vision-Modell prüfen. Kontext- und
   Ausgabelimits anhand des echten Deployments einstellen.
6. Beispielquelle indexieren. Embedding- und Rerank-Aufrufe in GPUStack
   prüfen; Quellenauszüge mit dem Original vergleichen.
7. OS-Schlüsselspeicher aktivieren, Dienst neu starten und Zugriff prüfen.
   Danach Schlüssel entfernen und GPUStack-seitig bei Bedarf widerrufen.
8. Recherche nur mit einem öffentlichen Testbegriff freigeben.
9. Falls benötigt, Docker-Runner bauen und die beiden Vorlagen mit
   Beispieldaten ausführen. XLSX/PPTX öffnen. Netzwerk- und Dateisystemgrenzen
   separat überprüfen.
10. Grössere CSV/XLSX hochladen und bekannte Werte vom Dateiende suchen.
    RAG-Auszüge von vollständigen Tabellenberechnungen unterscheiden.
11. Backup erzeugen und in einem separaten Datenordner wiederherstellen.
    Erst nach erfolgreicher technischer und institutioneller Abnahme
    freigegebene reale Daten verwenden.

## Erweiterung 0.1.5

| Prüffeld | Durchgeführt |
|---|---|
| Medien | Inline-Routen für Bild, PDF, WebM; private Anhangreferenzen bleiben im Chat; Scan-PDF als reine Vorschau wird nicht als Modellquelle gesendet; fremdes Projekt blockiert |
| Reasoning | Strukturierte Felder und über Chunks geteilte think-Marker; Literal im normalen Antworttext bleibt sichtbar; Teilbegründung bei Fehler erhalten; keine erneute Übermittlung in Folgeanfragen |
| Export | Reasoning standardmässig weder in MD noch JSON; opt-in enthält den gelieferten Text; length-Abbruch gekennzeichnet |
| Tokens | Herstellerreferenz getrennt von Deployment; char budget=0 funktioniert; lokale Nutzungsprüfung ohne Inferenz; bekannte Ausgabelimits durchgesetzt; Usage optional und serverseitige Kontextfehler ohne private Payload klassifiziert |
| Transkripte | Modell/Format explizit; Original unverändert; Arbeitsfassung und Version erhalten; veraltetes Update blockiert; MD/JSON und separate Projektquelle; gelöschtes Audio entfernt nicht das Transkript |
| Protokoll | Vollständiger Quelltext statt Ausschnitten; fehlende Angaben im Auftrag offen; Kontextüberschreitung ohne stilles Kürzen; Änderungen markieren bestehenden Entwurf als veraltet |
| DOM-Abläufe | Beide Kontextschalter und aria-expanded; Medienkarten und grosser Dialog; Reasoning-Exportwahl; Aufnahme-FSA-Reihenfolge Picker → Mikrofon → Schreiben → Close → File → eigener Upload; Audio-Inferenz erst nach Klick; Editor, Seek, Protokoll und Browserfallback |

MediaRecorder, Mikrofon, File-System-Access-API und Audio-Playback wurden im DOM-Test simuliert. Dieser Test bestätigt Ablauf und API-Verknüpfung, keine reale Aufnahme oder Browserdarstellung. PDF-Rendering, echter Windows-Dateipicker, UniBE-GPUStack, VPN und Transkriptionsqualität vor Ort abnehmen. Automatische Diarisierung ist nicht installiert; Import und manuelle Zuordnung sind implementiert. Bestehende Migrationsprüfung erwartet nun SQLite-Schema 3.

## Korrekturen 0.1.6

Erneut durchgeführt: **88 Python-Tests bestanden**, JavaScript-Syntaxprüfung und
der erweiterte DOM/API-Integrationstest bestanden. Kein neuer Live-/Browsertest.

| Fehlerfall | Geprüftes Ergebnis |
|---|---|
| Verzögerte PUT-Antwort, neue Notiz während Speicherung, erneuter Klick | Neue Notiz bleibt im Editor und in SQLite; Speicherkette verwendet die aktualisierte Version |
| Notiz editiert, Oberfläche neu gerendert, MD heruntergeladen | Download enthält aktuelle Unicode-Notiz; Speicherung erfolgt vor Export |
| Änderung im anderen Fenster vor JSON-Download | 409; lokaler Entwurf bleibt; JSON-Entwurf enthält lokale Notiz; bewusstes Neuladen öffnet gespeicherte Fremdfassung |
| Export / Projektquelle mit älterer Versionsnummer | 409; keine zusätzliche Projektquelle angelegt; richtige Version enthält aktuelle Notiz, Original bleibt unverändert |
| Chat aus anderem Projekt öffnen | Edits gespeichert; Audio-Editor/Transkriptliste gehören zum Zielprojekt; unübernommene Aufnahme blockiert Wechsel |
| Änderung nach Token-Prüfung / während verzögerter Antwort | Alte Schätzung entfernt; spätes Ergebnis wird verworfen |

Die simulierten Antwortverzögerungen prüfen Datenfluss und Persistenz. Reale
Windows-Dateidialoge, Mikrofon, GPUStack, VPN und gerendertes Layout bleiben
vor Ort zu prüfen.

## Erweiterung 0.1.7: Websuche

**130 Python-Tests bestanden**, davon 42 neue Webtests; erweiterter DOM/API-Test
und JavaScript-Syntaxprüfung bestanden.

| Prüffeld | Ergebnis |
|---|---|
| SearXNG / Brave | Parameter, Filter, Datenformat, Duplikate, Fehler-/Redirect-/Timeoutfälle und Antwortgrössen über MockTransport |
| Schlüssel | Brave-Schlüssel getrennt von GPUStack; Session, OS-Vault-Mock und Umgebung; keine Rückgabe in Bootstrap, Settings oder Backup |
| Datenwege | Nur expliziter Suchtext an Suchadapter, kein privater Chat-/Projekttext; private Quellen bleiben im GPUStack-Payload |
| Webseiten | HTML-Extraktion, Unicode/Charset, robots-Verbot, sichere Redirects, finale URL, private/IP-/Credential-Ziele blockiert, PDF-Hinweis |
| Netzwerk | Gemischte private/öffentliche DNS-Antwort blockiert; geprüfte IP im Socket-Mock verwendet; ursprünglicher TLS-Hostname bestätigt; Reader-Bytegrenze und fehlende Auth-/Cookie-Header geprüft |
| Chat | W/Q-Labels eindeutig im Verlauf, Quelle/Query/URL/Abruf im Export; leere Suche blockiert Modell; Seitenfehler als Snippet-Fallback bezeichnet; Kontextbudget auch mit Webquellen |
| Abbruch | Verbindungsabbruch vor Modellstart beendet Suche und gibt Thread frei; UI stellt noch nicht gesendete Frage wieder her |
| UI | Anbieter konfigurieren, Websuche ausführen, Textvorschau/Projektquelle, Chat-Webschalter, Quellenmodal, Antwortdownload mit URL |

Echte Webseitenverbindung versucht: `docs.searxng.org/dev/search_api.html`.
Die DNS-Auflösung scheiterte in dieser Ausführungsumgebung. Kein erfolgreicher
Live-Seitenabruf, kein echter Brave-Schlüssel/SearXNG-Zugang, kein neuer Windows-
oder visueller Browser-Test. Die offizielle API-Dokumentation wurde über den
Recherchezugang geprüft; das ist getrennt vom nativen App-Netzwerk.


## Einrichtungsanleitung 0.1.8

Lokaler Einrichtungsdialog unter Einstellungen und Recherche ergänzt; ausführliche
Anleitung über die vorhandene lokale StaticFiles-Route als Markdown verfügbar.
Brave-Konto, Web-Search-Tarif, Schlüssel, Kostenkontrolle und Speicherrechte
anhand offizieller Dokumentation geprüft. SearXNG: Basis-URL, JSON-Format,
IT-Einrichtung, Netzwerk und typische Fehler erklärt.

Validierung: JavaScript-Syntax und erweiterter DOM/API-Test. Der Dialog und die
Anbieterauswahl lösen keine Suche oder Konfigurationsspeicherung aus; ungespeicherte
Schlüssel bleiben im Formular, erscheinen nicht in der Hilfe und werden nicht
übertragen. Download liefert die lokale Anleitung. Der letzte vollständige
Python-Testlauf aus 0.1.7 bestand mit 130 Tests; die Rechercheimplementierung
ist in 0.1.8 unverändert. Keine Live-Anbieter-, Windows- oder visuelle Layout-Abnahme.
