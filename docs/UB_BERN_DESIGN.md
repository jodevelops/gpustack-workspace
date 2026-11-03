# UB Bern: Design der Anwendung

Branch `design/ub-bern`, auf Basis von Version 0.1.10. Grundlage ist das
bereitgestellte Paket **UB Bern Design System** mit dem darin ausgewerteten
UniBE Manual 06. Die Vorlage beschreibt überwiegend Präsentationen; ihre
Gestaltungsprinzipien wurden auf eine interaktive Anwendung übertragen.

## Farben und Typografie

| Rolle | Umsetzung |
|---|---|
| Primärfarbe | UniBE-Rot `#E6002E`: Hauptaktionen, aktive Navigation, Titel und obere Linie |
| Grundfläche / Text | Weiss `#FFFFFF` und Schwarz `#000000` |
| Logo-Kontur | Logo-Schwarz `#1D1D1B` |
| Grautöne | CD-Grau `#7A7C81` für Konturen, Hellgrau `#EDEDED` für Trennlinien; abgeleitete Fläche `#F7F7F7` |
| Sekundärtext | Abgeleitetes Dunkelgrau `#5C5D61` für lesbare kleine Beschriftungen |
| Links | Blau `#0563C1` aus den gelieferten Tokens, Rot bei Hover |
| Status | Punktuell Erde-Grün `#466553`, Braun `#583012`, Violett `#820924`; Senf `#C2B600` als Warnmarkierung |
| Schrift | Arial Regular/Bold; Fallbacks Helvetica Neue, Helvetica, Liberation Sans, sans-serif |

Der im Designsystem festgehaltene Arial-Entscheid gilt auch hier. Frutiger wird
nicht ohne bereitgestellte lizenzierte Schriftdateien eingebunden. Es werden
keine Fonts von externen Diensten geladen. Für bearbeitbaren Programmcode
bleibt eine lokale Monospace-Schrift erhalten.

## Layout und Bedienung

Die Oberfläche nutzt linksbündige Texte, grosszügigen Weissraum, flache weisse
Flächen und eine rote Linie am oberen Rand. Der zweifarbige Begrüssungstitel
hat zwei gleich grosse Zeilen. Runde Karten, Schatten und Verläufe entfallen.
Funktionale Eingabefelder, Tabellen und Bereichstrenner behalten Konturen;
Fokus und Auswahl sind sichtbar. Textgrössen und Abstände sind auf eine
Arbeitsoberfläche abgestimmt, statt Folienmasse unverändert zu übernehmen.

Die zentrale Anpassung steht in [`web/ub-bern.css`](../web/ub-bern.css), nach
dem bereinigten Layout-Stylesheet geladen. Sie gilt für Chat, Quellenpanel,
Projekte, Library, Audio, Prompts, Recherche, Routinen, Datenlabor und
Einstellungen. Das native Startfenster verwendet dieselben Grundfarben,
Arial und das neue Logo. Neue Desktop-Verknüpfungen verwenden das ICO-Asset.

Eigene Oberflächentexte verwenden die formelle Anrede **Sie** und Schweizer
Orthografie. Vom Benutzer gespeicherte Inhalte und Modellantworten werden
dabei nicht umgeschrieben.

## Schild und KI-Sterne

Das bisherige «A» wurde durch ein eigenes, zurückhaltendes App-Zeichen ersetzt:
eine feine Schildkontur für Schutz, zwei rote vierzackige Sterne und ein
kleiner grauer Stern für KI-Unterstützung. Das Zeichen ist in der Navigation,
auf der Startseite, an Modellantworten, als Favicon und im Startfenster sichtbar.
Es ist ein App-Logo; es ersetzt oder verändert keine offizielle UniBE-Wortbildmarke.

| Datei | Verwendung |
|---|---|
| [`web/brandmark.svg`](../web/brandmark.svg) | Skalierbare Originalzeichnung, ViewBox 64 × 64 |
| [`web/favicon.svg`](../web/favicon.svg) | Gleiches Zeichen für den Browser-Tab |
| [`web/brandmark.png`](../web/brandmark.png) | 128 × 128 Pixel, transparent, für Tk |
| [`web/arbeitsraum.ico`](../web/arbeitsraum.ico) | Windows-Icon mit Grössen von 16 bis 256 Pixeln |

## Lesbarkeit und Prüfung

Rot auf Weiss hat einen berechneten Kontrast von **4,77:1**. Kleine graue
Texte nutzen `#5C5D61` statt des helleren Vorlagen-Graus: **6,58:1** auf Weiss
und **6,14:1** auf der hellen Hinweisfläche. Rote aktive Tabs liegen auf Weiss;
Textaktionen auf grauen Hinweisen sind schwarz und unterstrichen. Diese
gezielten Prüfungen sind keine vollständige Barrierefreiheitszertifizierung.

Die [Screenshots im README](../README.md#1-auf-einen-blick) zeigen die tatsächliche
Anwendung mit synthetischen Daten. Browser- und Regressionsergebnisse stehen
im [Prüfprotokoll](PRUEFPROTOKOLL.md).
