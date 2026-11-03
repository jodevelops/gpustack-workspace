// Search providers get the visible search query only, never the assembled model context.
export function createWebWorkspace(h){
 const {state,api,render,refresh,esc,icon,btn,options,modal,toast,download,invalidateBudget}=h;
 const $=s=>document.querySelector(s);
 const W={enabled:false,query:"",language:"de",freshness:"all",readPages:false,url:"",pageBusy:false};
 const languages=[["de","Deutsch"],["en","Englisch"],["fr","Französisch"],["all","Anbieter-Vorgabe"]];
 const periods=[["all","Alle Zeiträume"],["day","Letzter Tag"],["month","Letzter Monat"],["year","Letztes Jahr"]];
 const cfg=()=>state().data.web_search;
 const enabled=()=>state().data.connection.internet_enabled;
 function reset(){W.enabled=false;W.query="";W.readPages=false;}
 function chatControls(){
  return `<div class="web-chat"><label class="check-label"><input id="chat-web-enabled" type="checkbox" ${W.enabled?"checked":""} ${state().busy?"disabled":""}><span>${icon("globe")}Websuche für diese Nachricht</span></label>
  ${W.enabled?`<div class="web-chat-fields"><div class="field"><label for="chat-web-query">Öffentlicher Suchtext · wird an ${esc(cfg().provider_name)} gesendet</label><input id="chat-web-query" type="text" minlength="2" maxlength="300" required value="${esc(W.query)}" ${state().busy?"disabled":""} placeholder="Suchbegriffe ohne vertrauliche Angaben"><button type="button" class="text-btn" data-action="web-copy-question" ${state().busy?"disabled":""}>Frage als Suchtext übernehmen</button></div>
  <div class="field-row"><div class="field"><label for="chat-web-language">Suchsprache</label><select id="chat-web-language" ${state().busy?"disabled":""}>${options(languages,W.language)}</select></div><div class="field"><label for="chat-web-freshness">Zeitraum</label><select id="chat-web-freshness" ${state().busy?"disabled":""}>${options(periods,W.freshness)}</select></div></div>
  <label class="check-label"><input id="chat-web-pages" type="checkbox" ${W.readPages?"checked":""} ${state().busy?"disabled":""}>Zusätzlich bis zu ${state().data.limits.web_read_pages} Trefferseiten einlesen</label>
  <p class="footnote">Nur der sichtbare Suchtext geht an den Suchanbieter. Gelesene Seiten erhalten Ihre IP-Adresse und die Seiten-URL. Treffer und gelesener Text gehen an Ihr GPUStack-Modell; Chatverlauf und Projektdateien gehen nicht an die Suchdienste.</p>
  ${!enabled()?'<p class="message-error">Externe Recherche zuerst in den Einstellungen freigeben.</p>':!cfg().ready?'<p class="message-error">Suchanbieter zuerst unter Einstellungen → Websuche einrichten.</p>':""}</div>`:""}</div>`;
 }
 function bind(){
  $("#chat-web-enabled")?.addEventListener("change",e=>{W.enabled=e.target.checked;invalidateBudget();render();});
  $("#chat-web-query")?.addEventListener("input",e=>{W.query=e.target.value;invalidateBudget();});
  for(const [id,key] of [["chat-web-language","language"],["chat-web-freshness","freshness"]])$("#"+id)?.addEventListener("change",e=>{W[key]=e.target.value;invalidateBudget();});
  $("#chat-web-pages")?.addEventListener("change",e=>{W.readPages=e.target.checked;invalidateBudget();});
  $("#web-page-url")?.addEventListener("input",e=>W.url=e.target.value);
  $("#web-page-form")?.addEventListener("submit",e=>{e.preventDefault();readPage(W.url).catch(h.fail);});
  $("#web-config-form")?.addEventListener("submit",e=>{e.preventDefault();saveConfiguration().catch(h.fail);});
  $("#web-provider")?.addEventListener("change",()=>{
   $("#searxng-fields").classList.toggle("hidden",$("#web-provider").value!=="searxng");
   $("#brave-fields").classList.toggle("hidden",$("#web-provider").value!=="brave");
   $("#brave-storage-note").classList.toggle("hidden",$("#web-provider").value!=="brave");
  });
 }
 function request(){
  if(!W.enabled)return {web_search:false};
  if(!enabled())throw new Error("Externe Recherche zuerst unter Einstellungen freigeben.");
  if(!cfg().ready)throw new Error("Suchanbieter zuerst unter Einstellungen → Websuche einrichten.");
  if(W.query.trim().length<2)throw new Error("Bitte einen separaten öffentlichen Suchtext eingeben.");
  return {web_search:true,web_query:W.query.trim(),web_language:W.language,web_freshness:W.freshness,web_read_pages:W.readPages};
 }
 function sent(){W.enabled=false;W.readPages=false;}
 function settings(){
  const c=cfg();
  return `<form id="web-config-form" class="panel"><div class="panel-title"><h3>${icon("globe")}Websuche</h3><span class="badge ${c.ready?"green":""}">${c.ready?"Konfiguriert · noch kein Erreichbarkeitstest":"Einrichtung erforderlich"}</span></div>
  <p class="muted">Allgemeine Suchtreffer für Recherche und Chat. SearXNG kann durch Ihre IT betrieben werden; Brave Search benötigt einen eigenen API-Schlüssel. Suchtext und gewählte Webseiten sind externe Anfragen. Die Freigabe erfolgt oben über „Externe Recherche“.</p>
  <div class="field"><label for="web-provider">Suchanbieter</label><select id="web-provider">${options([["searxng","SearXNG · eigene Instanz"],["brave","Brave Search API"]],c.provider)}</select></div>
  <div id="searxng-fields" class="${c.provider==="searxng"?"":"hidden"}"><div class="field"><label for="searxng-url">SearXNG-Basis-URL</label><input id="searxng-url" type="url" maxlength="500" value="${esc(c.searxng_url)}" placeholder="https://suche.intern oder http://127.0.0.1:8080"><small>JSON-Suchformat muss in der Instanz freigegeben sein. Kein zufällig gewählter öffentlicher Server. Auch eine eigene Instanz leitet Suchtexte an ihre konfigurierten Suchmaschinen weiter.</small></div></div>
  <div id="brave-fields" class="${c.provider==="brave"?"":"hidden"}"><div class="field"><label for="web-api-key">Brave-Suchschlüssel</label><input id="web-api-key" type="password" autocomplete="new-password" placeholder="${c.key_status!=="Nicht hinterlegt"?"Hinterlegt · leer lassen zum Beibehalten":"Separaten Suchschlüssel eingeben"}"><small>Status: ${esc(c.key_status)}. Unabhängig vom GPUStack-Schlüssel; Anbieterbedingungen und Kontingent gelten.</small></div><div class="field"><label for="web-key-storage">Neuen Suchschlüssel speichern</label><select id="web-key-storage"><option value="session">Nur diese Serversitzung</option><option value="vault">Betriebssystem-Schlüsselspeicher</option></select></div><a href="https://api-dashboard.search.brave.com/" target="_blank" rel="noopener noreferrer">Brave Search API einrichten</a></div>
  <div class="card-footer">${btn("Einrichtung Schritt für Schritt","web-setup","info","subtle")}<a class="button subtle" href="/static/websearch-guide.md" download="GPUStack-Websuche.md">${icon("download")}Anleitung herunterladen</a></div>
  <p class="footnote ${c.provider==="brave"?"":"hidden"}" id="brave-storage-note">Der Arbeitsraum speichert Webquellen in Chats und Projekten. Brave dafür nur mit einem Vertrag verwenden, der entsprechende Speicherrechte gewährt. Details stehen in der Anleitung.</p>
  <div class="card-footer"><button class="button primary" type="submit">Suchanbieter speichern</button>${btn("Suchschlüssel entfernen","web-forget-key","","subtle")}${btn("Websuche öffnen","web-open-search","search","subtle")}</div>
  <p class="footnote">Beim Speichern erfolgt keine Suche. Zum Test einen öffentlichen Begriff in der Recherche eingeben. Webseite ohne Suchschlüssel über ihre öffentliche HTTPS-Adresse einlesen.</p></form>`;
 }
 function setupGuide(){
  const preferred=$("#web-provider")?.value||cfg().provider;
  modal("Websuche einrichten · Schritt für Schritt",`<div class="web-setup-guide">
  <p>Sie benötigen entweder einen Brave-Suchschlüssel oder die Adresse einer erreichbaren SearXNG-Instanz. Für eine institutionelle Instanz übernimmt die IT den Betrieb; die GPUStack-Adresse ist keine SearXNG-Adresse.</p>
  <details ${preferred==="brave"?"open":""}><summary>Brave · Konto und API-Schlüssel</summary>
  <ol><li>Das <a href="https://api-dashboard.search.brave.com/" target="_blank" rel="noopener noreferrer">Brave Search API-Dashboard</a> öffnen, Konto anlegen und E-Mail bestätigen, oder einen institutionellen Zugang nutzen. Sie können Ihren bisherigen Browser weiterverwenden.</li>
  <li>Unter <b>Plans</b> einen Tarif mit <b>Web Search</b> aktivieren. Die aktuelle Einrichtung verlangt Zahlungsangaben. Preise und <b>Usage limits</b> im Dashboard prüfen. Der Arbeitsraum speichert Quellen: Vor Nutzung ausdrücklich passende <a href="https://brave.com/search/api/" target="_blank" rel="noopener noreferrer">Speicherrechte</a> klären.</li>
  <li>Unter <b>API Keys → Add API Key</b> einen Schlüssel erstellen, z.B. mit Namen „GPUStack Arbeitsraum“. Schlüssel kopieren.</li>
  <li>Hier <b>Brave Search API</b> wählen. Schlüssel in <b>Brave-Suchschlüssel</b> einfügen, Speicherung wählen und <b>Suchanbieter speichern</b>. Für Neustarts den Betriebssystem-Schlüsselspeicher verwenden; „Nur diese Serversitzung“ gilt bis zum Beenden des Dienstes.</li></ol>
  <p class="footnote">Der GPUStack-Schlüssel bleibt separat. Eine API-Konfiguration ist keine Bestätigung von Speicherrechten; der Arbeitsraum prüft Ihren Anbieter-Vertrag nicht.</p>
  <button type="button" class="button" id="web-guide-brave">Brave im Formular auswählen</button></details>
  <details ${preferred!=="brave"?"open":""}><summary>SearXNG · vorhandene Instanz oder IT-Einrichtung</summary>
  <ol><li>Von der IT die Basis-URL einer SearXNG-Instanz erhalten, z.B. <code>https://suche.intern</code>. Sie muss vom lokalen Python-Dienst erreichbar sein und JSON-Suche erlauben. <a href="https://docs.searxng.org/admin/installation-docker.html" target="_blank" rel="noopener noreferrer">Offizielle Installationsanleitung für die IT</a>.</li>
  <li>In der Instanz unter <code>search.formats</code> zusätzlich <code>json</code> freigeben und den Dienst neu starten. Das ist eine SearXNG-Einstellung, keine Änderung an GPUStack oder Ihrer <code>start.py</code>.</li>
  <li>Hier <b>SearXNG · eigene Instanz</b> wählen, Basis-URL ohne Suchparameter eintragen und <b>Suchanbieter speichern</b>. Die App ergänzt <code>/search</code>. Eine lokal laufende Instanz darf <code>http://127.0.0.1:8080</code> nutzen; ausserhalb von localhost ist HTTPS erforderlich.</li></ol>
  <p class="footnote">Die App installiert keinen Suchserver. Auf Ihrem verwalteten Windows-PC ist keine zusätzliche Installation nötig, wenn die IT eine Instanz bereitstellt. Browser-SSO und Cookies werden nicht übernommen; die IT muss den API-Zugang ermöglichen. SearXNG leitet Suchtexte an seine eingerichteten Suchmaschinen weiter.</p>
  <button type="button" class="button" id="web-guide-searxng">SearXNG im Formular auswählen</button></details>
  <details open><summary>Verbindung prüfen und im Chat verwenden</summary>
  <ol><li>Unter <b>Einstellungen</b> die Option <b>Externe Recherche freigeben</b> einschalten und die Verbindungseinstellungen speichern.</li>
  <li><b>Websuche öffnen</b> wählen. Unter <b>Recherche → Websuche</b> mit dem öffentlichen Suchtext <b>IIIF Presentation API</b> suchen. „Konfiguriert“ allein bestätigt noch keine Erreichbarkeit.</li>
  <li>Im Chat <b>Websuche für diese Nachricht</b> einschalten und den separaten öffentlichen Suchtext prüfen. Optional Trefferseiten einlesen lassen.</li></ol>
  <p>Zum Einlesen einer einzelnen öffentlichen HTTPS-Webseite reicht die externe Recherchefreigabe; dafür benötigen Sie keinen Suchanbieter.</p></details>
  <details><summary>Wenn es nicht funktioniert</summary>
  <ul><li><b>401/403 bei Brave:</b> Schlüssel, aktiven Tarif und Web-Search-Zugang prüfen.</li><li><b>403 bei SearXNG:</b> JSON-Freigabe, API-Zugang und vorgeschaltete Anmeldung prüfen lassen.</li><li><b>429:</b> Kontingent oder Anfragelimit erreicht; später versuchen und Dashboard bzw. IT prüfen.</li><li><b>Timeout / Zertifikat:</b> VPN, Netzfreigabe oder Zertifikatskette mit der IT prüfen. Die App übernimmt keine Proxy-Umgebungsvariablen.</li><li><b>Nach Neustart kein Brave-Schlüssel:</b> Sitzungsablage endet mit dem Dienst. Schlüssel erneut eingeben und Betriebssystem-Schlüsselspeicher wählen.</li></ul></details>
  <p class="footnote">Suchtext verlässt den Rechner; die Modellantwort entsteht weiter über GPUStack. Die Anleitung ist lokal verfügbar. Die offiziellen Anbieterlinks werden erst durch Anklicken geöffnet. Stand: 8. Oktober 2026; Tarif- und Vertragsbedingungen beim Anbieter prüfen.</p>
  <a class="button" href="/static/websearch-guide.md" download="GPUStack-Websuche.md">${icon("download")}Ausführliche Anleitung herunterladen</a></div>`);
  for(const provider of ["brave","searxng"]){
   $("#web-guide-"+provider).onclick=async()=>{
    try{
     if(!$("#web-config-form"))await h.navigate("settings");
     const select=$("#web-provider");select.value=provider;select.dispatchEvent(new Event("change",{bubbles:true}));
     $("#modal").close();const target=$(provider==="brave"?"#web-api-key":"#searxng-url");target.scrollIntoView?.({block:"center"});target.focus();
     toast("Anbieter ausgewählt. Angaben ergänzen und ausdrücklich speichern.");
    }catch(error){h.fail(error);}
   };
  }
 }
 async function saveConfiguration(forget=false){
  const form=$("#web-config-form");const buttons=form.querySelectorAll("button");buttons.forEach(b=>b.disabled=true);
  try{
   const result=await api("/api/web/config","POST",{provider:$("#web-provider").value,searxng_url:$("#searxng-url").value.trim(),api_key:forget?"":$("#web-api-key").value,persist_key:$("#web-key-storage").value==="vault",forget_key:forget});
   $("#web-api-key").value="";await refresh();render();toast(result.warning||(forget?"Websuchschlüssel entfernt.":"Suchanbieter gespeichert. Erreichbarkeit mit einer öffentlichen Suche prüfen."),!!result.warning);
  }finally{buttons.forEach(b=>b.disabled=false);}
 }
 function researchControls(){
  const s=state();
  return `${s.researchSource==="web"?`<div class="field-row"><div class="field"><label for="research-language">Suchsprache</label><select id="research-language">${options(languages,s.researchLanguage)}</select></div><div class="field"><label for="research-freshness">Zeitraum</label><select id="research-freshness">${options(periods,s.researchFreshness)}</select></div></div><p class="footnote">Anbieter: ${esc(cfg().provider_name)}. ${cfg().ready?"Zeit-/Sprachfilter hängen vom Suchindex ab; Datumsangaben fachlich prüfen.":'Noch nicht eingerichtet. <button type="button" class="text-btn" data-action="settings">Einstellungen → Websuche öffnen</button>.'} <button type="button" class="text-btn" data-action="web-setup">Einrichtung erklären</button></p>`:""}
  <details class="web-page-tools"><summary>Eine Webseite direkt einlesen</summary><p class="footnote">Öffentliche HTTPS-HTML-/Textseite ohne Anmeldung. Die Seite erhält Ihre IP-Adresse. Kein JavaScript, keine Übernahme von Browser-Cookies. Inhalt wird erst nach Ihrer Auswahl als Projektquelle gespeichert.</p>
  <form id="web-page-form" class="research-form"><input type="url" id="web-page-url" maxlength="2048" required value="${esc(W.url)}" placeholder="https://…" aria-label="Öffentliche Webseitenadresse" ${W.pageBusy?"disabled":""}><button class="button" ${!enabled()||W.pageBusy?"disabled":""}>${W.pageBusy?"Seite wird eingelesen …":"Einlesen und Vorschau"}</button></form></details>`;
 }
 function resultButtons(row,index){return row.kind?btn("Seite einlesen","web-read-result","file","compact",`data-index="${index}" ${W.pageBusy?"disabled":""}`):"";}
 function resultNote(row){return row.kind?`<p class="footnote">${row.kind==="page"?"Extrahierter Webtext":"Suchauszug · Seite noch nicht eingelesen"}${row.published?" · "+esc(row.published):""}${row.truncated?" · Text gekürzt":""}</p>`:"";}
 async function readPage(url){
  if(W.pageBusy)return;
  W.pageBusy=true;render();
  try{const result=await api("/api/web/page","POST",{url});pagePreview(result);}
  finally{W.pageBusy=false;render();}
 }
 function pagePreview(result){
  const row=result.results[0],projectId=state().project,projectName=state().data.projects.find(p=>p.id===projectId)?.name||projectId;
  modal("Webseite · gelesener Text",`<h3>${esc(row.title)}</h3><p class="path">${esc(row.url)}</p><p class="footnote">Abruf: ${esc(row.retrieved_at)}${row.truncated?" · Gekürzt auf "+state().data.limits.web_page_chars+" Zeichen":""}. ${esc(row.note||"")}</p><div class="web-page-extract prewrap">${esc(row.text)}</div><div class="card-footer"><a class="button" href="${esc(row.url)}" target="_blank" rel="noopener noreferrer">Originalseite öffnen</a><button type="button" class="button" id="web-download-page">MD herunterladen</button><button type="button" class="button primary" id="web-save-page">In ${esc(projectName)} speichern</button></div>`);
  $("#web-download-page").onclick=()=>download("webseite.md","# "+row.title+"\n\nQuelle: "+row.url+"\nAbruf: "+row.retrieved_at+(row.truncated?"\nHinweis: Text gekürzt.":"")+"\n\n"+row.text,"text/markdown");
  $("#web-save-page").onclick=async e=>{e.target.disabled=true;try{const doc=await api("/api/web/source","POST",{snapshot_id:result.snapshot_id,index:0,project_id:projectId});await refresh();toast(doc.status==="ablage"?"Originaltext abgelegt; Suchindex erst nach Anpassung der Grenzen verfügbar.":"Gelesenen Webtext als Projektquelle gespeichert.");$("#modal").close();render();}catch(error){h.fail(error);e.target.disabled=false;}};
 }
 async function saveResearch(index){
  const result=state().researchMeta;
  if(!result?.snapshot_id)throw new Error("Recherchestand fehlt. Erneut suchen.");
  const doc=await api("/api/web/source","POST",{snapshot_id:result.snapshot_id,index,project_id:state().project});await refresh();render();toast(doc.status==="ablage"?"Webquelle als Original abgelegt; Suchindex nicht vollständig eingelesen.":"Webtreffer als Projektquelle gespeichert.");
 }
 async function action(button){
  switch(button.dataset.action){
   case "web-setup":setupGuide();break;
   case "web-copy-question":W.query=state().draft.slice(0,300).replace(/[\uD800-\uDBFF]$/,"" );invalidateBudget();render();toast("Suchtext übernommen. Vor dem Senden vertrauliche Angaben entfernen.");break;
   case "web-forget-key":await saveConfiguration(true);break;
   case "web-read-result":await readPage(state().researchResults[+button.dataset.index].url);break;
   case "web-open-search":state().researchSource="web";await h.navigate("research");break;
  }
 }
 return {chatControls,bind,request,sent,reset,settings,researchControls,resultButtons,resultNote,saveResearch,action};
}
