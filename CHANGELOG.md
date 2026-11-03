# Änderungen

## 0.1.10 — 3. November 2026

- Grafischer Windows-Starter mit Einrichtung, Fortschritt, kopierbarem Protokoll,
  Desktop-Verknüpfung und Beenden; der normale Start benötigt keine Terminalbefehle.
- `start.cmd` öffnet das Startfenster ohne dauerhaftes Konsolenfenster.
  `start-debug.cmd` erhält den bisherigen Konsolenstart für Diagnosen.
- Vorhandene Python-Installation oder virtuelle Umgebung wiederverwenden.
  Paketinstallation erst nach explizitem Klick auf **Einrichten und starten**;
  Benutzerinstallation bzw. bestehende virtuelle Umgebung, ohne Administratorinstallation.
- Arbeitsraum nach Serverbereitschaft in einem Edge-/Chrome-App-Fenster oder
  dem Standardbrowser öffnen; eine laufende Instanz mit gleichem Datenordner wiederverwenden.
- Kontrolliertes Beenden über eine private Prozess-Pipe. Wird das Startfenster
  unerwartet beendet, beendet der gestartete Dienst sich ebenfalls.
- Neue Tests für Installationseinwilligung, Wiederverwendung und tatsächlichen
  Start/Stop des Desktop-Dienstes. Die native Windows-Oberfläche und
  Desktop-Verknüpfung benötigen weiterhin eine Prüfung auf einem Windows-Rechner.

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
