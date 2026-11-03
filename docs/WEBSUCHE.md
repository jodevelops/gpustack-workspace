# Aktive Websuche im GPUStack Arbeitsraum

**Version 0.1.8 · 8. Oktober 2026**

Der Arbeitsraum kann jetzt allgemein im Web suchen, einzelne Webseiten einlesen
und die gefundenen Quellen im Chat an das lokale GPUStack-Modell übergeben.
Die Antworten entstehen weiterhin auf deinem GPUStack-Endpunkt. Der Suchanbieter
bekommt den sichtbaren Suchtext; er erzeugt keine KI-Antwort für diesen Chat.

## Bestehende Installation aktualisieren

1. Dienst beenden und den bisherigen Nutzerdatenordner sichern.
2. **GPUStack-Arbeitsraum-Update-v0.1.8.zip** separat entpacken.
3. Inhalt in den bisherigen Programmordner **gpustack-arbeitsraum** kopieren und
   vorhandene Programmdateien ersetzen. Insbesondere **app/websearch.py** und
   **web/websearch.js** mitkopieren.
4. Wie bisher mit demselben Datenordner starten und **Strg+F5** drücken.

Das Update enthält keine Startskripte, `requirements`-Dateien, Schlüssel oder
Nutzerdaten. Deine angepasste `start.py` und `--data-dir`-Vorgabe bleiben erhalten.
Keine neuen Python-Abhängigkeiten. Keine neue Datenbankmigration für Websuche.

## Anleitung direkt in der App

**Einstellungen → Websuche → Einrichtung Schritt für Schritt** öffnet eine
lokal verfügbare Anleitung. Sie erklärt beide Anbieter, verlinkt die offiziellen
Einrichtungsseiten und hilft bei Fehlern. Auch unter **Recherche → Websuche →
Einrichtung erklären** erreichbar. **Anleitung herunterladen** speichert diese
ausführliche Fassung als Markdown.

**Brave / SearXNG im Formular auswählen** stellt nur das Anbieterfeld ein.
Es speichert nichts und startet keine Suche. Bereits eingegebene, noch nicht
gespeicherte Angaben bleiben in den Einstellungen erhalten. Anbieterlinks öffnen
sich erst durch Anklicken in einem neuen Tab; die Hilfe selbst braucht kein Internet.

## Einmalig einen Suchanbieter einrichten

**Einstellungen → Externe Recherche freigeben** einschalten und speichern.
Darunter steht der neue Bereich **Websuche**. Die Freigabe erlaubt externe
Suchtexte und bewusst gestartete Webseitenabrufe. Sie startet selbst keine Suche.

| Anbieter | Voraussetzung | Datenweg |
|---|---|---|
| SearXNG · eigene Instanz | Basis-URL einer lokalen oder institutionellen Instanz mit JSON-Suchformat | Suchtext an diese Instanz; sie fragt ihre eingerichteten Suchmaschinen ab |
| Brave Search API | Separater Brave-Suchschlüssel und freigegebener API-Zugang | Suchtext an die Brave Search API; Anbieterbedingungen und Kontingente gelten |

Es wird kein öffentlicher SearXNG-Server automatisch gewählt. Die App installiert
keinen Suchserver. Für euren institutionellen Betrieb kann die IT eine eigene
Instanz bereitstellen. Eine eigene Instanz verhindert nicht, dass ihre externen
Suchmaschinen den Suchtext erhalten.

### SearXNG: vorhandene Instanz verwenden

SearXNG ist ein separater Suchserver. Du benötigst die **Basis-URL** einer
laufenden Instanz. Eure GPUStack-Adresse ist kein SearXNG-Endpunkt.

1. Von der IT die SearXNG-Basis-URL erhalten, z.B. **https://suche.intern**.
   Diese ist ein Platzhalter; die tatsächliche Adresse muss eure IT nennen.
2. Unter **Einstellungen → Websuche** den Anbieter **SearXNG · eigene Instanz**
   wählen. Die erhaltene URL ohne Suchtext oder Query-Parameter eintragen.
   Die App ergänzt `/search`.
3. **Suchanbieter speichern**. Anschliessend **Websuche öffnen** und mit dem
   öffentlichen Suchtext **IIIF Presentation API** suchen.

Für eine tatsächlich auf deinem Rechner laufende Instanz ist
**http://127.0.0.1:8080** möglich; ausserhalb von localhost ist HTTPS erforderlich.
Auf deinem verwalteten Windows-PC musst du nichts zusätzlich installieren,
wenn die IT die Instanz bereitstellt.

### SearXNG: wenn die IT erst eine Instanz bereitstellen muss

Die offizielle [Container-Installation](https://docs.searxng.org/admin/installation-docker.html)
beschreibt Docker/Podman und die aktuellen Compose-Vorlagen. Der Suchserver kann
auf einem freigegebenen institutionellen Rechner laufen; Docker ist keine
Voraussetzung für den Arbeitsraum selbst.

Die IT benötigt folgende Schritte:

1. Host und Netzwerkzugang zu den gewünschten Suchmaschinen festlegen,
   eine funktionsfähige Docker-/Podman-Umgebung bereitstellen und die offizielle
   Compose-Installation einrichten. Vorlagen und eingesetzte Version prüfen.
2. In der **vorhandenen** `core-config/settings.yml` der aktuellen Compose-Installation
   (bei anderen Installationswegen kann der Pfad abweichen) unter `search` zusätzlich
   das JSON-Format freigeben. Vorhandene Konfiguration erhalten:

```yaml
search:
  formats:
    - html
    - json
```

3. Den SearXNG-Dienst nach der Konfigurationsänderung neu starten.
4. Für institutionellen Betrieb eine erreichbare HTTPS-Basis-URL und ihre
   Zertifikatskette bereitstellen. Für einen lokalen Test nur den Loopback-Port
   freigeben. Der lokale Python-Dienst muss den Endpunkt erreichen können.
5. Mit einem öffentlichen Testbegriff prüfen, ob beispielsweise
   `https://suche.intern/search?q=IIIF&format=json&categories=general` JSON mit
   einem `results`-Feld liefert. Ein erfolgreicher Browser-SSO-Aufruf allein
   bestätigt den Zugriff aus dem Arbeitsraum nicht.
6. Basis-URL an den Nutzer geben und im Arbeitsraum wie oben testen.

Kurze Anforderung an die IT zum Kopieren:

> Für den lokal laufenden GPUStack Arbeitsraum benötige ich die Basis-URL einer
> institutionellen SearXNG-Instanz mit freigegebenem JSON-Suchformat. Der lokale
> Python-Dienst muss GET /search mit q, format=json und categories=general über
> HTTPS erreichen können. Er übernimmt keine Browser-SSO-Cookies. Bitte auch die
> erlaubten Suchmaschinen, Netzfreigabe und Zertifikatskette festlegen.

Ohne JSON-Freigabe kann SearXNG HTTP 403 liefern. Browser-SSO, Cookies oder eine
GPUStack-Anmeldung werden nicht übernommen. Die Installation und Netzfreigabe
sind eine eigene Betriebsaufgabe; die App installiert keinen Suchserver.
Eine eigene Instanz leitet Suchtexte an ihre eingerichteten Suchmaschinen weiter.

### Brave Search API: Konto und Schlüssel einrichten

Für diesen Weg brauchst du einen freigegebenen Brave-API-Zugang. Dein bisheriger
Browser genügt; keine zusätzliche Browser- oder Python-Installation.

1. [Brave Search API-Dashboard](https://api-dashboard.search.brave.com/) öffnen.
   Konto mit E-Mail und Passwort anlegen, E-Mail bestätigen und anmelden;
   alternativ einen freigegebenen institutionellen Zugang nutzen.
2. Unter **Plans** einen Tarif aktivieren, der **Web Search** unterstützt. Der
   Arbeitsraum verwendet den Web-Search-Endpunkt. Die aktuelle
   [Brave-Einrichtung](https://api-dashboard.search.brave.com/documentation/quickstart)
   verlangt Zahlungsangaben zur Tarifaktivierung. Kosten, Kontingent und unter
   **Usage limits** die Nutzungslimits prüfen; bei Prepaid auch die Einstellung
   für automatisches Nachladen prüfen. Keine Zahlung oder Registrierung wird
   durch den Arbeitsraum ausgeführt.
3. **Vor Nutzung die Speicherrechte klären:** Der Arbeitsraum erhält Webauszüge
   im Chatverlauf und in gespeicherten Projektquellen. Brave verlangt für die
   dauerhafte Speicherung einen Tarif/Vertrag, der dies ausdrücklich erlaubt.
   Ein funktionierender Standard-Schlüssel bestätigt diese Rechte nicht.
   Siehe [Brave: API und Speicherrechte](https://brave.com/search/api/) und
   [Brave-Vertragsbedingungen](https://api-dashboard.search.brave.com/documentation/resources/terms-of-service).
   Für den institutionellen Einsatz einen entsprechend freigegebenen Vertrag
   nutzen oder eine eigene SearXNG-Instanz mit geklärten Quellenbedingungen wählen.
4. Unter **API Keys → Add API Key** einen Schlüssel erstellen, z.B. mit Namen
   **GPUStack Arbeitsraum**, und kopieren. Der GPUStack-Schlüssel funktioniert
   dafür nicht.
5. Im Arbeitsraum **Einstellungen → Websuche → Brave Search API** wählen.
   Schlüssel in **Brave-Suchschlüssel** einfügen. Unter **Neuen Suchschlüssel
   speichern** zwischen Serversitzung und **Betriebssystem-Schlüsselspeicher** wählen.
   Sitzungsablage endet beim Beenden des lokalen Dienstes; OS-Ablage bleibt über
   Neustarts bestehen, sofern der Schlüsselspeicher verfügbar ist.
6. **Suchanbieter speichern**. Externe Recherche oben freigeben und die
   Verbindungseinstellungen speichern. **Websuche öffnen** und mit dem
   öffentlichen Begriff **IIIF Presentation API** testen.

Die App prüft deinen Anbieter-Vertrag nicht und bietet keinen Modus an, der
Brave-Belege beim Speichern eines Chats automatisch entfernt. Für gespeicherte
Recherche daher nur einen Zugang mit passenden Speicherrechten verwenden.

Beim Speichern wird kein Suchtest ausgelöst. **Konfiguriert** bedeutet nur,
dass URL oder Schlüssel vorhanden sind, nicht, dass der Dienst erreichbar ist.
Der Schlüssel wird nicht an den Browser zurückgegeben und nicht in SQLite,
Projektdateien, Chat-Exporten oder Backups gespeichert. Der GPUStack-Schlüssel
bleibt davon unabhängig. Eine von der IT gesetzte Prozessvariable
`BRAVE_SEARCH_API_KEY` ist ebenfalls möglich; sie wird ausserhalb der App verwaltet.

## Typische Einrichtungsfehler

| Meldung / Beobachtung | Nächster Schritt |
|---|---|
| Externe Recherche nicht freigegeben | In Einstellungen einschalten und Verbindungseinstellungen speichern |
| Konfiguriert, aber Suche funktioniert nicht | Das bedeutet nur „URL oder Schlüssel vorhanden“; öffentlich suchen und konkrete Fehlermeldung prüfen |
| Brave 401 / 403 | Schlüssel, aktiven Tarif und Web-Search-Zugang im Dashboard prüfen |
| SearXNG 403 | JSON-Format, API-Zugang, Netzregeln oder vorgeschaltete Anmeldung mit IT prüfen |
| 429 | Kontingent / Anfragelimit prüfen, gegebenenfalls später erneut suchen |
| Timeout / DNS / Zertifikat | VPN, erreichbare Basis-URL, Netzfreigabe und Zertifikatskette prüfen lassen; kein Abschalten von TLS |
| Brave-Schlüssel fehlt nach Neustart | Sitzungsablage gewählt: neu eingeben; für Neustarts Betriebssystem-Schlüsselspeicher wählen |
| Einzelne Trefferseite nicht lesbar | Suchtreffer kann verfügbar sein, obwohl Seitenabruf an robots-Regeln, Bot-Schutz oder JS scheitert |

## Im Recherchebereich suchen

**Recherche → Datenquelle: Websuche** wählen. Öffentlichen Suchtext, Suchsprache
und bei Bedarf Zeitraum einstellen. Deutsch, Englisch und Französisch sind
verfügbar; **Anbieter-Vorgabe** setzt keinen eigenen Sprachparameter.
Datumsfilter und Angaben aus dem Suchindex sind keine verifizierten Publikationsdaten.

Die App zeigt Titel, Link und Suchauszug. **Suchauszug** bedeutet: Die Webseite
wurde noch nicht vom Arbeitsraum eingelesen. Mit **Seite einlesen** lässt sich
der extrahierte Text in einem Dialog prüfen, als Markdown herunterladen und
bewusst im aktuellen Projekt speichern. **Als Projektquelle speichern** direkt
am Treffer speichert den Suchauszug mit URL, Anbieter, Suchtext und Abrufzeit.

Ein gespeicherter Webtext wird wie andere Dokumente in der Library verwendet.
Er aktualisiert sich nicht automatisch, wenn die ursprüngliche Webseite später
geändert wird. Die UI-Speicherreferenz für noch nicht abgelegte Suchergebnisse
läuft nach 30 Minuten oder einem Serverneustart ab; dann erneut suchen/einlesen.

Crossref, Wikidata, GND/lobid und DataCite bleiben als getrennte Quellen erhalten.

## Eine Webseite ohne Suchanbieter einlesen

Unter **Recherche → Eine Webseite direkt einlesen** eine vollständige öffentliche
HTTPS-Adresse eingeben und **Einlesen und Vorschau** wählen. Dafür genügt die
Freigabe der externen Recherche; kein Suchschlüssel und keine SearXNG-Instanz.

Unterstützt werden öffentliche HTML-, XHTML- und Textseiten auf HTTPS-Port 443.
Der Leser führt kein JavaScript aus, übernimmt keine Browser-Cookies und meldet
sich nicht an. Skripte, Navigation und Formulare werden aus dem Text entfernt.
Das ist eine Textauswahl, kein Screenshot und kein vollständiges Originalarchiv.

`robots.txt` wird vor dem Abruf geprüft. Verbotene oder nicht verlässlich prüfbare
Abrufe werden abgewiesen. Private Netzwerkadressen, localhost, Zugangsdaten in
URLs und entsprechende Weiterleitungen sind gesperrt. DNS-Adressen werden vor
der Verbindung geprüft; die TCP-Verbindung verwendet die geprüfte IP, während
TLS den ursprünglichen Hostnamen prüft. Das verhindert einen Wechsel auf interne
Dienste zwischen separater DNS-Prüfung und Verbindung.

PDFs und andere Dateitypen separat herunterladen und lokal hochladen. Bei
JS-Seiten, Anmeldung, Paywall, Bot-Schutz oder Netzsperre kann kein brauchbarer
Text verfügbar sein. Die App umgeht solche Zugriffsgrenzen nicht.

## Im Chat mit Webquellen antworten

1. Frage schreiben.
2. **Websuche für diese Nachricht** einschalten.
3. Den separaten **Öffentlichen Suchtext** eingeben. Mit **Frage als Suchtext
   übernehmen** lässt sich die Frage bewusst kopieren; vor dem Senden prüfen.
4. Optional **Zusätzlich bis zu 3 Trefferseiten einlesen** einschalten. Der
   einstellbare Wert steht direkt am Schalter.
5. **Senden**. Der Arbeitsraum recherchiert und übergibt danach Treffer bzw.
   gelesenen Webtext gemeinsam mit deiner Frage an das gewählte GPUStack-Modell.

Webquellen tragen Labels **[W1]**, **[W2]** usw.; Projektdateien weiterhin **[Q1]**
usw. Die Labels bleiben im Verlauf eindeutig. Quellenbuttons zeigen die genau
übergebenen Texte, URL und Abrufzeit; ein Link öffnet das Original.
Suchtext und Anbieter werden unter der Nachricht angezeigt. Nach einer
angenommenen Anfrage ist neue Websuche für die nächste Nachricht wieder aus.
Bereits gespeicherte Webquellen können weiterhin Bestandteil des Chatverlaufs
und damit einer Folgeanfrage sein; für einen getrennten Kontext einen neuen Chat
beginnen. Eine neue Suche aktualisiert alte Belege nicht rückwirkend.

Ohne Webtreffer oder bei einem Suchdienstfehler wird keine Modellantwort als
aktuell recherchiert ausgegeben. Frage und Suchtext bleiben bearbeitbar.
Scheitert nur das optionale Einlesen einer Trefferseite, wird ihr Suchauszug
verwendet und diese Einschränkung sichtbar genannt. Das gesamte Eingabebudget
wird nach Aufnahme der Webquellen erneut geprüft; kein stilles Kürzen des Chats.

**Stoppen** während der Recherche erhält die noch nicht gesendete Frage.
Bereits gestartete externe Anfragen lassen sich nicht zurückrufen. Ein laufender
blockierender Seitenabruf kann bis zu seinem Zeitlimit auslaufen; nach erkanntem
Verbindungsabbruch startet die Chatvorbereitung keine neue Modellanfrage.

Es ist eine begrenzte Suche je ausdrücklich freigegebener Nachricht, kein
unbegrenzt selbstständig handelnder Rechercheagent. Das Verfahren setzt keine
Tool-Calling-Fähigkeit des Chatmodells voraus. Die Anwendung übergibt Webtext als
ungeprüftes Quellenmaterial; Belege und Modellantwort fachlich kontrollieren.

## Datenwege und Grenzen

| Vorgang | Was den Rechner verlässt |
|---|---|
| Websuche | Sichtbarer Suchtext, Sprache/Zeitraum, normale Verbindungsdaten; bei Brave zusätzlich der separate Suchschlüssel nur an Brave |
| Webseite einlesen | Seitenadresse und Verbindungsdaten an die Webseite; keine GPUStack- oder Brave-Schlüssel, Browser-Cookies oder Projektdateien |
| Antwort mit Webquellen | Frage, ausgewählte lokale Quellen/Verlauf und Webauszüge an deinen GPUStack-Endpunkt |
| Vorschau speichern / MD herunterladen | Lokale Ablage bzw. lokaler Download; keine neue Webabfrage |

Suchbegriffe und URLs müssen für externe Übermittlung geeignet sein.
Modellverarbeitung bleibt auf dem konfigurierten GPUStack-Endpunkt. Websuche
ändert die Datenschutzbewertung der Suchtexte: „Modell lokal“ bedeutet hier
nicht „keine Internetübermittlung“. Eine pauschale Datenschutzgarantie wird
nicht daraus abgeleitet.

Vorgaben unter **Einstellungen → Ressourcengrenzen**:

| Grenze | Vorgabe | Einstellbar bis |
|---|---:|---:|
| Websuchtreffer | 5 | 20 |
| Such-/Seitenzeitlimit | 30 s pro Vorgang | 120 s |
| Webseitenantwort | 2 MiB | 16 MiB |
| Extrahierter Text je Seite | 8.000 Zeichen | 100.000 |
| Optional eingelesene Trefferseiten im Chat | 3 | 10 |

Eine Suche plus mehrere Seiten kann länger als ein einzelnes Zeitlimit dauern.
Zusätzlich gilt eine feste Grenze von 2 MiB für die JSON-Suchantwort und ein
Suchtextlimit von 300 Zeichen; Brave erlaubt maximal 75 Wörter. Das Modell-
kontextfenster und dein Chatbudget bleiben unabhängig davon. Die lokale
Budgetvorschau ruft keine Suche auf und enthält neue Webtreffer noch nicht.
Textkürzungen am Webauszug werden kenntlich gemacht. Routinen starten weiterhin
keine automatischen Websuchen. Proxy-Umgebungsvariablen werden nicht übernommen;
`SSL_CERT_FILE` unterstützt eine von der IT bereitgestellte Zertifikatskette.

## Prüfung und Quellen

130 Python-Tests und der erweiterte DOM/API-Test bestanden. Websuche verwendet
in diesen Tests simulierte Anbieter; DNS, IP-Verbindung, TLS-Hostname, robots-
Regeln, Redirects, Bytegrenzen, Schlüsseltrennung, Abbruch, Budgets und Exporte
wurden gezielt geprüft. Kein echter Brave-Schlüssel oder institutioneller
SearXNG-Zugang stand zur Verfügung. Der Live-Abruf der SearXNG-Dokumentation
scheiterte hier an der DNS-Auflösung; das belegt keine Störung bei euch.
Windows, OS-Schlüsselspeicher und gerendertes Browserlayout vor Ort prüfen.

Offizielle Schnittstellen, geprüft am 8. Oktober 2026:

- [SearXNG Search API](https://docs.searxng.org/dev/search_api.html)
- [SearXNG Suchkonfiguration](https://docs.searxng.org/admin/settings/settings_search.html)
- [Brave Web Search API](https://api-dashboard.search.brave.com/api-reference/web/search/get)
- [Brave API-Einrichtung](https://api-dashboard.search.brave.com/documentation/quickstart)
- [Brave API-Dashboard](https://api-dashboard.search.brave.com/)
- [Brave API: Speicherrechte](https://brave.com/search/api/)
- [Brave API: Vertragsbedingungen](https://api-dashboard.search.brave.com/documentation/resources/terms-of-service)
- [SearXNG Container-Installation](https://docs.searxng.org/admin/installation-docker.html)
