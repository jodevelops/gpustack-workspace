# Änderungen

## 0.1.9 — 3. November 2026

Das bisherige Ergänzungspaket 0.1.8 wird zu einem vollständig installierbaren
Repository ergänzt.

- `start.py`: Start ausschließlich auf localhost, Browser erst nach
  Serverbereitschaft, verständliche Startfehler, `--port`, `--data-dir`,
  `--no-browser`, `--check` und `--version`.
- `start.cmd`: Windows-Start per Doppelklick; bestehende virtuelle Umgebung
  oder bereits eingerichtetes Python verwenden, ohne automatischen Download.
- Fester Benutzerdatenordner für neue Installationen; vorhandene lokale
  Datenbanken sowie explizite Datenpfade bleiben nutzbar. Eine zweite Instanz
  mit demselben Datenordner wird blockiert.
- Geprüfte Python-Abhängigkeitslisten, optionale DOM-Testabhängigkeiten mit
  npm-Lockdatei und fiktive Beispieldateien.
- Fehlender Docker-Bauplan für das optionale Datenlabor mit pandas,
  openpyxl, python-pptx und matplotlib ergänzt.
- Reale Start-/Neustarttests für Datenhaltung und Instanzsperre ergänzt;
  Versionsanzeige und Installationsanleitung auf das vollständige Paket umgestellt.

Der Zugriff auf das institutionelle GPUStack-Deployment und der Docker-Lauf
müssen weiterhin in der jeweiligen Zielumgebung geprüft werden.
