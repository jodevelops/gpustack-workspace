# Recherchequellen und Einbindung

Stand: 8. Oktober 2026 · Arbeitsraum 0.1.7

## Was am Wikidata-Anschluss geändert wurde

Der bisherige Endpunkt `https://www.wikidata.org/w/api.php` und die Aktion
`wbsearchentities` waren grundsätzlich richtig. Die Suchsprache bleibt Deutsch.
Der alte Client benannte weder HTTP-Status noch Antwortformat und hatte keine
Kontaktangabe in seiner Anwendungskennung. Die konkrete Ursache der vor Ort
beobachteten Fehlermeldung lässt sich damit rückblickend nicht beweisen.

Wikimedia verlangt eine aussagekräftige Clientkennung mit Kontaktmöglichkeit.
Die Anwendung verwendet jetzt eine eigene ResearchBot-Kennung mit der
ausdrücklich unter Einstellungen hinterlegten E-Mail oder HTTPS-Kontaktseite.
Ohne echten Recherchekontakt wird ein Wikidata-Aufruf mit einem verständlichen
Hinweis vor dem Versand abgelehnt. Browserkennungen werden nicht vorgetäuscht.

Explizite Parameter: `action=wbsearchentities`, `language=de`, `uselang=de`,
`type=item`, `format=json`, `limit=8` und `maxlag=5`.
Fehlerobjekte in HTTP-200-Antworten werden erkannt. Redirects sind auf
HTTPS und denselben Anbieter begrenzt; es gibt keine stille Ausweichsuche.
Bei Timeout, Zugriffsschutz oder Zertifikatsfehler erscheint eine quellenbezogene
Meldung statt eines pauschalen „nicht erreichbar“.

Ein HTTP 403 kann durch Anbieterregeln, IP-Sperren oder ein institutionelles
Gateway entstehen. Eine HTML-Seite kann ein Bot-Schutz oder eine
vorgeschaltete Anmeldung sein. Der Client löst solche Sperren nicht automatisch.
Systemweite Proxy-Variablen werden weiterhin nicht übernommen; die IT muss
die erlaubten Datenwege festlegen.

## Quellenbewertung

| Quelle | Eignung im Sammlungskontext | Zugang | Lieferstand |
|---|---|---|---|
| Crossref | Literatur, DOI, bibliografische Verknüpfungen | Öffentliche Such-API | Vorhandener Adapter verbessert |
| Wikidata | Entitäten und Normdatenverknüpfungen; Aussagen anhand ihrer Belege prüfen | Öffentliche Action API; Kontakt in Clientkennung | Überarbeitet |
| GND / lobid | Personen, Orte, Körperschaften, kontrollierte Begriffe | Öffentliche JSON-LD-Suche über hbz; möglicher Bot-Schutz | Neu implementiert |
| DataCite | Forschungsdaten und weitere Forschungsobjekte mit DOI | Öffentliche DOI-Suche | Neu implementiert |
| Europeana | Digitalisierte Kulturgüter, institutionelle Sammlungsnachweise, IIIF-Verknüpfungen | Persönlicher API-Schlüssel nach kostenloser Registrierung | Empfohlene nächste Erweiterung; nicht implementiert |
| OpenAlex | Breite wissenschaftliche Literatur und bibliografische Vernetzung | Aktuelle Auth-Dokumentation erlaubt Basissuchen ohne Key; kostenloser Key erhöht das Kontingent | Empfohlene nächste Erweiterung; nicht implementiert |
| Europe PMC | Lebenswissenschaften, medizinische Literatur, Abstracts | Öffentliche REST-Suche | Fachlich ergänzend, für deine Sammlungen weniger vorrangig; nicht implementiert |

Für Normierung sind GND-Datensätze besonders passend. Wikidata liefert
zusätzliche Verknüpfungen, ersetzt aber keine Quellenprüfung. DataCite ergänzt
die Crossref-Suche um Forschungsobjekte, die in Repositorien liegen.
Europeana ist für deine digitalen Sammlungen die nächste fachliche Priorität.
Hier braucht es eine getrennte, sichere Verwaltung des Europeana-Schlüssels:
Der GPUStack-Schlüssel darf dafür nicht verwendet werden.

OpenAlex hat seine Zugangspolitik 2026 geändert. Ein Beitrag vom Februar nennt
eine Schlüsselpflicht; die neuere Authentifizierungsdokumentation vom August
erlaubt begrenzte anonyme Nutzung. Für eine Integration sind die jeweils
aktuellen Endpunktregeln und das Budget nochmals zu prüfen. Diese Version
behauptet deshalb weder eine universelle Schlüsselpflicht noch unbegrenzten
kostenlosen API-Zugang.

## Daten und Ergebnisse der vier Fachquellen

Nur der eingegebene Suchtext, technische Anfrageparameter und gegebenenfalls
der Recherchekontakt werden an genau eine gewählte Quelle gesendet.
Keine automatischen Anfragen aus Chats, keine Dokumentübertragung, kein
GPUStack-Schlüssel und kein allgemeiner Webcrawler.
Ein Treffer ist eine Metadaten-/Normdatenquelle, kein automatisch geprüfter
Fakt und kein vollständig gelesener Artikel. Beim bewussten Speichern bleiben
Quelle, Link, ursprünglicher Suchtext und Zeitpunkt des Abrufs erhalten.

## Verifizierte Primärdokumentation

- [Wikimedia: API-Zugang und Clientkennung](https://www.mediawiki.org/wiki/Wikimedia_APIs/Access_policy)
- [Wikimedia: User-Agent-Richtlinie](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy/en)
- [hbz: lobid-GND und JSON-LD-Suche](https://github.com/hbz/lobid/blob/master/doc/lobid-gnd.md)
- [DataCite: Query-Parameter und Pagination](https://support.datacite.org/docs/api-queries)
- [Europeana: APIs und Schlüsselregistrierung](https://api.europeana.eu/en)
- [OpenAlex: aktuelle Authentifizierung](https://help.openalex.org/api/authentication/)
- [OpenAlex: Zugangspolitik vom Februar 2026](https://blog.openalex.org/openalex-api-new-features-and-usage-based-pricing/)
- [Europe PMC: RESTful Web Service](https://europepmc.org/RestfulWebService)

Die Dokumentation wurde recherchiert. Live-Anfragen aus dem lokalen Testprozess
an Wikidata, Crossref und lobid waren hier durch Zeitüberschreitungen blockiert.
Die in dieser Umgebung per Webabruf sichtbare lobid-Schutzseite ist ein
zusätzliches Signal für mögliche Zugangsgrenzen, kein Nachweis einer Sperre
deines Arbeitsplatzes. Die Adapter wurden mit synthetischen Antworten geprüft;
institutionelle Live-Tests müssen vor Ort erfolgen.

## Aktive Websuche ab 0.1.7

Zusätzlich zu den vier Fachquellen stehen eine allgemeine Suche über eine
konfigurierte SearXNG-Instanz oder die Brave Search API und ein gezielter
öffentlicher HTTPS-Webseitenabruf zur Verfügung. Suchschlüssel sind getrennt
vom GPUStack-Schlüssel. Die App bietet Suchauszüge, gelesenen Webtext, lokale
Projektablage und eine ausdrücklich je Chatnachricht zuschaltbare Webrecherche.

[Einrichtung, Datenwege, Bedienung und Prüfung](WEBSUCHE.md). Die allgemeine
Websuche verwendet nicht die Wikidata-/Crossref-Adapter. Keine automatische
Ausweichsuche und keine undeklarierte Übergabe privater Projekt-/Chatinhalte.
