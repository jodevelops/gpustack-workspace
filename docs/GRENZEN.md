# Grosse Dokumente und Ressourcengrenzen

**Version 0.1.7 · 8. Oktober 2026**

Die frühere Meldung „Extrahierter Text übersteigt 1 Mio. Zeichen“ entstand
im lokalen Parser, bevor ein Modell angesprochen wurde. Dieselbe Grenze
stand zusätzlich im Importdienst. Sie sollte den kleinen PoC vor zu hohem
RAM-Verbrauch, sehr vielen Datenbankabschnitten und lang laufenden Parsern
schützen. Für normale grössere Tabellen war sie zu knapp und nicht einstellbar.
Das war eine lokale Anwendungsgrenze, keine Vorgabe von GPUStack oder eines Modells.

## Was jetzt möglich ist

Unter **Einstellungen → Ressourcengrenzen → Grenzen anzeigen und ändern**
die Werte anpassen und **Grenzen speichern** wählen. Die Einstellungen bleiben
im bestehenden Nutzerdatenordner über Neustarts und Updates erhalten.
Eine Änderung benötigt keinen Neustart. Sie ist während laufender Modell- oder
Dateioperationen gesperrt. „Vorgaben eintragen“ füllt die Standardwerte ein;
erst „Grenzen speichern“ übernimmt sie.

| Grenze | Bisher | Neue Vorgabe / Verhalten |
|---|---|---|
| Originaldatei, einschliesslich Audio | 25 MiB | 100 MiB; bis 2.048 MiB einstellbar |
| Extrahierter Text pro Datei | 1 Mio. Zeichen, Upload scheiterte | 20 Mio.; bis 200 Mio. einstellbar; bei Überschreitung vollständiges Original ablegen |
| PDF-Seiten | 300 | Kein pauschales Seitenlimit; optional wieder begrenzen |
| Excel-Zeilen je Blatt | 30.000 | Kein pauschales Zeilenlimit; optional wieder begrenzen |
| Entpackte DOCX/XLSX-Datei | 80 MiB | 512 MiB; bis 8.192 MiB einstellbar |
| Office-ZIP-Einträge | 5.000 | 50.000; Schutz vor extrem vielen internen Teilen |
| Parser-Laufzeit | 45 s; 35 s CPU unter Linux | 180 s; bis 3.600 s einstellbar; CPU unter Linux entsprechend begrenzt |
| Parser-RAM unter Linux | 768 MiB | 1.536 MiB; bis 16.384 MiB einstellbar |
| Neue Textabschnitte | 900 Zeichen | 1.800; 500–8.000 einstellbar; ca. 13 % Überlappung |
| RAG-Auszüge je Anfrage | 6 | 12; 1–100 einstellbar |
| Chatnachricht | 80.000 Zeichen | 500.000; bis 4 Mio. einstellbar |
| Systemprompt / Projektnotiz / Promptvorlage | 16.000 / 20.000 Zeichen | 200.000 pro Feld; bis 4 Mio. einstellbar |
| Eingabebudget eines neuen Chats | 24.000 Zeichen | 48.000; 0 deaktiviert diese Zeichenprüfung; alte Chats behalten ihre Werte |
| Höchstes auswählbares Eingabebudget | 240.000 Zeichen | 2 Mio.; lokale Obergrenze bis 16 Mio. einstellbar |
| Höchste auswählbare Ausgabetokens | 32.768 | 262.144; lokale Obergrenze bis 1.048.576 einstellbar; tatsächlich unterstützte Werte am Modell prüfen |
| Quellen / Skills je Chatfrage | 30 / 8 | 200 / 32; das Eingabebudget gilt zusätzlich |
| Bildauflösung je Datei | 24 Mio. Pixel | 50 Mio.; bis 80 Mio. einstellbar |
| Neue Bilder je Frage | 4 / 12 MiB | 8 / 32 MiB; bis 32 Bilder / 256 MiB einstellbar |
| Modellanfrage inkl. Bildverlauf | 24 MiB | 64 MiB; bis 512 MiB einstellbar |
| GPUStack-Lesezeitlimit | 180 s; Audio 600 s | 600 s; 30–3.600 s einstellbar |
| Dokumentvorschau | Nur erste 100 Abschnitte | 100 pro Seite, weitere Seiten zugänglich; API maximal 200 pro Seite |
| Lokaler Importordner | Nur erste 300 Einträge | Durchblätterbar, 200 pro Seite; Dateinamen-/Pfadsuche |
| Arbeitsraum-Backup | Max. 150 MiB Originale, ZIP im RAM | Keine feste Gesamtgrenze; ZIP und SQLite-Snapshot temporär auf Festplatte |
| Datenlabor-Laufzeit / RAM | 45 s / 768 MiB | 300 s / 2.048 MiB; bis 3.600 s / 16.384 MiB einstellbar |
| Datenlabor-Temporärspeicher | 64 MiB | 512 MiB; bis 4.096 MiB einstellbar; zählt zum Container-RAM |
| Datenlabor-Ausgabedateien | 32 MiB je Datei, 50 MiB gesamt | 100 MiB pro Datei und gesamt; gemeinsame Grenze bis 2.048 MiB einstellbar |
| Datenlabor-Code / Eingabedateien | 50.000 Zeichen / 20 Dateien | 500.000 Zeichen / 200 Dateien |
| Datenlabor-Textausgabe | 100.000 Bytes, still gekürzt | 1 Mio. Bytes; Kürzung ausdrücklich markiert; grosse Ergebnisse als Datei speichern |
| Embedding-Dimension | Max. 8.192 | Max. 65.536; Dimension muss innerhalb eines Indexes konsistent sein |
| Recherche-Metadatenauszug | 2.000 Zeichen, still gekürzt | 20.000; Kürzung ausdrücklich markieren; Originaleintrag verlinkt |

**MiB** bedeutet 1.048.576 Bytes. Die neue Oberfläche benennt die Dateigrenzen
entsprechend. Für Dateien gibt es kein zusätzliches pauschales Limit je Projekt
oder für die gemeinsame Library. Freier Festplattenspeicher bleibt erforderlich.
Sehr hohe Einlesegrenzen sind keine Zusage, dass jeder Rechner jede Datei so
verarbeiten kann. Der Parser lädt seinen extrahierten Text weiterhin in den RAM;
Tabellenzellen und PDF-Objekte können zusätzlich Speicher benötigen.
Unter Windows greift das Laufzeitlimit, aber hier kein Parser-RAM-Hardlimit.

## Die passende Arbeitsweise wählen

| Ziel | Vorgehen |
|---|---|
| Einzelne Stellen finden, Inhalte befragen | Datei im Projekt einlesen und im Chat als Quelle wählen; optional semantisch indexieren |
| Sehr grosse Originale zunächst behalten | Library → Verarbeitung → **Nur Original ablegen**; danach Datei hochladen |
| Grenze beim Einlesen erreicht | Original wird automatisch vollständig abgelegt. Werte in den Einstellungen anpassen und in der Library **Text erneut einlesen** wählen |
| Summen, Zeilenzahlen, Dubletten, Statistik über die ganze Tabelle | Vollständige CSV/XLSX im Datenlabor als Eingabe wählen und mit pandas/openpyxl rechnen; Docker-Runner muss eingerichtet sein |
| Eine lange Dokumentation vollständig zusammenfassen | Kapitel/Abschnitte nacheinander auswerten und die geprüften Ergebnisse zusammenführen; die RAG-Auszüge allein liefern keine Vollständigkeitsgarantie |
| Umfangreiches Programm verbessern | Gezielte relevante Dateien/Abschnitte bereitstellen; für Arbeit am gesamten Projekt den separat eingerichteten OpenCode-Workflow verwenden |
| Modellkontext reicht nicht für Verlauf und Quellen | Chat → Kontext → Parameter → Eingabebudget passend zum geprüften Deployment erhöhen; alternativ neues Gespräch oder weniger Auszüge |

**Projektablage und Chat-Upload verwenden dieselben Dateigrenzen.**
Ein Projektordner umgeht kein Grössenlimit. Die Alternative „Nur Original ablegen“
umgeht die Textextraktion: Das Original ist herunterladbar und als vollständige
Datenlabor-Eingabe verfügbar, hat aber keinen RAG-Index und wird nicht als
Chatquelle verwendet. Durch späteres Einlesen kann es durchsuchbar werden.

Bei Text-, Seiten-, Zeilen-, Office-, Zeit- oder Parser-RAM-Grenzen entsteht
**kein still gekürzter Teilindex**. Das Original bleibt unverändert und die
Oberfläche erklärt den Zustand. Ein ungültiges oder verschlüsseltes Format
wird beim normalen Einlesen weiterhin abgelehnt; es kann bewusst nur als
Original abgelegt werden. Eine Datei über der Uploadgrenze wird nicht gespeichert.

„Text erneut einlesen“ behält Datei-ID, Projektzuordnung, Hash und Original.
Erst nach erfolgreichem Einlesen wird der alte Index in einer Datenbanktransaktion
ersetzt. Bei einem Fehler bleibt er erhalten. Der semantische Index muss nach
erfolgreichem erneutem Einlesen neu erstellt werden; bei vorhandenem Index
weist die Oberfläche vorab darauf hin. Alte Chatbelege bleiben gespeichert.

## Was eine grössere Datei nicht automatisch ändert

Eine Datei mit 20 Mio. Zeichen wird nicht vollständig an das Chatmodell gesendet.
RAG sucht lokal und übergibt ausgewählte Abschnitte. Im Chat wird der tatsächliche
Umfang ausdrücklich angegeben. Ohne Texttreffer sind Dokumentanfänge eine
Stichprobe. Für Gesamtberechnungen sind solche Auszüge ungeeignet.

Das lokale Eingabebudget ist eine **Zeichenzahl**, kein Tokenizer. Verlauf,
Systemanweisungen, Projektnotizen, Skills und Quellen zählen gemeinsam.
Der Server kürzt den Verlauf nicht still. Das tatsächliche Token-Kontextfenster,
Bildtokens, erlaubte Dateigrössen für Whisper, Ausgabetokens und Requestlimits
in GPUStack können kleiner sein. Höhere lokale Grenzwerte vergrössern diese
Deployment-Eigenschaften nicht. Parameter je Modell vor Ort prüfen.

Neue Routinen können ein eigenes Eingabebudget und Ausgabetokens speichern.
Bestehende Routinen werden ohne Verlust ihres Inhalts migriert. Bei später
herabgesetzten Grenzen wird eine unzulässige Routine als Fehler markiert und
bleibt nicht dauerhaft im Zustand „Läuft“ hängen.

## Verarbeitung grosser Bestände

Uploads werden in Portionen auf Festplatte geschrieben. Parserergebnisse laufen
als UTF-8-Datei statt als grosse Windows-stdout-Ausgabe; der frühere Unicode-Fix
bleibt erhalten. Texte werden in Datenbankpaketen von 256 Abschnitten geschrieben.
UTF-8 sowie UTF-16/UTF-32 mit BOM und Windows-1252 werden unterstützt.

Die Textsuche lädt Treffer statt den gesamten Dokumentbestand.
Die semantische Suche scannt Vektoren in Paketen von 128 und hält nur die besten
Kandidaten. Das begrenzt RAM, ist aber weiterhin eine lineare Suche: sehr grosse
Sammlungen benötigen später einen eigenen Vektorindex und Hintergrundjobs.

Die Embedding-Indexierung sendet Pakete von 16 Abschnitten und speichert jedes
erfolgreiche Paket. Nach einer Unterbrechung setzt **Indexieren** an den fehlenden
Abschnitten fort. Nach Modell-/Endpunktwechsel ist ein neuer Index erforderlich.
Es gibt kein festes Gesamtzeitlimit für die komplette Indexierung; einzelne
API-Aufrufe haben das konfigurierte Zeitlimit. Grössere Abschnitte müssen in das
Embedding-Modell passen. Schon ein kleiner Fehler im Abschnittsformat kann die
Trefferqualität beeinflussen; längere Abschnitte sind keine Qualitätsgarantie.

Das Backup benötigt temporär freien Festplattenspeicher für Snapshot und ZIP.
Nach dem Download wird die temporäre Sicherung entfernt. Datenlabor-Ausgaben
und OS-Schlüssel sind weiterhin nicht im Backup enthalten. Für eine vollständige
Sicherung den Dienst beenden und den ganzen Nutzerdatenordner sichern.

## Bewusst beibehaltene Grenzen

- Namen/Titel sind kurze Metadaten: Projekte/Prompts/Routinen 100 Zeichen,
  Chats 140, sichere Dateinamen 160, Modellkennungen 160, Modellbeschreibungen
  200 und Projektbeschreibung 1.000. Dokumentinhalte gehören nicht in Titel.
- Verlaufssuche und Ordnerfilter: 200 Zeichen; Rechercheabfrage: 300.
  Die Textsuche nutzt höchstens 64 unterschiedliche Suchwörter aus einer Frage
  und weist auf diese Auswahl hin. Lange Texte besser als Datei ablegen.
- Recherche: acht Treffer je gewähltem Anbieter, HTTPS, höchstens zwei erlaubte
  Weiterleitungen, 25 Sekunden mit 10 Sekunden Verbindungsaufbau. Dies ist eine
  gezielte Metadatensuche, kein vollständiger Katalogexport oder Webcrawler.
  Lange Anbieter-Metadaten sind auf 20.000 Zeichen und Titel auf 2.000 begrenzt,
  mit Hinweis auf den Originaleintrag. Anbieterlimits bleiben zusätzlich bestehen.
- Modellparameter: Temperatur 0–2, Top P grösser 0 bis 1; sie richten sich nach
  dem OpenAI-kompatiblen Protokoll und den Fähigkeiten des Deployments.
- Routinen: 1–365 Tage Intervall, Ausführung nur bei laufendem Dienst;
  Startkontrolle etwa alle 30 Sekunden, keine sekundengenaue Zeitplanung.
- Runner: eine CPU, 64 Prozesse, kein Netzwerk, kein Host-Python-Fallback;
  Ergebnisdownloads nur für die vorgesehenen Dateitypen. Diese Isolationsgrenzen
  bleiben bestehen. Der temporäre Speicher zählt zum Container-RAM.
- GPUStack-Verbindungsaufbau: 15 Sekunden; SQLite-Wartezeit bei Schreibsperren:
  30 Sekunden. Die neuen Laufzeitwerte sind keine universellen Netz-Timeouts.
- Dateitypen bleiben PDF, DOCX, XLSX, CSV, TSV, TXT, MD, JSON, PNG/JPEG/WebP
  und die bisherigen Audioformate. Kein OCR, keine alte XLS- oder Makroausführung.
- Originale werden nicht automatisch von der KI verändert. Schreibbare
  Ergebnisdateien entstehen im freigegebenen Datenlabor unter `/output`.

## Update ohne Verlust der eigenen Startkonfiguration

**GPUStack-Arbeitsraum-Update-v0.1.7.zip** separat entpacken. Dienst beenden,
Nutzerdatenordner sichern und den Inhalt des Updates in den bestehenden
**gpustack-arbeitsraum**-Programmordner kopieren. Vorhandene Dateien ersetzen.
Das Paket enthält keine Startskripte, keinen Datenordner und keine Schlüssel.
Eine selbst angepasste `start.py` und feste `--data-dir`-Vorgabe bleiben erhalten.
Wie bisher einmal starten, Browser mit **Strg+F5** laden und Upload wiederholen.
Keine neuen Python-Abhängigkeiten nötig.

## Ergänzung 0.1.5: Medien und Tokens

Neue Chats verwenden 8.192 Ausgabetokens, gegebenenfalls das kleinere eingetragene Deployment-Limit. Bestehende Budgets bleiben erhalten. Die lokale Zeichenprüfung ist optional (0 = aus); tatsächlicher Modellkontext und Anfragegrössenlimits gelten weiterhin. Herstellerreferenzen und bekannte Deployment-Limits erscheinen getrennt. Ausführliche Erklärung: [Medien, Tokens und Audio](MEDIEN_AUDIO.md).

WebM-Aufnahmen werden ebenfalls unterstützt. Transkript-Arbeitsfassungen verwenden die eingestellte Text- und Anfragegrössengrenze; maximal 100.000 Zeitsegmente, 50 pro Editorseite. Protokollerstellung übergibt das vollständige Transkript; bei zu grossem Input keine stille Auswahl.

## Ergänzung 0.1.7: Websuche

Unter Ressourcengrenzen sind jetzt Websuchtreffer (5, bis 20), Zeit je Suche/Seite
(30 s, bis 120 s), Webseitenantwort (2 MiB, bis 16 MiB), Text je Seite
(8.000 Zeichen, bis 100.000) und optional gelesene Chat-Trefferseiten (3, bis 10)
einstellbar. Lange Seitentexte werden sichtbar als gekürzter Auszug markiert.

Feste Adaptergrenzen: 2 MiB JSON-Suchantwort, 300 Zeichen Suchtext, bei Brave
höchstens 75 Wörter. Das sind Suchparameter/Transportgrenzen, keine Dateiupload-
oder Modellkontextgrenzen. Webquellen zählen zum tatsächlichen Chatbudget;
Vorabprüfung holt keine neuen Webtreffer. [Weitere Angaben](WEBSUCHE.md).
