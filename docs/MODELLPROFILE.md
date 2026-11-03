# Modellprofile

Grundlage ist die bereitgestellte Datei **GPUstack Modelle (1).md**.
Ihre acht als „Ready“ bezeichneten Deployment-IDs wurden als Startkonfiguration
übernommen. Die Quelldatei ist selbst eine generierte Modellübersicht; ihre
Leistungsrangfolgen, Kontextgrößen und pauschalen Datenschutz-/Lizenzaussagen
werden nicht als verifizierte Fakten in die Anwendung übernommen.

| Deployment-ID aus der Datei | Startrolle im UI | Vor Ort prüfen |
|---|---|---|
| gpt-oss-120b | Chat: Text, Strukturierung, Code | Unterstützte Parameter, Ausgabe-/Kontextbudget, konkrete Quantisierung |
| qwen3.8-27b | Chat: Text | Exakte Modellidentität hinter dem Alias; Bildfähigkeit gegebenenfalls aktivieren |
| minimax-m2.7 | Chat: Text und Code | Exakte Gewichte/Version und Endpunktfähigkeiten |
| internvl3-8b-instruct | Chat: Text + Bild | Bildinput, Promptformat, Qualität bei Scans/Handschrift |
| qwen3-embedding-0.6b | Embeddings | Kontextlimit, Vektordimension, ggf. Instruktionspräfix |
| granite-embedding-107m-multilingual | Embeddings | Tokenlimit, Spracheignung, ggf. Query-/Passage-Präfix |
| jina-reranker-v2-base-multilingual | Reranking | /rerank-Route, Ergebnisformat, Lizenzprüfung durch zuständige Stelle |
| faster-whisper-large-v3 | Transkription | Audioformate, maximale Größe/Länge, API-Timeouts |

Die genannten nicht bereiten Modelle sind nicht als aktive Startprofile
eingetragen. Neu verfügbare IDs erscheinen nach einem Modelllistenabgleich als
„Nicht zugeordnet“, bis ihre Aufgabe im UI festgelegt wurde.

**Wichtige Konsequenzen:**

- Embedding- und Reranker-Modelle erscheinen nicht als Chatmodelle.
- Whisper ist ein eigener Transkriptionsweg unter Audio & Transkripte.
- Die Anwendung stellt keine Rangliste „bestes Modell“ auf.
- „In Modellliste“ ist keine Prüfung von Halluzinationsrate, Sicherheit oder
  rechtlicher Eignung.
- Modellname und Parameterzahl allein identifizieren ein Deployment nicht
  zuverlässig. Basisgewichte, Revision, Quantisierung, Serving-Backend und
  Inferenzparameter sollten institutionell dokumentiert werden.
- Für verlässliche Zahlenanalyse ist die Daten-/Codeausführung entscheidend.
  Ein RAG-Ausschnitt einer CSV ist kein Zugriff auf die komplette Tabelle.
- Embeddings und Reranking verbessern eine Quellenauswahl, garantieren aber
  weder Vollständigkeit noch Wahrheit.

Für einen ersten fachlichen Abnahmetest sind wenige bekannte Beispiele mit
prüfbaren Soll-Antworten sinnvoll: sauberes Textdokument, Scan mit bekannten
Feldern, mehrsprachiges Dokument und CSV mit absichtlich fehlenden Werten.

## Kontextreferenzen ab 0.1.5

Die UI ergänzt separat gekennzeichnete Konfigurationswerte aus aktuellen Herstellerquellen. Diese ersetzen keine Prüfung des tatsächlichen Deployments. Bekannte Kontext- und Outputlimits im Modellprofil eintragen; /models.max_model_len wird nur übernommen, wenn ausdrücklich vorhanden. Quellen und Zahlen: [Medien, Tokens und Audio](MEDIEN_AUDIO.md). Reasoning-Parser und verbose_json-Zeitsegmente benötigen Backendunterstützung.
