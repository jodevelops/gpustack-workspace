# Medien, Modellbegründungen, Tokens und Audio

**Version 0.1.7 · 8. Oktober 2026**

## Vorhandene Installation aktualisieren

1. Unter Einstellungen den tatsächlich verwendeten Datenordner prüfen und eine Sicherung herunterladen. Datenlabor-Ausgaben separat sichern.
2. Dienst im Terminal mit Strg+C beenden. Falls eine weitere Instanz läuft, diese ebenfalls regulär beenden.
3. **GPUStack-Arbeitsraum-Update-v0.1.7.zip** separat entpacken und die enthaltenen Dateien in den bestehenden Programmordner `gpustack-arbeitsraum` kopieren. Insbesondere die neuen Dateien **app/transcripts.py** und **web/audio.js** übernehmen.
4. Wie bisher starten und Browser mit **Strg+F5** vollständig neu laden. Einstellungen zeigt Version **0.1.7** in der Bootstrap-Antwort; die Navigation enthält **Audio & Transkripte**.

Das Update enthält keine Startskripte, requirements-Dateien oder Nutzerdaten. Deine angepasste `--data-dir`-Vorgabe bleibt bestehen. Keine neuen Python-Abhängigkeiten. Die Datenbank wird beim Start um eine Transkripttabelle erweitert; bestehende Chats, Projekte und Originale bleiben erhalten. Gleichen Datenordner wie bisher verwenden, sonst öffnet sich ein anderer Arbeitsraum.

## Bilder und PDFs anzeigen

Im Chatentwurf erscheinen Vorschaubilder bzw. PDF-Karten. Draufklicken öffnet das Original in einem grossen Dialog. Auch im gespeicherten Chat bleiben die Dateireferenzen sichtbar. Zusätzlich funktioniert dies in der Library über das Augensymbol.

PDFs verwenden den lokalen PDF-Viewer des Browsers, ohne CDN oder externe PDF-Dienste. Falls der Browser keine eingebettete Anzeige erlaubt, **Separat öffnen** oder **Original herunterladen** wählen. Bildansicht passt sich dem Dialog an; separat öffnen erlaubt die Zoomfunktionen des Browsers. Nach Löschen des Originals bleibt im Chat ein Hinweis, die Vorschau ist dann nicht mehr verfügbar.

Ein Scan-PDF kann angezeigt werden, obwohl es keine lesbare Textebene hat. Solche Anhänge sind **nur Vorschau** und gehen nicht als Textquelle an das Modell. Ebenso wird bei einem Text-PDF nur die gewählte RAG-Auswahl übergeben, nicht automatisch das gesamte visuelle PDF. Bilder gehen nur nach Auswahl an ein als bildfähig freigegebenes Modell. OCR ist weiterhin eine separate Aufgabe.

## Gelieferte Begründung / CoT

Der Arbeitsraum zeigt **tatsächlich vom Endpunkt ausgegebenen Reasoning-Text** in einem aufklappbaren Bereich. Unterstützt sind die Streamfelder `reasoning_content`, `reasoning` und ein ausdrücklich mit `<think>…</think>` markierter Block am Anfang des Antworttexts, auch über Chunkgrenzen hinweg. Ohne solche Daten erscheint der Hinweis, dass kein separater Reasoning-Text geliefert wurde.

Das ist keine Garantie, dass alle internen Modellabläufe sichtbar oder die Begründungen fachlich korrekt sind. Die Anwendung kann nichts ausgeben, das GPUStack nicht liefert. Gegebenenfalls muss die IT einen zum Modell passenden Reasoning-Parser im Serving-Backend konfigurieren. Der Arbeitsraum aktiviert keinen unbekannten Parser und sendet keine geratenen Backendparameter.

Reasoning wird separat mit der Antwort lokal gespeichert, auch bei Teilantworten und Fehlern. Bei Folgefragen wird nur der eigentliche Antworttext erneut übergeben. Im **Chat-Export** und beim **Antwort-Download** wählst du, ob die Begründung enthalten sein soll. Standard: **aus**, sowohl für Markdown als auch JSON. Eine vollständige Arbeitsraumsicherung enthält die Datenbank und damit gespeicherte Reasoning-Texte; sie ist kein bereinigter Chat-Export.

## Tokenparameter verstehen

| Anzeige | Bedeutung |
|---|---|
| Herstellerreferenz | Mitgelieferte Konfiguration eines passenden Referenzmodells, mit Quelle und Prüfdatum. Die Deployment-ID allein beweist die Zuordnung nicht. |
| GPUStack-Deployment | Tatsächlich eingetragenes oder ausdrücklich über `/models` als `max_model_len` gemeldetes Kontextlimit. Unbekannte Werte bleiben unbekannt. |
| Deployment-Ausgabelimit | Separates serverseitiges Maximum, falls bekannt und manuell eingetragen. Sonst unbekannt. |
| Maximale Ausgabetokens | Budget dieser Antwort. Je nach Modell / Backend werden auch Reasoning-Tokens daraus bezahlt. |
| Eingabebudget in Zeichen | Optionale lokale Prüfung der zusammengestellten Texteingabe. **0 deaktiviert diese Prüfung.** |
| Lokale Ressourcenmaxima | Grenzen des PoC für RAM, Verarbeitung und Anfragegrösse; kein Beleg für die Kontextfähigkeit eines Modells. |

**Input und Ausgabe teilen das Modellkontextfenster.** Mehr gewünschte Ausgabe lässt weniger Platz für Input. Bildtokens, Chat-Templates und Backendbesonderheiten kommen hinzu. Ein Herstellerwert ist keine Zusage für eure GPUStack-Konfiguration, die wegen Serving-Einstellungen oder Speicher kleiner sein kann.

Unter **Einstellungen → Modellprofile → Bearbeiten** bekannte Deployment-Kontexttokens und ein separates Ausgabelimit eintragen. Leere Felder bedeuten unbekannt. Die Oberfläche und das Backend verhindern Ausgabewerte oberhalb eingetragener Deployment-Limits. Bei einem Endpunktwechsel werden Deployment-Limits, Erreichbarkeitsstatus und optionale Stream-Usage-Freigabe zurückgesetzt: sie gehören zum bisherigen Server und müssen neu geprüft werden.

Die Herstellerreferenzen sind eingebündelt; das Öffnen der Parameter löst keine Internetrecherche aus:

| Deployment-ID | Konfigurationswert `max_position_embeddings` | Primärquelle, geprüft 07.10.2026 |
|---|---:|---|
| gpt-oss-120b | 131.072 | [OpenAI-Konfiguration](https://huggingface.co/openai/gpt-oss-120b/blob/main/config.json) |
| qwen3.8-27b | 262.144 | [Qwen-Konfiguration, text_config](https://huggingface.co/Qwen/Qwen3.8-27B/blob/main/config.json) |
| minimax-m2.7 | 204.800 | [MiniMax-Konfiguration](https://huggingface.co/MiniMaxAI/MiniMax-M2.7/blob/main/config.json) |
| internvl3-8b-instruct | 32.768 | [InternVL3-8B-Konfiguration, llm_config](https://huggingface.co/OpenGVLab/InternVL3-8B/blob/main/config.json) |

Dies sind Konfigurationsreferenzen, keine Messungen am UniBE-Endpunkt. RoPE-Erweiterungen, andere Gewichte hinter dem Alias und separate Hosting-Angebote können andere Werte haben. Die frühere generierte Modellübersicht wird dafür nicht als Beleg verwendet.

### Lokale Zeichenprüfung ausschalten oder erhöhen

**Kontext → Parameter → Eingabebudget in Zeichen = 0 → Einstellungen speichern.** Bei einem neuen Chat reicht die Auswahl vor dem Senden. Alternativ einen höheren Wert einstellen; das lokale einstellbare Maximum steht unter **Einstellungen → Ressourcengrenzen**.

Die Zeichenprüfung dient dazu, unabsichtlich grosse Verläufe früh zu erkennen. Für die Modellfunktion ist sie nicht zwingend. Ihr Abschalten entfernt weder das tatsächliche Kontextlimit noch die Request-Grössen-, Nachrichten-, Datei- oder Zeitgrenzen. Der Verlauf wird weiterhin nie still gekürzt. Die lokale Ausgabetoken-Obergrenze ist standardmässig 262.144 und bis 1.048.576 einstellbar; bei den mitgelieferten Referenzmodellen liegt sie bereits über deren gesamtem Konfigurationskontext.

Neue Chats starten mit **8.192 Ausgabetokens** bzw. einem kleineren eingetragenen Deployment-Limit und weiterhin **48.000 Zeichen** als anfänglicher Prüfung. Bestehende Chats behalten ihre Werte. Ein bewusst deaktiviertes Budget bleibt über Neustarts erhalten.

**Eingabe lokal prüfen** baut Verlauf, Anweisungen und ausgewählte Quellenauszüge ohne Modellanfrage zusammen. Der Chat und seine Parameter werden dazu gespeichert, keine Nachricht. Die Texttokenzahl ist eine grobe Schätzung aus Zeichen (2–5 Zeichen/Token), die insbesondere bei Code, Unicode oder anderen Sprachen stark abweichen kann. Kein lokaler Modelltokenizer; keine zuverlässige Vorhersage von Bildtokens. Bei semantischer Suche kann die spätere Quellenauswahl abweichen.

Exakte vom Server gelieferte `usage`-Werte erscheinen unter der Antwort. Optional im Modellprofil **Tokenverbrauch im Stream anfordern** einschalten, wenn das Backend `stream_options.include_usage` unterstützt. Unbekannte Backendfunktionen werden nicht automatisch angefordert.

### Antwort endet zu früh

Bei `finish_reason=length` erscheint ein klarer Hinweis, auch im Export. Reasoning kann das Budget verbrauchen, bevor eine eigentliche Antwort entsteht. Dann wird die gelieferte Begründung erhalten und das fehlende Antwortbudget sichtbar.

Ausgabebudget erhöhen und erneut fragen; dabei den verfügbaren Kontext beachten. Sehr grosse Verläufe besser in Themen / neue Threads gliedern. Für Gesamtauswertung grosser Tabellen das Datenlabor nutzen. Der Arbeitsraum setzt abgeschnittene Antworten nicht automatisch mit weiteren Modellanfragen fort.

## Audio: erst aufnehmen und speichern, dann hochladen

1. **Audio & Transkripte → Aufnehmen & Speicherort wählen**. In aktuellen unterstützenden Edge-/Chrome-Versionen wird zuerst ein Dateispeicherort gewählt, erst danach das Mikrofon freigegeben.
2. Aufnahme läuft mit fortlaufendem Schreiben in die gewählte Datei. **Stoppen & Datei fertig speichern** schliesst die Datei und gibt das Mikrofon frei.
3. Aufnahme bei Bedarf lokal im Player anhören. **Gespeicherte Aufnahme ins Projekt übernehmen** kopiert die fertige Datei in den Arbeitsraum. Noch keine Modellanfrage.
4. Modell, Sprache und Ausgabeformat auswählen. **An GPUStack senden & transkribieren** startet erst jetzt die API-Anfrage.

Ohne `showSaveFilePicker` bietet die Oberfläche eine Aufnahme zum Download an. Nach dem Download die gespeicherte Datei über **Gespeicherte Datei wählen** auswählen. Der Browser kann einen erfolgreichen Dateidownload nicht zuverlässig bestätigen; deshalb wird die Aufnahme aus dem Arbeitsspeicher nicht automatisch hochgeladen. Datei gegebenenfalls vor Browserabschluss sichern.

Verwendete Formate: WebM/Opus, alternativ je nach Browser MP4/M4A oder Ogg. Die vorhandenen Uploadformate WAV, MP3, M4A, MP4, Ogg bleiben bestehen. GPUStack bzw. das Whisper-Backend muss das konkrete Format verarbeiten können. Falls nötig vor Ort lokal in WAV umwandeln; kein externer Konvertierungsdienst ist eingebaut.

Die Aufnahme stoppt an der lokalen Uploadgrenze, statt beliebig im Browser-RAM weiterzulaufen. Ein letzter Chunk kann die Grenze geringfügig überschreiten; dann vor Übernahme die Grenze erhöhen oder Aufnahme teilen. Aufnehmen benötigt Mikrofonfreigabe und ein unterstütztes Browserumfeld auf localhost. Navigation während aktiver Aufnahme verhindert einen versehentlichen Projektwechsel. Aufnahmefehler / Schreibfehler werden angezeigt; kein automatischer Upload.

## Transkripte und Protokolle bearbeiten

Alle freigegebenen **Audio-Modellprofile** stehen im Dropdown. Weitere tatsächlich bereitgestellte Whisper-Modelle in den Einstellungen zuordnen. Die Anfrage verwendet `/audio/transcriptions` am konfigurierten GPUStack-Endpunkt.

- **Text (kompatibel)** funktioniert auch mit einfachen Backends. Keine Zeiten werden erfunden.
- **Mit Zeitsegmenten (verbose_json)** fordert Segmentzeiten an. Unterstützt das Deployment dieses Format nicht, nach Fehlermeldung bewusst mit Text wiederholen. Keine stille zweite Audioübertragung.

Originalantwort samt gelieferter Segment-/Wortdaten bleibt unverändert in SQLite. Das ursprüngliche TXT wird ebenfalls als Projektquelle gespeichert. Die Arbeitsfassung kann separat bearbeitet werden, mit Versionsprüfung gegen überschreibende parallele Änderungen.

Bei Zeitsegmenten: Start/Ende in Sekunden korrigieren, Sprecherlabel ergänzen, Text nachbearbeiten. Zeitbutton startet den Player am Segment. **Zeit und Sprecherzuordnung durch Abhören geprüft** erst nach Prüfung setzen; weitere Segmentänderungen entfernen diese Bestätigung. Überlappungen sind zulässig. Grosse Transkripte zeigen 50 Segmente pro Seite; maximal 100.000 Segmente, darüber Aufnahme aufteilen.

Freitextbearbeitung entfernt die Zeitsegmente nur aus der Arbeitsfassung. Originaldaten bleiben erhalten. Import von Zeitsegmenten ersetzt die Arbeitssegmente, nicht das Original. Vor Import bei Bedarf die aktuelle Arbeitsfassung exportieren.

**Änderungen lokal speichern** speichert den Entwurf. Vor Navigation / Modellanfrage wird ein geänderter Entwurf ebenfalls lokal gespeichert; fehlgeschlagene Speicherung verhindert diesen Schritt und lässt den Entwurf stehen. Beim Browserabschluss mit ungespeicherten Änderungen erscheint die Browserwarnung. Ein Browserabsturz kann noch ungespeicherte Änderungen verlieren.

### Diarisierung und verlässliche Zeiten

Whisper allein ist kein garantierter Diarisierungsdienst. Vorschlag: **WhisperX mit Alignment und pyannote** als separater lokaler IT-Dienst; Modellgewichte, Berechtigungen und Offline-Betrieb vorher bereitstellen. [Projekt und Anleitung](https://github.com/m-bain/whisperX), [Publikation](https://arxiv.org/abs/2303.00747). Dieser zusätzliche ML-Dienst ist hier nicht installiert.

Ein solcher Dienst kann JSON ausgeben, das über **Zeitsegmente / Diarisierung importieren** übernommen wird:

```json
{
  "segments": [
    {"start": 0.0, "end": 2.5, "text": "Guten Morgen.", "speaker": "SPRECHER_01"},
    {"start": 2.6, "end": 5.0, "text": "Wir beginnen mit dem Bericht.", "speaker": "SPRECHER_02"}
  ]
}
```

Zeiten relativ zum Beginn genau dieser Aufnahme, sortiert nach Startzeit. Sprecherlabels identifizieren Stimmen, keine bestätigten Personen. Importierte Angaben gelten zunächst als ungeprüft. Quelle / Verfahren in Prüfnotizen dokumentieren; kritische Stellen abhören. Auch Alignment ist keine Garantie fehlerfreier Zeiten.

### Meeting-Protokoll als Markdown

Titel, Datum, Teilnehmende, Agenda und Prüfnotizen ergänzen. Ein lokales Chatmodell auswählen, Outputbudget setzen, dann **Gespeichertes Transkript an Modell senden**. Der Arbeitsraum übergibt die vollständige Arbeitsfassung; kein RAG-Sampling und kein stilles Kürzen. Überschrittene Zeichen-/Anfragegrenzen oder GPUStack-Kontextfehler werden angezeigt. Lange Aufnahmen gegebenenfalls nach Traktanden teilen.

Der Modellauftrag umfasst Kurzüberblick, Themen/Ergebnisse, Beschlüsse, Aufgaben mit Verantwortlichen/Fristen/Belegen, offene Fragen und nächste Schritte. Nicht genannte Angaben sollen offenbleiben. Der Entwurf ist keine verifizierte Feststellung; manuell nachbearbeiten und mit Audio abgleichen. Nach Änderungen an der Transkriptquelle zeigt die App, dass ein bestehendes Protokoll erneut abgeglichen werden muss.

**MD herunterladen** speichert die sichtbaren Änderungen zuerst und bündelt Metadaten, Protokollentwurf, Prüfnotizen und bearbeitetes Transkript inklusive vorhandener Zeiten und Sprecherlabels. Der JSON-Export speichert ebenfalls zuerst und enthält zusätzlich das unveränderte Original. Downloads und Projektquellen prüfen die gewünschte Version; bei einer zwischenzeitlichen Änderung wird eine Fehlermeldung angezeigt. **Als Projektquelle speichern** erstellt einen separat datierten Stand für die Library/RAG; spätere Transkriptänderungen ändern diese Quelle nicht automatisch.

## Sicher speichern und Konflikte lösen (0.1.6)

Während einer manuellen Speicherung darf weiter editiert werden. Hinzugekommene
Änderungen werden danach gegen die neue Version gespeichert; wiederholte Klicks
auf Speichern teilen denselben Speichervorgang. Beim Verlassen des Editors wird
eine laufende Speicherung abgewartet. Ein Download sperrt den Editor kurz,
speichert die sichtbare Arbeitsfassung und exportiert genau diese Version.
Schlägt Speichern oder Download fehl, bleibt der Entwurf im Editor erhalten.

Bei einer Änderung in einem zweiten Fenster verhindert die Versionsprüfung das
Überschreiben. Der Konfliktdialog bietet **Entwurf als JSON sichern** und
**Gespeicherte Fassung laden**. Beim Laden werden die ungespeicherten Eingaben
ersetzt. Deshalb zuerst sichern, wenn sie noch benötigt werden. Die Entwurfs-
JSON enthält die sichtbare Arbeitsfassung mit Projekt/ID/Version; sie ist eine
Sicherung zum manuellen Abgleich, kein automatisch importierbarer Vollbackup.
Die beiden Befehle sind auch direkt am Editor verfügbar.

Ein Chat aus einem anderen Projekt wechselt nun auch die Transkriptliste und
den Editor. Eine noch nicht übernommene Aufnahme verhindert den Projektwechsel,
bis sie importiert oder ihre Vorschau bewusst geschlossen wurde.

Die lokale Eingabeprüfung gilt für den zuletzt geprüften Stand. Änderungen an
Nachricht, Parametern, Anweisungen, Quellenauswahl oder Verlauf löschen die alte
Schätzung. **Eingabe lokal prüfen** berechnet sie erneut; verspätete Ergebnisse
für einen inzwischen geänderten Stand werden verworfen.

## Abnahme vor Ort

Automatisierte Linux-Tests verwenden synthetische Medien und einen simulierten GPUStack-Endpunkt. Aufnahme-, Speicher- und Player-APIs wurden in DOM-Tests simuliert. Kein Test des realen Mikrofons, institutionellen VPN, Windows-Dateipickers, GPUStack-Whisper, tatsächlicher PDF-Browserdarstellung oder Diarisierungsqualität.

Für den ersten Versuch: kurzes nicht vertrauliches Testaudio speichern, im Player prüfen, mit dem gewählten Modell transkribieren, bei Bedarf verbose_json testen, einen Sprecher manuell ergänzen und MD herunterladen. Bekannte PDF/Bilddatei öffnen, Reasoning-Lieferung je Chatmodell kontrollieren und echten Deployment-Kontext mit der IT eintragen.

Allgemeine Websuche ist ab 0.1.7 zusätzlich verfügbar: [Websuche](WEBSUCHE.md).
