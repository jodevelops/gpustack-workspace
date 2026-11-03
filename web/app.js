import {createAudioWorkspace} from "/static/audio.js";
import {createWebWorkspace} from "/static/websearch.js";
const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];
const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const icons = {
 chat:'<path d="M21 11a8 8 0 0 1-8 8H6l-4 3V11a9 9 0 0 1 19 0Z"/><path d="M7 9h10M7 13h7"/>',
 folder:'<path d="M3 6a2 2 0 0 1 2-2h5l2 3h7a2 2 0 0 1 2 2v10H3Z"/>',
 library:'<path d="M4 4h4v16H4zM11 4h4v16h-4zM18 5l3 14"/>',
 prompt:'<path d="m8 4-5 8 5 8M16 4l5 8-5 8M14 4l-4 16"/>',
 search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
 clock:'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
 settings:'<path d="M4 7h16M4 17h16"/><circle cx="8" cy="7" r="3" fill="currentColor"/><circle cx="16" cy="17" r="3" fill="currentColor"/>',
 plus:'<path d="M12 5v14M5 12h14"/>',
 file:'<path d="M6 2h8l5 5v15H6Z"/><path d="M14 2v6h5M9 12h7M9 16h7"/>',
 lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>',
 shield:'<path d="m12 2 8 4v6c0 5-8 10-8 10S4 17 4 12V6Z"/><path d="m8 12 3 3 5-6"/>',
 download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
 upload:'<path d="M12 16V4m-5 5 5-5 5 5M4 17v4h16v-4"/>',
 x:'<path d="m6 6 12 12M18 6 6 18"/>',
 copy:'<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M15 8V3H3v13h5"/>',
 edit:'<path d="m14 5 5 5M4 20l5-1L21 7l-5-5L4 14Z"/>',
 trash:'<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/>',
 eye:'<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
 image:'<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="2"/><path d="m3 17 6-5 4 3 4-6 4 8"/>',
 link:'<path d="m9 15 6-6M8 16l-2 2a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0m2 1 2-2a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0" transform="translate(1 0) scale(.92)"/>',
 bolt:'<path d="m13 2-9 12h7l-1 8 10-13h-7Z"/>',
 menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
 panel:'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M15 4v16"/>',
 chevron:'<path d="m9 5 7 7-7 7"/>',
 check:'<path d="m4 12 5 5L20 6"/>',
 globe:'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
 code:'<path d="m7 6-5 6 5 6m10-12 5 6-5 6m-3-14-4 16"/>',
 play:'<path d="m8 4 12 8-12 8Z"/>',
 stop:'<rect x="5" y="5" width="14" height="14" rx="1"/>',
 attach:'<path d="m8 13 7-7a3 3 0 0 1 4 4L9 20a5 5 0 0 1-7-7L13 2"/>',
 info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7v.1"/>',
 audio:'<path d="M4 9v6M8 5v14M12 2v20M16 6v12M20 9v6"/>'
};
const icon = name => `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.file}</svg>`;
const btn = (label,action,ic="",cls="",attrs="") => `<button type="button" class="button ${cls}" data-action="${action}" ${attrs}>${ic?icon(ic):""}${label}</button>`;
const ibtn = (label,action,ic,attrs="") => `<button type="button" class="icon-btn" data-action="${action}" title="${esc(label)}" aria-label="${esc(label)}" ${attrs}>${icon(ic)}</button>`;
const limitValue = key => S.data.limits[key];
const prettySize = n => n>1048576?(n/1048576).toFixed(1)+" MB":Math.max(1,Math.round(n/1024))+" KB";
const prettyDate = s => s ? new Date(s).toLocaleString("de-CH",{dateStyle:"short",timeStyle:"short"}) : "–";
const options = (items,current) => items.map(([value,label])=>`<option value="${esc(value)}" ${value===current?"selected":""}>${esc(label)}</option>`).join("");
let currentLimits=null,currentModels=[];
const defaultSettings = () => ({model:"gpt-oss-120b",system_prompt:"",temperature:.3,top_p:1,max_tokens:Math.min(8192,currentLimits?.output_max_tokens||8192,currentModels.find(m=>m.id==="gpt-oss-120b")?.deployment_output_tokens||Infinity,(currentModels.find(m=>m.id==="gpt-oss-120b")?.deployment_context_tokens||Infinity)-1),context_chars:Math.min(48000,currentLimits?.context_max_chars||48000)});
const S = {data:null,view:"chat",project:"workspace",thread:null,messages:[],docs:[],selected:new Set(),attachments:new Set(),skills:new Set(),
 settings:defaultSettings(),draft:"",semantic:false,tab:"sources",panelOpen:false,sideOpen:false,
 busy:false,abort:null,stage:"antwortet",connected:false,sourceHits:[],sourceNotes:[],filter:"",promptFilter:"all",
 researchResults:[],researchQuery:"",researchSource:"web",researchBusy:false,researchLanguage:"de",researchFreshness:"all",researchMeta:null,
 researchResultSource:"",researchResultQuery:"",researchRetrievedAt:"",labResult:null,
 labCode:"",labDocs:new Set(),libraryGlobal:false,importMode:"text",history:[],historyQuery:""};
let budgetResult=null,budgetRevision=0;
const budgetHint="Texttokenzahl ist vor der Anfrage nur geschätzt. Exakte Nutzung wird angezeigt, wenn GPUStack sie liefert.";
function invalidateBudget(){budgetResult=null;budgetRevision++;const result=$("#budget-result");if(result)result.textContent=budgetHint;}
let toastTimer;
function toast(message,error=false) {
 const t=$("#toast"); t.textContent=message; t.className="visible"+(error?" error":"");
 clearTimeout(toastTimer); toastTimer=setTimeout(()=>t.className="",error?8000:4000);
}
async function api(path,method="GET",body,signal) {
 const headers={}; if(method!=="GET") headers["X-CSRF-Token"]=S.data?.csrf || "";
 if(body && !(body instanceof FormData)) headers["Content-Type"]="application/json";
 const r=await fetch(path,{method,headers,body:body?(body instanceof FormData?body:JSON.stringify(body)):undefined,signal});
 if(!r.ok) { let message="Der lokale Dienst ist nicht erreichbar."; try {const data=await r.json();message=typeof data.detail==="string"?data.detail:"Bitte Eingaben und Wertebereiche prüfen.";}catch{} const error=new Error(message);error.status=r.status;throw error; }
 return r.json();
}
async function refresh() {
 invalidateBudget();
 S.data=await api("/api/bootstrap");currentLimits=S.data.limits;currentModels=S.data.models;
 if(!S.thread){S.settings.context_chars=Math.min(S.settings.context_chars,currentLimits.context_max_chars);S.settings.max_tokens=Math.min(S.settings.max_tokens,outputCeiling(S.settings.model));}
 if(!S.data.projects.some(x=>x.id===S.project)){AudioUI.reset();S.project=S.data.projects[0].id;}
 S.docs=await api("/api/documents?project_id="+encodeURIComponent(S.project));
 S.selected=new Set([...S.selected].filter(id=>S.docs.some(d=>d.id===id)));
 S.attachments=new Set([...S.attachments].filter(id=>S.docs.some(d=>d.id===id)));
}
const project = () => S.data.projects.find(p=>p.id===S.project);
const chatModels = () => S.data.models.filter(m=>m.type==="chat");
const modelOptions = current => options(chatModels().map(m=>[m.id,m.id]),current);
const AudioUI=createAudioWorkspace({state:()=>S,api,refresh,render,esc,icon,btn,ibtn,field,options,modelOptions,modal,toast,fail:e=>fail(e),prettyDate,prettySize,download,modelInfo,outputCeiling});
const WebUI=createWebWorkspace({state:()=>S,api,render,refresh,esc,icon,btn,options,modal,toast,download,invalidateBudget,fail:e=>fail(e),navigate});
function markdown(value) {
 const tick=String.fromCharCode(96);
 const parts=String(value).split(tick.repeat(3));
 return parts.map((p,i)=> i%2 ? "<pre><code>"+esc(p.replace(/^[\w+-]*\n/,""))+"</code></pre>" :
  esc(p).replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>").replace(new RegExp(tick+"([^"+tick+"\\n]+)"+tick,"g"),"<code>$1</code>")).join("");
}
function render() {
 if(!S.data) return;
 const nav=[["chat","Chat","chat"],["history","Verlauf","clock"],["projects","Projekte","folder"],["library","Library","library"],["audio","Audio & Transkripte","audio"],["prompts","Prompts & Skills","prompt"],["research","Recherche","globe"],["routines","Routinen","clock"],["lab","Datenlabor","code"]];
 const names=Object.fromEntries(nav.map(([a,b])=>[a,b])); names.settings="Einstellungen";
 const current=S.data.threads.find(t=>t.id===S.thread);
 $("#app").innerHTML=`<div class="shell">
 <aside class="sidebar ${S.sideOpen?"open":""}" aria-label="Hauptnavigation">
  <div class="brand"><span class="brand-mark">A</span><div><div class="brand-name">Arbeitsraum</div><small>MIT GPUSTACK</small></div></div>
  <button class="newchat" data-action="new-chat">${icon("plus")}Neuer Chat</button>
  <nav class="navgroup">${nav.map(([id,label,ic])=>`<button class="navbutton ${S.view===id?"active":""}" data-view="${id}" ${S.view===id?'aria-current="page"':""}>${icon(ic)}${label}${id==="library"&&S.docs.length?`<span class="count">${S.docs.length}</span>`:""}</button>`).join("")}</nav>
  <div class="side-scroll"><div class="side-title">PROJEKTE ${ibtn("Projekt erstellen","new-project","plus")}</div>
   ${S.data.projects.map(p=>`<button class="project-link ${S.project===p.id?"active":""}" data-project="${p.id}"><i class="folder-dot"></i><span>${esc(p.name)}</span></button>`).join("")}
   <div class="side-title">LETZTE CHATS</div>
   ${S.data.threads.filter(t=>t.project_id===S.project).slice(0,12).map(t=>`<button class="thread-link ${S.thread===t.id?"active":""}" data-thread="${t.id}">${icon("chat")}<span>${esc(t.title)}</span></button>`).join("") || '<p class="side-empty">Deine Gespräche bleiben hier erhalten.</p>'}
  </div>
  <div class="side-footer"><span class="avatar">LO</span><div>Lokaler Arbeitsraum<br><small>Persönlicher PoC · v${esc(S.data.version)}</small></div>${ibtn("Einstellungen","settings","settings")}</div>
 </aside>
 <main class="workarea" id="content">
  <header class="topbar">${ibtn("Navigation öffnen","menu","menu",'class="mobile-menu"').replace('class="icon-btn"','class="icon-btn mobile-menu"').replace('class="mobile-menu"',"")}
   <div class="topbar-title"><div class="breadcrumbs">${icon("folder")}${esc(project().name)}${icon("chevron")}${esc(names[S.view])}</div><h1>${S.view==="chat"?esc(current?.title || "Neuer Chat"):esc(names[S.view])}</h1></div>
   <button class="connection" data-action="settings" title="GPUStack-Verbindung einrichten"><span class="status-dot ${S.connected?"connected":""}"></span><span class="label">${S.connected?"Modellliste erreichbar":S.data.connection.base_url?"Endpunkt konfiguriert":"GPUStack verbinden"}</span>${icon("settings")}</button>
  </header>
  ${S.view==="chat"?chatView():`<div class="page"><div class="page-inner">${pageView()}</div></div>`}
 </main></div><input type="file" id="file-input" class="hidden" multiple accept=".pdf,.docx,.xlsx,.csv,.tsv,.txt,.md,.json,.png,.jpg,.jpeg,.webp,.mp3,.wav,.m4a,.mp4,.ogg,.webm">`;
 bindInputs();WebUI.bind();
 if(S.view==="audio")AudioUI.bind();
 if(S.view==="chat") {renderMessages();renderInspector();renderChips();}
}
function chatView() {
 return `<div class="toolbar"><div class="toolbar-group"><select id="chat-model" class="model-picker" aria-label="Chatmodell" ${S.busy?"disabled":""}>${modelOptions(S.settings.model)}</select><span class="badge">${S.data.models.find(m=>m.id===S.settings.model)?.vision?"Text + Bild":"Text"}</span></div><div class="toolbar-group">${S.thread?btn('<span class="export-label">Export</span>',"export-chat","download","subtle"):""}${S.thread?ibtn("Chat umbenennen","rename-thread","edit"):""}${ibtn("Kontext und Parameter","toggle-panel","panel",`aria-expanded="${S.panelOpen}" aria-controls="context-panel"`)}</div></div>
 <div class="chat-layout ${S.panelOpen?"panel-open":""}"><section class="chat-column" aria-label="Chat"><div class="chat-scroll" id="chat-scroll"><div id="messages"></div></div>
  <div class="composer-wrap"><form class="composer" id="chat-form"><div id="selection-chips" class="selection-chips"></div>
   <textarea id="message-input" maxlength="${limitValue("message_chars")}" aria-label="Nachricht" placeholder="Nachricht schreiben oder eine Frage zu deinen Quellen stellen …" rows="2" ${S.busy?"disabled":""}>${esc(S.draft)}</textarea>
   ${WebUI.chatControls()}<div class="composer-bottom"><div class="toolbar-group">${ibtn("Dateien hinzufügen","upload","attach")}${ibtn("Systemprompt bearbeiten","prompt-panel","prompt")}<span class="compose-label">${S.selected.size?S.selected.size+" Quellen ausgewählt":"Quellen bewusst auswählen"}</span></div>
    ${S.busy?'<button type="button" class="send" data-action="stop">'+icon("stop")+'Stoppen</button>':'<button type="submit" class="send">Senden '+icon("play")+'</button>'}
   </div></form><div class="privacy-line">${icon("lock")}Ablage lokal · Modellanfragen an deinen Endpunkt · Antworten prüfen</div></div></section>
 <aside id="context-panel" class="inspector ${S.panelOpen?"open":""}" aria-label="Kontext"><div class="inspector-top"><h3>Kontext</h3><span class="source-count">${S.selected.size} Quellen</span>${ibtn("Kontext schließen","close-panel","x")}</div>
 <div class="tabs" role="tablist" aria-label="Kontextbereiche">${[["sources","Quellen"],["instructions","Anweisungen"],["parameters","Parameter"]].map(([id,label])=>`<button class="tab ${S.tab===id?"active":""}" data-tab="${id}" role="tab" aria-selected="${S.tab===id}">${label}</button>`).join("")}</div><div class="inspector-body" id="inspector-body" role="tabpanel"></div></aside></div>`;
}
function renderMessages() {
 const root=$("#messages"); if(!root) return;
 if(!S.messages.length) {
  root.innerHTML=`<div class="welcome"><div class="welcome-icon">${icon("chat")}</div><div class="eyebrow">DEIN LOKALER KI-ARBEITSRAUM</div><h2>Womit beginnen wir?</h2><p>Mit deinen Modellen denken, Dokumente befragen und Ergebnisse festhalten. Alles in einem Arbeitsraum.</p>
   <div class="quick-grid"><button class="quick-card" data-action="quick-document">${icon("file")}<b>Dokument befragen</b><span>Antworten mit Quellenstellen</span></button><button class="quick-card" data-action="quick-metadata">${icon("prompt")}<b>Metadaten strukturieren</b><span>Personen, Orte und Daten</span></button><button class="quick-card" data-view="lab">${icon("code")}<b>Daten untersuchen</b><span>Berechnen und exportieren</span></button></div>
   <div class="connection-note">${icon(S.data.connection.base_url?"shield":"link")}<div>${S.data.connection.base_url?"Dein Endpunkt ist konfiguriert. Wähle rechts Quellen und Anweisungen für dieses Gespräch.":'Richte zuerst deinen GPUStack-Endpunkt ein. Projekte und Dokumente kannst du bereits vorbereiten. <button class="text-btn" data-action="settings">Verbindung einrichten</button>'}</div></div></div>`;
  return;
 }
 root.innerHTML=S.messages.map((m,i)=>`<article class="message ${m.role}" data-message-index="${i}"><div class="message-head">${m.role==="assistant"?'<span class="mini-mark">A</span>':""}${m.role==="user"?"Du":esc(m.metadata?.model || S.settings.model)}${m.metadata?.status==="streaming"?'<span class="waiting">'+esc(S.stage)+'</span>':""}</div>
  ${mediaCards(m.metadata?.documents || (m.metadata?.images||[]).map(id=>S.docs.find(d=>d.id===id)).filter(Boolean))}
  ${m.metadata?.reasoning?`<details class="model-reasoning" ${m.metadata.status==="streaming"?"open":""}><summary>Vom Modell gelieferte Begründung / CoT</summary><p class="footnote">Vom Endpunkt ausgegebener Reasoning-Text; kein garantierter Einblick in interne Modellabläufe. Wird nicht in Folgeanfragen übernommen.</p><div class="message-body">${markdown(m.metadata.reasoning)}</div></details>`:""}
  <div class="message-body">${markdown(m.content)}</div>
  ${m.role==="assistant"&&m.metadata?.status!=="streaming"&&!m.metadata?.reasoning?'<p class="token-usage">Kein separater Reasoning-Text vom Endpunkt geliefert.</p>':""}
  ${m.metadata?.usage&&Object.keys(m.metadata.usage).length?`<p class="token-usage">${usageLabel(m.metadata.usage)}</p>`:""}
  ${m.metadata?.status==="error"?`<p class="message-error">${esc(m.metadata?.error || "Anfrage fehlgeschlagen. Verbindung prüfen.")}</p>`:""}
  ${m.metadata?.status==="cancelled"?'<p class="message-error">Antwort wurde abgebrochen.</p>':""}
  ${m.metadata?.finish_reason==="length"?'<p class="message-error">Ausgabelimit erreicht. Die Antwort ist unvollständig; bei Reasoning-Modellen kann auch die Begründung Ausgabetokens verbrauchen. Budget unter Kontext → Parameter erhöhen und erneut anfragen.</p>':""}
  ${m.metadata?.web_search?`<p class="web-query-note">${icon("globe")}Websuche: ${esc(m.metadata.web_search.provider)} · Suchtext: ${esc(m.metadata.web_search.sent_query)} · ${esc(prettyDate(m.metadata.web_search.retrieved_at))}</p>`:""}
  ${m.metadata?.notes?.length?`<details class="context-note"><summary>Umfang der Quellenauswertung</summary>${m.metadata.notes.map(n=>`<p>${esc(n)}</p>`).join("")}</details>`:""}
  ${m.metadata?.sources?.length?`<div class="source-tags">${m.metadata.sources.map((x,k)=>`<button data-proof="${i}:${k}">${esc(x.label)} · ${esc(x.name)}</button>`).join("")}</div>`:""}
  ${m.role==="assistant"&&m.metadata?.status!=="streaming"?`<div class="message-footer">${ibtn("Antwort kopieren","copy-message","copy",`data-index="${i}"`)}${ibtn("Antwort herunterladen","download-message","download",`data-index="${i}"`)}${m.created?esc(prettyDate(m.created)):""}</div>`:""}
 </article>`).join("");
 const scroll=$("#chat-scroll"); scroll.scrollTop=scroll.scrollHeight;
}
function updateStreamingMessage(){
 const index=S.messages.length-1,m=S.messages[index],article=$(`[data-message-index="${index}"]`),scroll=$("#chat-scroll");if(!article)return;
 const nearEnd=scroll.scrollHeight-scroll.scrollTop-scroll.clientHeight<100;
 const body=$(':scope > .message-body',article);body.innerHTML=markdown(m.content);
 if(m.metadata.reasoning){let details=$(".model-reasoning",article);if(!details){details=document.createElement("details");details.className="model-reasoning";details.open=true;details.innerHTML='<summary>Vom Modell gelieferte Begründung / CoT</summary><p class="footnote">Vom Endpunkt gelieferter Reasoning-Text.</p><div class="message-body"></div>';body.before(details);}$(".message-body",details).innerHTML=markdown(m.metadata.reasoning);}
 if(nearEnd)scroll.scrollTop=scroll.scrollHeight;
}
function renderChips() {
 const c=$("#selection-chips"); if(!c) return;
 c.innerHTML=mediaCards([...new Set([...S.selected,...S.attachments])].map(id=>S.docs.find(d=>d.id===id)).filter(Boolean),true)+[...S.selected].map(id=>{const d=S.docs.find(x=>x.id===id);return d?`<span class="chip">${icon(d.status==="bild"?"image":"file")}<span>${esc(d.name)}</span><button data-remove-source="${id}" aria-label="${esc(d.name)} abwählen">${icon("x")}</button></span>`:"";}).join("")+
 [...S.skills].map(id=>{const p=S.data.prompts.find(x=>x.id===id);return p?`<span class="chip">${icon("bolt")}<span>${esc(p.name)}</span><button data-remove-skill="${id}" aria-label="Skill abwählen">${icon("x")}</button></span>`:"";}).join("");
 const count=$(".source-count"); if(count) count.textContent=S.selected.size+" Quellen";
 const compose=$(".compose-label"); if(compose) compose.textContent=S.selected.size?S.selected.size+" Quellen ausgewählt":"Quellen bewusst auswählen";
}
function renderInspector() {
 const el=$("#inspector-body"); if(!el) return;
 if(S.tab==="sources") {
  el.innerHTML=`<div class="panel-label">Für dieses Gespräch</div>
   ${!S.docs.length?`<div class="source-empty">${icon("library")}<h3>Dein Wissen hinzufügen</h3><p>Lade Dokumente oder Bilder hoch und wähle sie als Kontext aus.</p>${btn("Dateien hinzufügen","upload","plus","compact")}</div>`:
   `<div class="stack">${btn("Dateien hinzufügen","upload","plus","compact")}</div>${S.docs.filter(d=>d.status!=="audio").map(d=>`<div class="source-row"><input id="source-${d.id}" type="checkbox" data-source="${d.id}" ${["ablage","ohne_text"].includes(d.status)?"disabled":""} ${S.selected.has(d.id)?"checked":""}><label for="source-${d.id}">${esc(d.name)}<small>${d.status==="bild"?"Bild · benötigt Bildmodell":d.chunks?d.chunks+" Abschnitte · "+(d.indexed===d.chunks?"semantisch indexiert":"Textsuche"):d.status==="ablage"?"Nur Original · zuerst einlesen":"Keine Textebene"}</small></label>${ibtn("Quelle ansehen","preview-doc","eye",`data-id="${d.id}"`)}</div>`).join("")}`}
   <div class="panel-rule"></div><label class="toggle-line"><span>Semantische Suche<br><small class="muted">Embeddings über GPUStack</small></span><input type="checkbox" id="semantic" ${S.semantic?"checked":""}></label>
   <p class="panel-note">Aus ausgewählten Dokumenten gehen höchstens ${limitValue("rag_hits")} passende Textabschnitte an das Modell; es liest dabei nicht die ganze Datei. Die Textsuche funktioniert ohne Index. Semantische Indizes erstellst du in der Library.</p>
   ${S.sourceHits.length?`<div class="panel-rule"></div><div class="panel-label">Letzte Quellenauswahl</div>${S.sourceNotes.map(n=>`<p class="panel-note">${esc(n)}</p>`).join("")}${S.sourceHits.map(x=>`<details class="source-proof"><summary><b>${esc(x.label)}</b> · ${esc(x.name)}<br><span class="muted">${esc(x.location)}</span></summary><p>${esc(x.content)}</p></details>`).join("")}`:""}`;
 } else if(S.tab==="instructions") {
  el.innerHTML=`<div class="field"><label for="system-template">Gespeicherten Prompt übernehmen</label><select id="system-template"><option value="">Vorlage wählen …</option>${options(S.data.prompts.filter(p=>p.kind==="system").map(p=>[p.id,p.name]),"")}</select></div>
   <div class="field"><label for="system-prompt">Systemprompt dieses Chats</label><textarea id="system-prompt" maxlength="${limitValue("prompt_chars")}" rows="7" placeholder="Wie soll das Modell arbeiten?">${esc(S.settings.system_prompt)}</textarea><small>Ergänzt die Projektanweisungen. Wird mit dem Chat gespeichert.</small></div>
   <div class="panel-label">Skills aktivieren</div>${S.data.prompts.filter(p=>p.kind==="skill").map(p=>`<div class="source-row"><input type="checkbox" id="skill-${p.id}" data-skill="${p.id}" ${S.skills.has(p.id)?"checked":""}><label for="skill-${p.id}">${esc(p.name)}</label></div>`).join("")}
   <div class="panel-rule"></div><div class="panel-label">Projektgedächtnis</div><p class="panel-note">${esc(project().memory || "Noch keine festen Projektnotizen. Du bestimmst selbst, was sich das Modell merken soll.")}</p>${btn("Projektnotizen bearbeiten","edit-project","edit","subtle",`data-id="${S.project}"`)}
   <details class="source-proof"><summary>Projekt-Systemprompt</summary><p>${esc(project().system_prompt || "Kein Projekt-Systemprompt.")}</p></details><p class="panel-note">Skills sind wiederverwendbare Arbeitsanweisungen. Sie führen keine Programme oder Aktionen aus.</p>`;
 } else {
  el.innerHTML=`${modelInfo(S.settings.model)}<div class="panel-label">Antwortverhalten</div><div class="field"><label for="temperature">Temperatur <span id="temp-value" class="muted">${S.settings.temperature}</span></label><input type="range" id="temperature" min="0" max="2" step="0.1" value="${S.settings.temperature}"><small>Niedrig: gleichmäßiger. Hoch: mehr Variation.</small></div>
   <div class="field"><label for="top-p">Top P</label><input type="number" id="top-p" value="${S.settings.top_p}" min=".01" max="1" step=".05"><small>Meist bei 1 belassen, wenn du die Temperatur regelst.</small></div>
   <div class="field"><label for="max-tokens">Maximale Ausgabetokens</label><input type="number" id="max-tokens" value="${S.settings.max_tokens}" min="1" max="${outputCeiling(S.settings.model)}" step="1"><small>Antwort und gegebenenfalls Reasoning teilen dieses Budget. Mehr Ausgabe benötigt mehr Zeit und Platz im Modellkontext.</small></div>
   <div class="field"><label for="context-chars">Eingabebudget in Zeichen</label><input type="number" id="context-chars" value="${S.settings.context_chars}" min="0" max="${limitValue("context_max_chars")}" step="1"><small>0 = lokale Zeichenprüfung deaktiviert. Optionaler Schutz vor versehentlich grossen Anfragen: Verlauf, Anweisungen und Quellenauszüge. Keine Modell-Kontextgrösse; GPUStack-Token- und Anfragegrössenlimits gelten weiterhin.</small></div>
   ${btn("Eingabe lokal prüfen","check-budget","info","compact")}<div id="budget-result" class="panel-note">${budgetResult||budgetHint}</div><div class="panel-rule"></div><p class="panel-note">Parameter müssen vom jeweiligen Deployment unterstützt werden. Der Verlauf wird bei Überschreitung nicht still gekürzt.</p>${S.thread?btn("Einstellungen speichern","save-thread","check","compact"):""}`;
 }
 bindPanel();
}
function heading(title,description,action="") {return `<div class="page-heading"><div><h2>${title}</h2><p>${description}</p></div>${action}</div>`;}
function empty(ic,title,description,action="") {return `<div class="empty">${icon(ic)}<h3>${title}</h3><p>${description}</p>${action}</div>`;}
function pageView() {
 switch(S.view) {
 case "history": return heading("Gespräche wiederfinden","Suche in den Titeln und Nachrichten dieses Projekts.")+
  `<div class="filters"><div class="search">${icon("search")}<input type="text" id="history-search" value="${esc(S.historyQuery)}" maxlength="200" placeholder="Gespräche durchsuchen …" aria-label="Chatverlauf durchsuchen"></div></div><div id="history-results">${historyResults()}</div>`;
 case "projects": return heading("Ein Kontext für jedes Vorhaben","Projekte bündeln Gespräche, Quellen und feste Arbeitsanweisungen.",btn("Neues Projekt","new-project","plus","primary"))+
  `<div class="cards">${S.data.projects.map(p=>`<article class="card"><div class="card-icon">${icon("folder")}</div><h3>${esc(p.name)}</h3><p>${esc(p.description || "Noch keine Beschreibung.")}</p><div class="card-meta"><span>${p.threads} Chats</span><span>${p.documents} Dokumente</span><span>${p.memory?"Mit Projektnotizen":"Ohne Projektnotizen"}</span></div><div class="card-footer"><button class="button compact" data-project="${p.id}">Öffnen</button>${btn("Bearbeiten","edit-project","edit","compact",`data-id="${p.id}"`)}${ibtn("Projekt löschen","delete-project","trash",`data-id="${p.id}"`)}</div></article>`).join("")}</div>`;
 case "library": return libraryView();
 case "audio": return AudioUI.view();
 case "prompts": return promptsView();
 case "research": return researchView();
 case "routines": return routinesView();
 case "lab": return labView();
 case "settings": return settingsView();
 default: return "";
 }
}
function historyResults() {
 return S.history.length?`<div class="table-wrap"><table><thead><tr><th>Gespräch</th><th>Modell</th><th>Zuletzt geändert</th><th></th></tr></thead><tbody>${S.history.map(t=>`<tr><td><b>${esc(t.title)}</b><br><small class="muted">${t.messages} Nachrichten</small></td><td>${esc(t.model)}</td><td>${prettyDate(t.updated)}</td><td><button class="button compact" data-thread="${t.id}">Öffnen</button></td></tr>`).join("")}</tbody></table></div>`:empty("chat","Noch keine passenden Gespräche","Neue Chats werden automatisch gespeichert. Der Verlauf bleibt auch nach einem Neustart verfügbar.");
}
function libraryView() {
 const filtered=S.docs.filter(d=>d.name.toLowerCase().includes(S.filter.toLowerCase()));
 return heading("Dokumente, die mitdenken","Deine Ablage für Originale, Quellen und Transkripte. Dateien werden beim Hochladen lokal gespeichert.",btn("Dateien hochladen","upload","upload","primary"))+
 `<div class="dropzone" id="dropzone"><div class="drop-info">${icon("upload")}<div><b>Dateien hier ablegen</b><p>PDF, Word, Excel, CSV, Text, Bilder und Audio · bis ${limitValue("file_mb")} MiB je Datei</p></div></div><label class="check-label"><input type="checkbox" id="library-global" ${S.libraryGlobal?"checked":""}>Projektübergreifend ablegen</label><div class="field"><label for="import-mode">Verarbeitung</label><select id="import-mode">${options([["text","Text einlesen; bei Ressourcengrenze Original ablegen"],["original","Nur Original ablegen (für grosse Dateien / Datenlabor)"]],S.importMode)}</select></div></div>
 <div class="info">${icon("info")}<span>Upload und Projektablage haben dieselbe Dateigrenze. Bis ${limitValue("text_chars").toLocaleString("de-CH")} Textzeichen werden lokal für die Suche eingelesen. Ein grösseres Original bleibt vollständig erhalten. RAG zeigt passende Ausschnitte; Gesamtstatistiken aus Tabellen im Datenlabor berechnen. <button class="text-btn" data-action="settings">Ressourcengrenzen anpassen</button></span></div>
 <div class="filters"><div class="search">${icon("search")}<input id="library-search" type="text" placeholder="Dateien suchen …" value="${esc(S.filter)}" aria-label="Dateien suchen"></div><span class="badge">${esc(project().name)} + gemeinsame Library</span>${S.selected.size?btn(S.selected.size+" im Chat verwenden","use-sources","chat","compact"):""}</div>
 <div id="document-table">${documentTable(filtered)}</div>
 <p class="footnote">Ein Upload löst keine Modellanfrage aus. „Indexieren“ sendet die Textabschnitte an das gewählte Embedding-Modell. Quellen können in Antworten gespeichert bleiben, auch wenn das Original später gelöscht wird.</p>`;
}
function documentTable(docs) {
 if(!docs.length) return empty("library","Hier beginnt deine Wissensbasis","Füge eine erste Datei hinzu. Danach kannst du sie ansehen, gezielt befragen und bei Bedarf semantisch indexieren.");
 return `<div class="table-wrap"><table><thead><tr><th>Datei</th><th>Verarbeitung</th><th>Größe</th><th>Aktionen</th></tr></thead><tbody>${docs.map(d=>`<tr><td><div class="file-name"><input type="checkbox" data-source="${d.id}" aria-label="${esc(d.name)} auswählen" ${S.selected.has(d.id)?"checked":""} ${["audio","ablage","ohne_text"].includes(d.status)?'disabled title="Zuerst Text einlesen oder transkribieren"':""}><span class="file-tile">${icon(d.status==="bild"?"image":d.status==="audio"?"audio":"file")}</span><span>${esc(d.name)}<small>${d.status==="ablage"?esc(d.note)+"<br>":""}${d.project_id?"Projektquelle":"Gemeinsame Library"} · ${prettyDate(d.created)}</small></span></div></td><td><span class="badge ${d.status==="ohne_text"?"yellow":d.indexed&&d.indexed===d.chunks?"green":""}">${d.status==="bild"?"Bild":d.status==="audio"?"Audio":d.status==="ohne_text"?"Keine Textebene":d.status==="ablage"?"Original abgelegt":d.chunks&&d.indexed===d.chunks?"Semantisch indexiert":d.chunks+" Textabschnitte"}</span></td><td class="muted">${prettySize(d.size)}</td><td><div class="row-actions">${ibtn("Vorschau","preview-doc","eye",`data-id="${d.id}"`)}${d.status==="ablage"||d.chunks?ibtn("Text erneut einlesen","reprocess-doc","play",`data-id="${d.id}"`):""}${d.chunks?ibtn("Semantisch indexieren","index-doc","bolt",`data-id="${d.id}"`):""}${d.status==="audio"?ibtn("Transkribieren","transcribe-doc","audio",`data-id="${d.id}"`):""}<a class="icon-btn" href="/api/documents/${d.id}/download" aria-label="Original herunterladen" title="Original herunterladen">${icon("download")}</a>${ibtn("Datei löschen","delete-doc","trash",`data-id="${d.id}"`)}</div></td></tr>`).join("")}</tbody></table></div>`;
}
function promptsView() {
 const list=S.data.prompts.filter(p=>S.promptFilter==="all"||S.promptFilter===p.kind);
 return heading("Gute Arbeitsweisen wiederverwenden","Systemprompts geben die Haltung vor. Skills ergänzen eine konkrete Methode.",btn("Neue Vorlage","new-prompt","plus","primary"))+
 `<div class="subtabs">${[["all","Alle Vorlagen"],["system","Systemprompts"],["skill","Skills"]].map(([key,label])=>`<button data-prompt-filter="${key}" class="${S.promptFilter===key?"active":""}">${label}</button>`).join("")}</div><div class="cards">${list.map(p=>`<article class="card"><div class="status-line"><span class="card-icon">${icon(p.kind==="skill"?"bolt":"prompt")}</span><span class="badge">${p.kind==="skill"?"Skill":"Systemprompt"}</span></div><h3>${esc(p.name)}</h3><p class="card-preview">${esc(p.content)}</p><div class="card-footer">${btn("Im Chat verwenden","apply-prompt","plus","compact",`data-id="${p.id}"`)}${ibtn("Vorlage bearbeiten","edit-prompt","edit",`data-id="${p.id}"`)}${ibtn("Vorlage löschen","delete-prompt","trash",`data-id="${p.id}"`)}</div></article>`).join("")}</div>`;
}
function researchView() {
 const providers=S.data.research_sources||[{id:"crossref",name:"Crossref"},{id:"wikidata",name:"Wikidata"}];
 const resultProvider=providers.find(p=>p.id===S.researchResultSource);
 return heading("Gezielt recherchieren","Suche in verfügbaren Datenquellen und übernimm passende Treffer in dein Projekt.")+
 `<div class="info ${S.data.connection.internet_enabled?"":"warning"}">${icon("globe")}<span>${S.data.connection.internet_enabled?"Externe Recherche ist freigegeben. Suchtext und ein gegebenenfalls hinterlegter Recherchekontakt gehen an die gewählte Datenquelle. Keine Chats, GPUStack-Schlüssel oder Projektdateien.":'Externe Recherche ist deaktiviert. <button class="text-btn" data-action="settings">In den Einstellungen freigeben</button>, wenn Suchbegriffe das lokale System verlassen dürfen.'}</span></div>
 <form id="research-form" class="research-form"><input type="text" id="research-query" maxlength="300" minlength="2" required ${S.researchBusy?"disabled":""} placeholder="Öffentlichen Suchbegriff eingeben …" value="${esc(S.researchQuery)}" aria-label="Rechercheanfrage"><select id="research-source" aria-label="Datenquelle" ${S.researchBusy?"disabled":""}>${options(providers.map(p=>[p.id,p.name]),S.researchSource)}</select><button class="button primary" ${!S.data.connection.internet_enabled||S.researchBusy?"disabled":""}>${icon("search")}${S.researchBusy?"Suche läuft …":"Suchen"}</button></form>
 ${WebUI.researchControls()}<p class="footnote">Crossref: Publikationsmetadaten. Wikidata: Entitäten. GND/lobid: Normdaten. DataCite: DOI-Metadaten zu Forschungsobjekten. Websuche: allgemeine Suchtreffer; einzelne Webseiten gezielt einlesen. Wikidata benötigt einen Recherchekontakt unter Einstellungen.</p>
 ${S.researchResults.length?`<p class="footnote">Treffer aus ${esc(resultProvider?.name||S.researchResultSource)} · Suchtext: ${esc(S.researchResultQuery)} · Abruf: ${esc(S.researchRetrievedAt)}${S.researchMeta?.provider?" · "+esc(S.researchMeta.provider):""}</p>`:""}
 ${(S.researchMeta?.notes||[]).map(n=>`<p class="message-error">${esc(n)}</p>`).join("")}<div class="panel-rule"></div>${S.researchResults.length?S.researchResults.map((r,i)=>`<article class="result-card"><h3>${esc(r.title)}</h3><p>${esc(r.text)}</p>${WebUI.resultNote(r)}${r.truncated&&!r.kind?'<p class="footnote">Metadatenauszug gekürzt; vollständigen Eintrag über „Quelle öffnen“ prüfen.</p>':""}<div class="result-foot"><a href="${safeURL(r.url)}" target="_blank" rel="noopener noreferrer">Quelle öffnen</a>${WebUI.resultButtons(r,i)}${btn("Als Projektquelle speichern","save-research","plus","compact",`data-index="${i}"`)}</div></article>`).join(""):empty("search","Quellen finden, gezielt übernehmen","Suche beispielsweise nach einem Forschungsbegriff oder einem Ortsnamen. Prüfe den Treffer vor der Übernahme.")}`;
}
function routinesView() {
 const list=S.data.routines.filter(r=>r.project_id===S.project);
 return heading("Wiederkehrende Aufgaben","Gespeicherte Prompts nach einem festen Intervall ausführen.",btn("Neue Routine","new-routine","plus","primary"))+
 `<div class="info">${icon("clock")}<span>Routinen laufen nur bei gestartetem lokalem Dienst und erreichbarem GPUStack. Verpasste Termine werden einmal nachgeholt. Ergebnisse erscheinen als neue Chats. Kein automatischer Internetzugriff.</span></div>
 ${list.length?`<div class="cards">${list.map(r=>`<article class="card"><div class="status-line"><span class="card-icon">${icon("clock")}</span><span class="badge ${r.enabled?"green":""}">${r.enabled?"Aktiv":"Pausiert"}</span></div><h3>${esc(r.name)}</h3><p class="card-preview">${esc(r.prompt)}</p><p class="routine-meta">Alle ${r.interval_days} Tage · ${esc(r.model)}<br>Nächster Termin: ${prettyDate(r.next_run)}<br>Status: ${esc(r.status)}</p><div class="card-footer">${btn(r.enabled?"Pausieren":"Aktivieren","toggle-routine",r.enabled?"stop":"play","compact",`data-id="${r.id}"`)}${btn("Jetzt ausführen","run-routine","play","compact",`data-id="${r.id}"`)}${ibtn("Routine löschen","delete-routine","trash",`data-id="${r.id}"`)}${r.last_thread?`<button class="button subtle compact" data-thread="${r.last_thread}">Ergebnis öffnen</button>`:""}</div></article>`).join("")}</div>`:empty("clock","Noch keine Routinen","Zum Beispiel regelmäßig eine feste Prüffrage beantworten lassen. Prompt und Projektgedächtnis werden jeweils an GPUStack übergeben.")}`;
}
const templates={
 csv: '# Vollständige Daten lokal berechnen. Dateien liegen schreibgeschützt unter /input.\nfrom pathlib import Path\nimport pandas as pd\n\nfiles = list(Path("/input").glob("*.csv"))\nif not files:\n    raise ValueError("Bitte eine CSV-Datei als Eingabe auswählen.")\ndf = pd.read_csv(files[0], sep=None, engine="python")\nprint(f"Zeilen: {len(df)} | Spalten: {len(df.columns)}")\nprint(df.isna().sum().to_string())\nreport = pd.DataFrame({\n    "Spalte": df.columns,\n    "Fehlende Werte": df.isna().sum().values,\n    "Eindeutige Werte": df.nunique().values,\n})\nreport.to_excel("/output/datenpruefung.xlsx", index=False)\nprint("Ergebnis: datenpruefung.xlsx")\n',
 pptx:'# Eine echte, editierbare PowerPoint-Datei erzeugen.\nfrom pptx import Presentation\nfrom pptx.util import Inches, Pt\nfrom pptx.dml.color import RGBColor\n\nprs = Presentation()\nprs.slide_width = Inches(13.333)\nprs.slide_height = Inches(7.5)\nfor title, body in [\n    ("Ergebnisse", "Titel und Inhalt durch geprüfte Ergebnisse ersetzen."),\n    ("Nächste Schritte", "1. Quellen prüfen\\n2. Ergebnisse abstimmen\\n3. Maßnahmen festhalten"),\n]:\n    slide = prs.slides.add_slide(prs.slide_layouts[1])\n    slide.shapes.title.text = title\n    slide.placeholders[1].text = body\n    for shape in slide.shapes:\n        if shape.has_text_frame:\n            for paragraph in shape.text_frame.paragraphs:\n                paragraph.font.name = "Aptos"\n                paragraph.font.size = Pt(26)\n                paragraph.font.color.rgb = RGBColor(24, 51, 57)\nprs.save("/output/ergebnisse.pptx")\nprint("Ergebnis: ergebnisse.pptx")\n'
};
function labView() {
 if(!S.labCode) S.labCode=templates.csv;
 return heading("Aus Antworten werden Ergebnisse","Python-Code prüfen, lokal ausführen und fertige Dateien herunterladen.")+
 `<div class="subtabs"><button class="active">Python-Labor</button><button data-action="connector">Lokaler Ordner</button><button data-action="opencode">OpenCode-Anschluss</button></div>
 <div class="info ${S.data.runner_enabled?"":"warning"}">${icon("shield")}<span>${S.data.runner_enabled?"Der Docker-Runner ist aktiviert. Jede Ausführung benötigt deine Freigabe und läuft ohne Netzwerk, ohne API-Schlüssel und mit Ressourcenlimits.":"Das Datenlabor benötigt einen separat eingerichteten Docker-Runner. Ohne diesen wird kein Code ausgeführt. Auf einem verwalteten Rechner kann die IT den Runner bereitstellen. Anleitung: README im Startpaket."}</span></div>
 <div class="panel"><div class="panel-title"><h3>${icon("code")}Code vor der Ausführung prüfen</h3><select id="lab-template" aria-label="Codevorlage" class="model-picker"><option value="">Vorlage einfügen …</option><option value="csv">CSV → Excel-Prüfbericht</option><option value="pptx">PowerPoint erstellen</option></select></div>
 <textarea id="lab-code" maxlength="500000" class="code-editor" spellcheck="false" aria-label="Python-Code">${esc(S.labCode)}</textarea>
 <div class="panel-label">Eingabedateien freigeben</div><div class="code-inputs">${S.docs.map(d=>`<label class="check-label"><input type="checkbox" data-lab-doc="${d.id}" ${S.labDocs.has(d.id)?"checked":""}>${esc(d.name)}</label>`).join("") || '<p class="small muted">Noch keine Dateien im Projekt. Über die Library hinzufügen.</p>'}</div>
 <p class="footnote">Eingaben: /input · Ergebnisse: /output · ${limitValue("runner_seconds")} Sekunden · ${limitValue("runner_memory_mb")} MiB RAM · ${limitValue("runner_output_mb")} MiB Ausgaben. pandas, openpyxl, python-pptx und matplotlib sind im Runner enthalten.</p><div class="panel-rule"></div>
 <label class="check-label"><input type="checkbox" id="lab-approve">Ich habe Code und Eingabedateien geprüft und gebe diese Ausführung frei.</label><div class="card-footer">${btn("Code ausführen","run-code","play","primary",S.data.runner_enabled?"":"disabled")}${btn("Skript herunterladen","download-code","download")}</div></div>
 ${S.labResult?`<div class="panel"><h3>${esc(S.labResult.status)}</h3><pre class="terminal">${esc(S.labResult.output || "Keine Textausgabe.")}</pre><div class="card-footer">${S.labResult.files.map(f=>`<a class="button" href="/api/jobs/${S.labResult.id}/${encodeURIComponent(f.name)}">${icon("download")}${esc(f.name)}</a>`).join("")}</div></div>`:""}`;
}
function settingsView() {
 const c=S.data.connection;
 return heading("Dein Endpunkt. Deine Ablage.","GPUStack liefert die Modelle. Der Arbeitsraum hält deine Projekte und Dokumente zusammen.")+
 `<div class="setting-grid"><div><form id="connection-form" class="panel"><div class="panel-title"><h3>${icon("link")}GPUStack verbinden</h3><span class="badge">OpenAI-kompatibel</span></div>
 <div class="field"><label for="base-url">API-Basis-URL</label><input id="base-url" type="url" placeholder="https://gpustack.intern/v1" value="${esc(c.base_url)}"><small>Die vollständige Basis-URL aus eurem GPUStack. Je nach Installation /v1 oder /v1-openai. Die VPN-Verbindung muss auf diesem Rechner aktiv sein.</small></div>
 <div class="field"><label for="api-key">API-Schlüssel</label><input id="api-key" type="password" autocomplete="new-password" placeholder="${S.data.key_status!=="Nicht hinterlegt"?"Hinterlegt · leer lassen zum Beibehalten":"Schlüssel eingeben"}"><small>Aktuell: ${esc(S.data.key_status)}. Wird nie an den Browser zurückgegeben.</small></div>
 <div class="field"><label for="key-storage">Neuen Schlüssel speichern</label><select id="key-storage"><option value="session">Nur für diese Serversitzung</option><option value="vault">Im Betriebssystem-Schlüsselspeicher</option></select><small>Kein Schlüssel in localStorage, Datenbank oder Projektdateien.</small></div>
 <div class="field-row"><div class="field"><label for="embedding-model">Embedding-Modell</label><select id="embedding-model">${options(S.data.models.filter(m=>m.type==="embedding").map(m=>[m.id,m.id]),c.embedding_model)}</select></div>
 <div class="field"><label for="rerank-model">Reranker (optional)</label><select id="rerank-model">${options([["","Ohne Reranking"],...S.data.models.filter(m=>m.type==="reranker").map(m=>[m.id,m.id])],c.rerank_model)}</select></div></div>
 <label class="check-label"><input type="checkbox" id="internet-enabled" ${c.internet_enabled?"checked":""}><span>Externe Recherche freigeben<br><small class="muted">Suchtexte dürfen an die in der Recherche gewählte Datenquelle gesendet werden.</small></span></label>
 <div class="field"><label for="research-contact">Recherchekontakt für externe APIs</label><input id="research-contact" type="text" maxlength="200" placeholder="E-Mail-Adresse oder HTTPS-Kontaktseite" value="${esc(c.research_contact||"")}"><small>Für Wikidata erforderlich. Eine echte Kontaktadresse wird zusammen mit der Anwendungskennung an die gewählte Quelle gesendet. Kein API-Schlüssel.</small></div>
 <div class="card-footer"><button type="submit" class="button primary">Speichern</button>${btn("Speichern & testen","test-connection","bolt")}${btn("Schlüssel entfernen","forget-key","","subtle")}</div>
 <div id="connection-result" class="footnote" role="status"></div></form></div>
 <div><div class="panel"><div class="panel-title"><h3>${icon("lock")}Daten & Zugriff</h3></div><div class="info-lines">
 <div><b>Persönlicher lokaler Dienst</b><small>Kein Mehrbenutzerbetrieb und noch keine SSO-Anmeldung. Zugriff über dein Betriebssystemkonto und localhost.</small></div>
 <div><b>Lokale Speicherung</b><small>Chats, Dateien, Vektoren und Projektnotizen werden unverschlüsselt in deinem Datenordner gehalten. Laufwerksverschlüsselung und Dateirechte sind erforderlich.</small><span class="path">${esc(S.data.data_dir)}</span></div>
 <div><b>Sicherung</b><small>Export enthält Chats, Quellen, Prompts und Konfiguration, keine API-Schlüssel. Datenlabor-Ausgaben separat herunterladen.</small><a class="button compact" href="/api/backup">${icon("download")}Arbeitsraum sichern</a></div>
 <div><b>SSO als nächste Ausbaustufe</b><small>Separater OIDC-Client am institutionellen Identity Provider, serverseitige Sitzungen und Projektberechtigungen. Eine GPUStack-Webanmeldung ist keine automatische Anmeldung an diesem Dienst.</small></div>
 </div></div></div></div>
 ${WebUI.settings()}<form id="limits-form" class="panel"><div class="panel-title"><h3>Ressourcengrenzen</h3></div>
 <p class="muted">Diese Grenzen gelten lokal für alle Modelle und Projekte. Höhere Werte erlauben grössere Dateien und längere Verarbeitung, benötigen aber mehr RAM, Festplatte und Zeit. Das Kontextfenster in GPUStack bleibt davon unabhängig. Neue Chatparameter können die hier gesetzten Maxima nutzen; bestehende Chats behalten ihr Budget.</p>
 <details><summary>Grenzen anzeigen und ändern</summary><div class="limit-fields">${S.data.limit_fields.map(f=>field(f.label,f.key,limitValue(f.key),"number",`required min="${f.min}" max="${f.max}" step="1"`)).join("")}</div>
 <p class="footnote">PDF-Seiten und Excel-Zeilen: 0 hebt den jeweiligen Zähler auf. Text-, Zeit- und Speichergrenzen bleiben aktiv. Eine neue Abschnittslänge gilt nach neuem Upload bzw. erneutem Einlesen; dafür wird ein bisheriger semantischer Index ersetzt. Windows begrenzt die Parserlaufzeit, hat hier aber keinen RAM-Hardlimit.</p>
 <div class="card-footer"><button class="button primary" type="submit">Grenzen speichern</button>${btn("Vorgaben eintragen","reset-limits","","subtle")}</div></details></form>
 <div class="panel"><div class="panel-title"><h3>Modellprofile</h3>${btn("Profil ergänzen","new-model","plus","compact")}</div><p class="muted">Die acht Einträge stammen aus deiner Modellliste. „Erreichbar“ bedeutet: in /models gelistet. Fähigkeiten und reale Kontextgrenzen müssen im Deployment geprüft werden.</p><div class="panel-rule"></div><div class="table-wrap"><table><thead><tr><th>Deployment-ID</th><th>Aufgabe</th><th>Status</th><th></th></tr></thead><tbody>
 ${S.data.models.map(m=>`<tr><td><b>${esc(m.id)}</b><br><small class="muted">${esc(m.description)}</small></td><td>${esc({chat:"Chat",embedding:"Embedding",reranker:"Reranking",audio:"Transkription",unclassified:"Nicht zugeordnet"}[m.type])}${m.vision?" + Bild":""}</td><td><span class="badge ${m.verified?"green":""}">${m.verified?"In Modellliste":"Ungeprüft"}</span></td><td>${ibtn("Modellprofil bearbeiten","edit-model","edit",`data-id="${esc(m.id)}"`)}</td></tr>`).join("")}</tbody></table></div></div>`;
}
function safeURL(value) {try{const u=new URL(value);return u.protocol==="https:"?esc(u.href):"#";}catch{return "#";}}
function bindInputs() {
 let searchTimer;
 $("#history-search")?.addEventListener("input",e=>{S.historyQuery=e.target.value;clearTimeout(searchTimer);searchTimer=setTimeout(async()=>{try{S.history=await api("/api/history?project_id="+encodeURIComponent(S.project)+"&q="+encodeURIComponent(S.historyQuery));if($("#history-results"))$("#history-results").innerHTML=historyResults();}catch(e){fail(e);}},200);});
 $("#file-input")?.addEventListener("change",e=>uploadFiles(e.target.files));
 $("#chat-form")?.addEventListener("submit",e=>{e.preventDefault();sendMessage().catch(fail);});
 $("#message-input")?.addEventListener("input",e=>{S.draft=e.target.value;invalidateBudget();e.target.style.height="auto";e.target.style.height=Math.min(180,e.target.scrollHeight)+"px";});
 $("#message-input")?.addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey&&!e.isComposing){e.preventDefault();sendMessage().catch(fail);}});
 $("#chat-model")?.addEventListener("change",e=>{S.settings.model=e.target.value;S.settings.max_tokens=Math.min(S.settings.max_tokens,outputCeiling(S.settings.model));invalidateBudget();render();});
 $("#library-global")?.addEventListener("change",e=>S.libraryGlobal=e.target.checked);
 $("#library-search")?.addEventListener("input",e=>{S.filter=e.target.value;$("#document-table").innerHTML=documentTable(S.docs.filter(d=>d.name.toLowerCase().includes(S.filter.toLowerCase())));});
 $("#import-mode")?.addEventListener("change",e=>S.importMode=e.target.value);
 $("#limits-form")?.addEventListener("submit",async e=>{
  e.preventDefault();const button=$('button[type="submit"]',e.target);button.disabled=true;
  try {const values=Object.fromEntries([...new FormData(e.target)].map(([k,v])=>[k,Number(v)]));await api("/api/limits","PUT",values);await refresh();render();toast("Ressourcengrenzen gespeichert.");}
  catch(err){fail(err);}finally{button.disabled=false;}
 });
 $("#connection-form")?.addEventListener("submit",e=>{e.preventDefault();saveConnection(false).catch(fail);});
 $("#research-form")?.addEventListener("submit",e=>{e.preventDefault();doResearch().catch(fail);});
 $("#research-query")?.addEventListener("input",e=>S.researchQuery=e.target.value);
 $("#research-source")?.addEventListener("change",e=>{S.researchSource=e.target.value;render();});
 $("#research-language")?.addEventListener("change",e=>S.researchLanguage=e.target.value);
 $("#research-freshness")?.addEventListener("change",e=>S.researchFreshness=e.target.value);
 $("#lab-code")?.addEventListener("input",e=>S.labCode=e.target.value);
 $("#lab-template")?.addEventListener("change",e=>{if(e.target.value){S.labCode=templates[e.target.value];$("#lab-code").value=S.labCode;}});
 const dz=$("#dropzone");
 dz?.addEventListener("dragover",e=>{e.preventDefault();dz.classList.add("dragover");});
 dz?.addEventListener("dragleave",()=>dz.classList.remove("dragover"));
 dz?.addEventListener("drop",e=>{e.preventDefault();dz.classList.remove("dragover");uploadFiles(e.dataTransfer.files);});
}
function bindPanel() {
 $("#system-prompt")?.addEventListener("input",e=>{S.settings.system_prompt=e.target.value;invalidateBudget();});
 $("#system-template")?.addEventListener("change",e=>{const p=S.data.prompts.find(x=>x.id===e.target.value);if(p){S.settings.system_prompt=p.content;invalidateBudget();renderInspector();}});
 $("#temperature")?.addEventListener("input",e=>{S.settings.temperature=+e.target.value;invalidateBudget();$("#temp-value").textContent=e.target.value;});
 for(const [id,key] of [["top-p","top_p"],["max-tokens","max_tokens"],["context-chars","context_chars"]]) $("#"+id)?.addEventListener("input",e=>{S.settings[key]=+e.target.value;invalidateBudget();});
 $("#semantic")?.addEventListener("change",e=>{S.semantic=e.target.checked;invalidateBudget();});
}
const fail = e => toast(e.message || "Der Vorgang ist fehlgeschlagen.",true);
async function navigate(view) {await AudioUI.beforeNavigate();S.view=view;S.sideOpen=false;await refresh();if(view==="audio")await AudioUI.onOpen();if(view==="history")S.history=await api("/api/history?project_id="+encodeURIComponent(S.project)+"&q="+encodeURIComponent(S.historyQuery));render();}
async function newChat() {
 await AudioUI.beforeNavigate();
 if(S.busy) throw new Error("Bitte zuerst die laufende Antwort stoppen.");
 invalidateBudget();WebUI.reset();
 S.thread=null;S.messages=[];S.settings=defaultSettings();S.draft="";S.sourceHits=[];S.sourceNotes=[];S.skills.clear();S.selected.clear();S.attachments.clear();S.view="chat";render();
}
async function switchProject(id) {
 if(S.busy) throw new Error("Bitte zuerst die laufende Antwort stoppen.");
 await AudioUI.beforeNavigate(true);
 AudioUI.reset();
 S.project=id;await newChat();await refresh();render();
}
async function openThread(id) {
 if(S.busy) throw new Error("Bitte zuerst die laufende Antwort stoppen.");
 const data=await api("/api/threads/"+id);
 const projectChange=data.thread.project_id!==S.project;
 await AudioUI.beforeNavigate(projectChange);
 if(projectChange)AudioUI.reset();
 invalidateBudget();WebUI.reset();
 S.thread=id;S.project=data.thread.project_id;S.messages=data.messages;
 S.settings={...defaultSettings(),...data.thread.parameters,model:data.thread.model,system_prompt:data.thread.system_prompt};
 S.view="chat";S.draft="";S.selected.clear();S.attachments.clear();S.skills.clear();S.sourceHits=[];S.sourceNotes=[];
 const last=[...data.messages].reverse().find(m=>m.metadata?.sources?.length);
 if(last) S.sourceHits=last.metadata.sources;
 S.sideOpen=false;await refresh();render();
}
async function saveThread() {
 const title=S.data.threads.find(t=>t.id===S.thread)?.title || "Neuer Chat";
 const body={project_id:S.project,title,...S.settings};
 if(!S.thread) {const r=await api("/api/threads","POST",body);S.thread=r.id;}
 else await api("/api/threads/"+S.thread,"PUT",body);
}
async function sendMessage() {
 if(S.busy||!S.draft.trim()) return;
 const content=S.draft.trim(),webRequest=WebUI.request();
 if(!S.data.connection.base_url) {toast("Bitte zuerst den GPUStack-Endpunkt verbinden.",true);await navigate("settings");return;}
 await saveThread();
 invalidateBudget();
 S.busy=true;S.stage=webRequest.web_search?"recherchiert im Web …":"antwortet";S.abort=new AbortController();S.draft="";S.view="chat";
 const originalLength=S.messages.length;
 S.messages.push({role:"user",content,metadata:{}},{role:"assistant",content:"",metadata:{model:S.settings.model,status:"streaming"}});
 render();
 let received=false;
 try {
  const r=await fetch("/api/threads/"+S.thread+"/send",{method:"POST",headers:{"Content-Type":"application/json","X-CSRF-Token":S.data.csrf},
   body:JSON.stringify({content,document_ids:[...S.selected],preview_ids:[...S.attachments],skill_ids:[...S.skills],semantic:S.semantic,...webRequest}),signal:S.abort.signal});
  if(!r.ok) {const data=await r.json();throw new Error(typeof data.detail==="string"?data.detail:"Bitte Eingaben prüfen.");}
  received=true;WebUI.sent();S.stage="antwortet";renderMessages();
  const reader=r.body.getReader(),decoder=new TextDecoder();let buffer="";
  while(true) {
   const {done,value}=await reader.read();if(done) break;buffer+=decoder.decode(value,{stream:true});
   let split;
   while((split=buffer.indexOf("\n\n"))!==-1) {
    const chunk=buffer.slice(0,split);buffer=buffer.slice(split+2);
    const line=chunk.split("\n").find(l=>l.startsWith("data:"));if(!line) continue;
    const evt=JSON.parse(line.slice(5));
    if(evt.type==="context"){S.sourceHits=evt.sources;S.sourceNotes=evt.notes;S.messages[originalLength].metadata=evt;renderInspector();renderMessages();}
    if(evt.type==="token"){S.messages[S.messages.length-1].content+=evt.text;updateStreamingMessage();}
    if(evt.type==="reasoning"){const meta=S.messages[S.messages.length-1].metadata;meta.reasoning=(meta.reasoning||"")+evt.text;updateStreamingMessage();}
    if(evt.type==="error") {toast(evt.message,true);S.draft=content;}
   }
  }
 } catch(e) {
  if(e.name!=="AbortError") {fail(e);S.draft=content;}
  if(!received){S.messages.splice(originalLength);S.draft=content;}
 } finally {
  S.abort=null;
  try {const r=await api("/api/threads/"+S.thread);S.messages=r.messages;await refresh();}catch{}
  S.busy=false;render();
 }
}
async function uploadFiles(files) {
 if(!files?.length) return;
 const wasChat=S.view==="chat",projectId=S.libraryGlobal&&!wasChat?"":S.project,mode=wasChat?"text":S.importMode;
 let count=0;const archived=[],errors=[];
 for(const file of files) {
  try {
   if(file.size>limitValue("file_mb")*1024*1024) throw new Error(file.name+": eingestellt sind "+limitValue("file_mb")+" MiB. Unter Einstellungen → Ressourcengrenzen erhöhen.");
   toast(file.name+(mode==="original"?" wird lokal abgelegt …":" wird lokal eingelesen …"));
   const form=new FormData();form.append("file",file);form.append("project_id",projectId);form.append("mode",mode);
   const doc=await api("/api/documents","POST",form);
   if(wasChat&&["bereit","bild"].includes(doc.status)) S.selected.add(doc.id);
   if(wasChat&&(doc.status==="bild"||doc.mime==="application/pdf")) S.attachments.add(doc.id);
   if(doc.status==="ablage") archived.push(doc);
   count++;
  } catch(e) {errors.push(e.message);}
 }
 await refresh();render();
 if(archived.length||errors.length) modal("Ergebnis des Dateiimports",
  `<p>${count} Datei(en) lokal gespeichert. Keine Modellanfrage ausgelöst.</p>${archived.map(d=>`<div class="info warning"><span><b>${esc(d.name)} · Original gespeichert</b><br>${esc(d.note)}</span></div>`).join("")}${errors.map(e=>`<p class="message-error">${esc(e)}</p>`).join("")}<p>Originale findest du in der Library dieses Projekts. Dort „Text erneut einlesen“ wählen, nachdem die Grenzen angepasst sind. Für Gesamtzahlen oder Berechnungen die vollständige CSV/XLSX als Eingabe im Datenlabor wählen. Projektübergreifende Ablage hat dieselben Grenzen.</p>`);
 else if(count) toast(count+" Datei(en) lokal gespeichert. Keine Modellanfrage ausgelöst.");
}
async function saveConnection(test) {
 const form=$("#connection-form");
 const buttons=$$("button",form);buttons.forEach(b=>b.disabled=true);
 try {
  const result=await api("/api/connection","POST",{base_url:$("#base-url").value.trim(),api_key:$("#api-key").value,
   persist_key:$("#key-storage").value==="vault",embedding_model:$("#embedding-model").value,rerank_model:$("#rerank-model").value,internet_enabled:$("#internet-enabled").checked,research_contact:$("#research-contact").value.trim()});
  $("#api-key").value="";
  S.connected=false;
  if(test){const response=await api("/api/connection/test","POST",{});S.connected=true;toast(response.count+" Modelle vom Endpunkt geladen.");}
  else toast("Verbindungseinstellungen gespeichert. Schlüssel: "+result.key_status);
  await refresh();render();
 } finally {buttons.forEach(b=>b.disabled=false);}
}
function modal(title,body,submitLabel="",onSubmit=null) {
 const d=$("#modal");
 d.className="";
 d.innerHTML=`<form id="modal-form"><div class="modal-head"><h2>${title}</h2><button type="button" class="icon-btn" data-close aria-label="Schließen">${icon("x")}</button></div><div class="modal-body">${body}</div><div class="modal-error" role="alert"></div><div class="modal-footer"><button type="button" class="button" data-close>${submitLabel?"Abbrechen":"Schließen"}</button>${submitLabel?`<button class="button primary" type="submit">${submitLabel}</button>`:""}</div></form>`;
 $$("[data-close]",d).forEach(b=>b.onclick=()=>d.close());
 $("#modal-form",d).onsubmit=async e=>{
  e.preventDefault();if(!onSubmit){d.close();return;}
  const b=$('button[type="submit"]',d);b.disabled=true;
  try{await onSubmit(new FormData(e.target));d.close();}catch(err){$(".modal-error",d).textContent=err.message;$(".modal-error",d).classList.add("visible");}finally{b.disabled=false;}
 };
 if(!d.open)d.showModal();
}
function field(label,name,value="",type="text",extra="") {return `<div class="field"><label for="f-${name}">${label}</label>${type==="textarea"?`<textarea id="f-${name}" name="${name}" ${extra}>${esc(value)}</textarea>`:`<input id="f-${name}" name="${name}" type="${type}" value="${esc(value)}" ${extra}>`}</div>`;}
function confirmAction(title,description,label,fn) {modal(title,`<p class="muted">${esc(description)}</p>`,label,fn);}
function editProject(id) {
 if(S.busy && !id) throw new Error("Bitte vor einem neuen Projekt die laufende Antwort beenden.");
 const p=S.data.projects.find(p=>p.id===id) || {};
 modal(id?"Projekt bearbeiten":"Neues Projekt",field("Projektname","name",p.name||"","text",'required maxlength="100"')+
  field("Beschreibung","description",p.description||"","textarea",'rows="2" maxlength="1000"')+
  field("Projekt-Systemprompt","system_prompt",p.system_prompt||"Antworte auf Deutsch. Kennzeichne Unsicherheiten und belege Aussagen.","textarea",`rows="4" maxlength="${limitValue("prompt_chars")}"`)+
  field("Feste Projektnotizen / Gedächtnis","memory",p.memory||"","textarea",`rows="4" maxlength="${limitValue("prompt_chars")}"`)+
  '<p class="footnote">Diese Notizen werden bei jeder Anfrage in diesem Projekt übergeben. Es wird kein verborgenes Gedächtnis automatisch aufgebaut.</p>',"Speichern",async fd=>{
   const body=Object.fromEntries(fd);
   const r=await api(id?"/api/projects/"+id:"/api/projects",id?"PUT":"POST",body);
   if(!id){AudioUI.reset();S.project=r.id;S.thread=null;S.messages=[];S.selected.clear();S.attachments.clear();}
   await refresh();render();toast("Projekt gespeichert.");
  });
}
function editPrompt(id) {
 const p=S.data.prompts.find(p=>p.id===id)||{};
 modal(id?"Vorlage bearbeiten":"Neue Vorlage",field("Name","name",p.name||"","text",'required maxlength="100"')+
  `<div class="field"><label for="f-kind">Typ</label><select id="f-kind" name="kind">${options([["system","Systemprompt"],["skill","Skill / Arbeitsanweisung"]],p.kind||"system")}</select></div>`+
  field("Anweisung","content",p.content||"","textarea",`required rows="10" maxlength="${limitValue("prompt_chars")}"`),"Speichern",async fd=>{
   await api(id?"/api/prompts/"+id:"/api/prompts",id?"PUT":"POST",Object.fromEntries(fd));await refresh();render();toast("Vorlage gespeichert.");
  });
}
function editModel(id) {
 const m=S.data.models.find(m=>m.id===id)||{};
 modal(id?"Modellprofil bearbeiten":"Modellprofil ergänzen",field("Exakte Deployment-ID","id",m.id||"","text",`required maxlength="160" ${id?"readonly":""}`)+
  `<div class="field"><label for="f-type">Aufgabe</label><select id="f-type" name="type">${options([["chat","Chat"],["embedding","Embedding"],["reranker","Reranker"],["audio","Transkription"],["unclassified","Noch nicht zugeordnet"]],m.type||"chat")}</select></div>`+
  field("Kurzer Hinweis","description",m.description||"","text",'maxlength="200"')+
  modelInfo(m.id)+field("Deployment-Kontexttokens · leer = unbekannt","deployment_context_tokens",m.deployment_context_tokens||"","number",'min="128" max="16777216" step="1"')+
  field("Deployment-Ausgabelimit · leer = unbekannt","deployment_output_tokens",m.deployment_output_tokens||"","number",'min="1" max="1048576" step="1"')+
  `<label class="check-label"><input type="checkbox" name="stream_usage" ${m.stream_usage?"checked":""}>Tokenverbrauch im Stream anfordern (stream_options.include_usage)</label><p class="footnote">Nur aktivieren, wenn der Backend-Server diesen Parameter unterstützt. Ohne ihn werden trotzdem vom Server gelieferte Usage-Werte angezeigt.</p>`+
  `<label class="check-label"><input type="checkbox" name="vision" ${m.vision?"checked":""}>Bildinput für dieses Chatmodell freigeben</label><p class="footnote">Nur Fähigkeiten aktivieren, die im konkreten GPUStack-Deployment getestet sind. Der Modellname allein reicht nicht als Nachweis.</p>`,"Speichern",async fd=>{
   await api("/api/models","POST",{...Object.fromEntries(fd),vision:fd.has("vision"),stream_usage:fd.has("stream_usage"),deployment_context_tokens:fd.get("deployment_context_tokens")?+fd.get("deployment_context_tokens"):null,deployment_output_tokens:fd.get("deployment_output_tokens")?+fd.get("deployment_output_tokens"):null});await refresh();render();toast("Modellprofil gespeichert.");
  });
}
async function previewDoc(id,offset=0) {
 const data=await api("/api/documents/"+id+"/text?offset="+offset),d=data.document;
 if(d.status==="bild"||d.mime==="application/pdf"||d.status==="audio"){
  const url="/api/documents/"+id+"/download?inline=true";
  modal(esc(d.name),`<div class="media-viewer">${d.status==="bild"?`<img class="preview-image" src="${url}" alt="${esc(d.name)}">`:d.mime==="application/pdf"?`<iframe class="pdf-viewer" src="${url}#view=FitH" title="${esc(d.name)}"></iframe>`:`<audio controls preload="metadata" src="${url}"></audio>`}</div><div class="card-footer"><a class="button" href="${url}" target="_blank" rel="noopener">Separat öffnen</a><a class="button" href="/api/documents/${id}/download">Original herunterladen</a></div><p class="footnote">PDF-Anzeige nutzt den PDF-Viewer deines Browsers. Falls er nicht eingebettet angezeigt wird: separat öffnen oder herunterladen. Die Anzeige ersetzt keine OCR oder vollständige Modellübergabe.</p>`);
  $("#modal").classList.add("media-modal");return;
 }
 modal(esc(d.name),`<p class="small muted">${esc(d.note)} · ${prettySize(d.size)}</p><div class="panel-rule"></div>${d.status==="bild"?`<img class="preview-image" src="/api/documents/${id}/download?inline=true" alt="${esc(d.name)}">`:data.chunks.length?data.chunks.map(c=>`<details class="source-proof" open><summary>${esc(c.location)}</summary><p>${esc(c.content)}</p></details>`).join(""):`<p class="muted">${d.status==="audio"?"Audio kann in der Library explizit transkribiert werden.":d.status==="ablage"?"Vollständiges Original gespeichert. Kein Textindex. Nach Anpassung der Grenzen erneut einlesen oder das Original im Datenlabor verwenden.":"Kein lesbarer Text vorhanden. Scans als Bilder übergeben oder zuerst lokal OCR ausführen."}</p>`}
 <p class="footnote">Vorschau: ${data.chunks.length?offset+1:0}–${offset+data.chunks.length} von ${data.total} Textabschnitten. Original vollständig als Download verfügbar.</p>
 <div class="card-footer">${offset?'<button type="button" class="button compact" id="preview-prev">Vorherige Abschnitte</button>':""}${data.next_offset!==null?'<button type="button" class="button compact" id="preview-next">Weitere Abschnitte</button>':""}<a class="button compact" href="/api/documents/${id}/download">Original herunterladen</a></div>`);
 $("#preview-prev")?.addEventListener("click",()=>previewDoc(id,Math.max(0,offset-100)).catch(fail));
 $("#preview-next")?.addEventListener("click",()=>previewDoc(id,data.next_offset).catch(fail));
}
async function doResearch() {
 if(S.researchBusy) return;
 const query=S.researchQuery,source=S.researchSource,language=S.researchLanguage,freshness=S.researchFreshness;
 S.researchBusy=true;S.researchResults=[];S.researchMeta=null;render();
 try {const r=await api("/api/research","POST",{query,source,language,freshness});S.researchResults=r.results;S.researchMeta=r;
  S.researchResultSource=r.source;S.researchResultQuery=r.sent_query;S.researchRetrievedAt=r.retrieved_at;
  if(!r.results.length)toast("Keine Treffer gefunden.");}
 finally {S.researchBusy=false;render();}
}
function newRoutine() {
 const future=new Date(Date.now()+86400000);const local=new Date(future.getTime()-future.getTimezoneOffset()*60000).toISOString().slice(0,16);
 modal("Neue Routine",field("Name","name","","text",'required maxlength="100"')+
  field("Wiederkehrender Prompt","prompt","","textarea",`required rows="5" maxlength="${limitValue("message_chars")}"`)+
  `<div class="field"><label for="f-model">Chatmodell</label><select id="f-model" name="model">${modelOptions(S.settings.model)}</select></div><div class="field-row">${field("Intervall in Tagen","interval_days","7","number",'required min="1" max="365"')}${field("Erster Termin (lokale Zeit)","next_run",local,"datetime-local","required")}</div>
  <div class="field-row">${field("Eingabebudget in Zeichen","context_chars",S.settings.context_chars,"number",`required min="0" max="${limitValue("context_max_chars")}"`)}${field("Maximale Ausgabetokens","max_tokens",S.settings.max_tokens,"number",`required min="1" max="${limitValue("output_max_tokens")}"`)}</div>
  <label class="check-label"><input type="checkbox" name="enabled">Aktivieren und wiederkehrende Modellanfragen freigeben</label><p class="footnote">Fester Abstand in Tagen (24 Stunden), keine Kalenderregel. Sommerzeit kann die lokale Uhrzeit verschieben. Quellen und Internetrecherche werden nicht automatisch einbezogen.</p>`,"Routine speichern",async fd=>{
   await api("/api/routines","POST",{...Object.fromEntries(fd),project_id:S.project,context_chars:+fd.get("context_chars"),max_tokens:+fd.get("max_tokens"),interval_days:+fd.get("interval_days"),next_run:new Date(fd.get("next_run")).toISOString(),enabled:fd.has("enabled")});await refresh();render();toast("Routine gespeichert.");
  });
}
function download(name,text,mime="text/plain") {
 const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([text],{type:mime}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),5000);
}
async function connector() {
 if(!S.data.connector_enabled) {modal("Lokalen Ordner anbinden",'<p>Gib beim Start einen einzelnen Ordner über <code>WORKROOM_IMPORT_ROOT</code> frei. Danach kannst du Dateien hier einzeln importieren.</p><p class="footnote">Der Konnektor liest ausschließlich aus diesem Ordner. Er verändert keine Originale und steuert keine lokalen Anwendungen. Einrichtung und Windows-Beispiel stehen in der README.</p>');return;}
 let offset=0,query="";
 async function page() {
  const r=await api("/api/connector?offset="+offset+"&q="+encodeURIComponent(query));
  modal("Dateien aus freigegebenem Ordner",`<p class="path">${esc(r.root)}</p><div class="field"><label for="connector-query">Dateiname / Pfad suchen</label><input type="text" id="connector-query" maxlength="200" value="${esc(query)}"><button type="button" class="button compact" id="connector-search">Suchen</button></div><div class="field"><label for="f-path">Datei wählen · Seite ${Math.floor(offset/200)+1}</label><select name="path" id="f-path" required>${options(r.files.map(f=>[f.path,f.path+" · "+prettySize(f.size)]),"")}</select></div><div class="card-footer">${offset?'<button type="button" class="button compact" id="connector-prev">Zurück</button>':""}${r.next_offset!==null?'<button type="button" class="button compact" id="connector-next">Weitere Dateien</button>':""}</div>`,"In Projekt importieren",async fd=>{
   if(!fd.get("path"))throw new Error("Bitte eine Datei wählen.");
   const doc=await api("/api/connector/import","POST",{path:fd.get("path"),project_id:S.project});await refresh();render();toast(doc.status==="ablage"?doc.note:"Datei in das Projekt kopiert.");
  });
  $("#connector-search").onclick=()=>{query=$("#connector-query").value;offset=0;page().catch(fail);};
  $("#connector-prev")?.addEventListener("click",()=>{offset=Math.max(0,offset-200);page().catch(fail);});
  $("#connector-next")?.addEventListener("click",()=>{offset=r.next_offset;page().catch(fail);});
 }
 await page();
}
function opencode() {
 const cfg={"$schema":"https://opencode.ai/config.json",share:"disabled",autoupdate:false,enabled_providers:["gpustack"],
  provider:{gpustack:{npm:"@ai-sdk/openai-compatible",name:"GPUStack",options:{baseURL:S.data.connection.base_url || "https://GPUSTACK-HOST/v1",apiKey:"{env:GPUSTACK_API_KEY}"},
  models:Object.fromEntries(chatModels().map(m=>[m.id,{name:m.id}]))}},
  model:"gpustack/"+S.settings.model,small_model:"gpustack/"+S.settings.model,permission:{"*":"ask",external_directory:"deny",webfetch:"deny",websearch:"deny"}};
 modal("OpenCode vorbereiten",`<p>OpenCode kann denselben GPUStack-Endpunkt über einen eigenen API-Schlüssel ansprechen. Die Konfigurationsdatei enthält nur eine Umgebungsreferenz, keinen Schlüssel.</p><div class="panel-rule"></div><p>Im PoC ist dies eine Konfigurationsübergabe. OpenCode ist nicht eingebettet und wird nicht aus dem Chat gestartet. Seine Aktionsfreigaben ersetzen keine isolierte Ausführungsumgebung.</p><p class="footnote">Konfiguration für OpenCode 1.x. Vor Installation die verwendete Version, ausgehende Verbindungen und Berechtigungen prüfen. Auf einem verwalteten Rechner mit der IT abstimmen.</p>`,"Konfiguration herunterladen",async()=>{download("opencode.json",JSON.stringify(cfg,null,2),"application/json");});
}
document.addEventListener("change",e=>{
 const t=e.target;
 if(t.dataset.source) {invalidateBudget();t.checked?S.selected.add(t.dataset.source):S.selected.delete(t.dataset.source);if(S.view==="chat")renderChips();else render();}
 if(t.dataset.skill){invalidateBudget();t.checked?S.skills.add(t.dataset.skill):S.skills.delete(t.dataset.skill);renderChips();}
 if(t.dataset.labDoc){t.checked?S.labDocs.add(t.dataset.labDoc):S.labDocs.delete(t.dataset.labDoc);}
});
document.addEventListener("click",async e=>{
 const b=e.target.closest("button");if(!b||b.disabled) return;
 if(b.closest("#modal"))return;
 try {
  if(b.dataset.view){await navigate(b.dataset.view);return;}
  if(b.dataset.project){await switchProject(b.dataset.project);return;}
  if(b.dataset.thread){await openThread(b.dataset.thread);return;}
  if(b.dataset.tab){S.tab=b.dataset.tab;$$("[data-tab]").forEach(t=>{t.classList.toggle("active",t===b);t.setAttribute("aria-selected",t===b);});renderInspector();return;}
  if(b.dataset.removeSource){invalidateBudget();S.selected.delete(b.dataset.removeSource);S.attachments.delete(b.dataset.removeSource);renderChips();renderInspector();return;}
  if(b.dataset.removeSkill){invalidateBudget();S.skills.delete(b.dataset.removeSkill);renderChips();renderInspector();return;}
  if(b.dataset.promptFilter){S.promptFilter=b.dataset.promptFilter;render();return;}
  if(b.dataset.proof){const [i,k]=b.dataset.proof.split(":").map(Number);const s=S.messages[i].metadata.sources[k];modal("Quelle "+esc(s.label),`${s.url?`<p><a href="${safeURL(s.url)}" target="_blank" rel="noopener noreferrer">Originalquelle öffnen</a></p><p class="footnote">${s.kind==="page"?"Extrahierter Webtext":"Suchauszug · kein gelesener Volltext"}${s.truncated?" · Text gekürzt":""}</p>`:""}<h3>${esc(s.name)}</h3><p class="small muted">${esc(s.location)}</p><div class="panel-rule"></div><p class="prewrap">${esc(s.content)}</p>`);return;}
  const id=b.dataset.id;
  if(b.dataset.action?.startsWith("web-")){await WebUI.action(b);return;}
  if(b.dataset.action?.startsWith("audio-")){await AudioUI.action(b);return;}
  switch(b.dataset.action) {
   case "menu":S.sideOpen=!S.sideOpen;$(".sidebar").classList.toggle("open",S.sideOpen);break;
   case "settings":await navigate("settings");break;
   case "new-chat":await newChat();break;
   case "upload":$("#file-input").click();break;
   case "stop":S.abort?.abort();break;
   case "toggle-panel":setPanel(!S.panelOpen);break;
   case "close-panel":setPanel(false);break;
   case "prompt-panel":S.tab="instructions";S.panelOpen=true;render();break;
   case "quick-document":invalidateBudget();S.tab="sources";S.panelOpen=true;S.draft="Fasse die ausgewählten Quellen zusammen und belege die zentralen Aussagen.";render();$("#file-input").click();break;
   case "quick-metadata":{invalidateBudget();const p=S.data.prompts.find(p=>p.name==="Metadaten extrahieren");if(p)S.skills.add(p.id);S.draft="Extrahiere Personen, Orte und Datumsangaben aus den ausgewählten Quellen.";S.tab="sources";S.panelOpen=true;render();break;}
   case "use-sources":S.view="chat";S.tab="sources";render();break;
   case "new-project":await AudioUI.beforeNavigate(true);editProject();break;
   case "edit-project":editProject(id||S.project);break;
   case "delete-project":confirmAction("Projekt löschen?","Alle Chats, Originale, Indizes, Routinen und Datenlabor-Aufträge dieses Projekts werden entfernt. Dies kann nicht rückgängig gemacht werden.","Projekt löschen",async()=>{await api("/api/projects/"+id,"DELETE");if(S.project===id){S.thread=null;S.messages=[];S.selected.clear();S.attachments.clear();}await refresh();render();});break;
   case "new-prompt":editPrompt();break;
   case "edit-prompt":editPrompt(id);break;
   case "delete-prompt":confirmAction("Vorlage löschen?","Gespeicherte Chat-Snapshots bleiben erhalten.","Löschen",async()=>{await api("/api/prompts/"+id,"DELETE");S.skills.delete(id);await refresh();render();});break;
   case "apply-prompt":{invalidateBudget();const p=S.data.prompts.find(x=>x.id===id);if(p.kind==="system")S.settings.system_prompt=p.content;else S.skills.add(id);S.view="chat";S.tab="instructions";S.panelOpen=true;render();toast("Vorlage für den nächsten Prompt übernommen.");break;}
   case "new-model":editModel();break;
   case "edit-model":editModel(id);break;
   case "preview-doc":await previewDoc(id);break;
   case "delete-doc":confirmAction("Datei löschen?","Original und Suchindex werden entfernt. Bereits verwendete Quellenauszüge bleiben im Chatverlauf und in früheren Exporten. Für vollständige Entfernung auch betroffene Chats löschen.","Datei löschen",async()=>{await api("/api/documents/"+id,"DELETE");S.selected.delete(id);await refresh();render();});break;
   case "reset-limits":for(const f of S.data.limit_fields)$("#f-"+f.key).value=f.default;toast("Vorgaben eingetragen; zum Übernehmen speichern.");break;
   case "reprocess-doc":{
    const run=async()=>{b.disabled=true;try{await api("/api/documents/"+id+"/reprocess","POST",{});await refresh();render();toast("Text vollständig neu eingelesen. Semantischen Index bei Bedarf neu erstellen.");}finally{b.disabled=false;}};
    if(S.docs.find(d=>d.id===id)?.indexed)confirmAction("Text erneut einlesen?","Der bisherige Text- und semantische Index wird nach erfolgreichem Einlesen ersetzt. Original und gespeicherte Chatbelege bleiben erhalten. Danach bei Bedarf erneut semantisch indexieren.","Erneut einlesen",run);
    else await run();break;
   }
   case "index-doc":confirmAction("Semantischen Index erstellen?","Die Textabschnitte dieser Datei werden an "+S.data.connection.embedding_model+" auf deinem GPUStack-Endpunkt übergeben. Der Index wird lokal gespeichert. Grosse Dokumente können viele Anfragen benötigen. Erfolgreiche Teilpakete bleiben erhalten; erneutes Indexieren setzt nach einer Unterbrechung fort.","Indexieren",async()=>{await api("/api/documents/"+id+"/index","POST",{});await refresh();render();toast("Semantischer Index erstellt.");});break;
   case "transcribe-doc":await navigate("audio");AudioUI.chooseAudio(id);render();break;
   case "test-connection":await saveConnection(true);break;
   case "forget-key":confirmAction("Schlüssel entfernen?","Der Sitzungsschlüssel und ein gespeicherter Schlüssel für diesen Endpunkt werden entfernt. Ein Schlüssel aus einer Umgebungsvariable muss außerhalb der App entfernt werden.","Entfernen",async()=>{await api("/api/connection","POST",{...S.data.connection,forget_key:true});await refresh();render();});break;
   case "save-thread":await saveThread();await refresh();toast("Chateinstellungen gespeichert.");break;
   case "rename-thread":modal("Chat bearbeiten",field("Titel","title",S.data.threads.find(t=>t.id===S.thread)?.title||"","text",'required maxlength="140"')+btn("Diesen Chat löschen","noop","trash","danger",'id="delete-thread-modal" type="button"'),"Speichern",async fd=>{await api("/api/threads/"+S.thread,"PUT",{project_id:S.project,title:fd.get("title"),...S.settings});await refresh();render();});$("#delete-thread-modal").onclick=()=>confirmAction("Chat dauerhaft löschen?","Der gesamte Verlauf einschließlich gespeicherter Quellenauszüge wird entfernt.","Chat löschen",async()=>{await api("/api/threads/"+S.thread,"DELETE");$("#modal").close();await newChat();await refresh();render();});break;
   case "export-chat":showChatExport();break;
   case "check-budget":await checkBudget();break;
   case "copy-message":if(!navigator.clipboard)throw new Error("Kopieren ist in diesem Browser nicht verfügbar. Bitte den Download verwenden.");await navigator.clipboard.writeText(S.messages[+b.dataset.index].content);toast("Antwort kopiert.");break;
   case "download-message":showAnswerExport(+b.dataset.index);break;
   case "save-research":{if(S.researchResultSource==="web"){await WebUI.saveResearch(+b.dataset.index);break;}const r=S.researchResults[+b.dataset.index];const text="# "+r.title+"\n\nQuelle: "+r.url+"\nAbruf: "+S.researchRetrievedAt+"\nDatenquelle: "+S.researchResultSource+"\nSuchtext: "+S.researchResultQuery+"\n\n"+r.text+(r.truncated?"\n\nHinweis: Metadatenauszug gekürzt. Vollständigen Eintrag beim Anbieter prüfen.":"")+"\n\nHinweis: Metadaten, Normdaten oder Abstract; kein vollständiger Artikel und keine verifizierte Tatsachenprüfung.";const fd=new FormData();fd.append("file",new File([text],"recherche-"+(Number(b.dataset.index)+1)+".md",{type:"text/markdown"}));fd.append("project_id",S.project);await api("/api/documents","POST",fd);await refresh();toast("Recherchetreffer als Projektquelle gespeichert.");break;}
   case "new-routine":newRoutine();break;
   case "toggle-routine":await api("/api/routines/"+id+"/toggle","POST",{});await refresh();render();break;
   case "delete-routine":confirmAction("Routine löschen?","Die Routine wird entfernt. Bereits erzeugte Ergebnis-Chats bleiben erhalten.","Löschen",async()=>{await api("/api/routines/"+id,"DELETE");await refresh();render();});break;
   case "run-routine":b.disabled=true;b.textContent="Läuft …";try{const r=await api("/api/routines/"+id+"/run","POST",{});if(!r.thread_id)throw new Error(r.status);await openThread(r.thread_id);}finally{b.disabled=false;}break;
   case "download-code":download("analyse.py",S.labCode,"text/x-python");break;
   case "run-code":if(!$("#lab-approve").checked)throw new Error("Bitte Code und Eingabedateien ausdrücklich freigeben.");b.disabled=true;b.textContent="Wird ausgeführt …";try{S.labResult=await api("/api/jobs","POST",{project_id:S.project,code:S.labCode,document_ids:[...S.labDocs],approved:true});render();}finally{b.disabled=false;}break;
   case "connector":await connector();break;
   case "opencode":opencode();break;
  }
 }catch(err){fail(err);}
});
window.addEventListener("beforeunload",e=>{if(S.busy||AudioUI.hasUnsaved()){e.preventDefault();e.returnValue="";}});
function setPanel(open){
 S.panelOpen=open;$(".inspector")?.classList.toggle("open",open);$(".chat-layout")?.classList.toggle("panel-open",open);
 $('[data-action="toggle-panel"]')?.setAttribute("aria-expanded",String(open));
}
function mediaCards(docs,removable=false){
 const media=docs.filter(d=>d.status==="bild"||d.mime==="application/pdf");
 return media.length?`<div class="media-cards">${media.map(d=>{
  const exists=S.docs.some(x=>x.id===d.id),url="/api/documents/"+d.id+"/download?inline=true";
  return `<div class="media-card-wrap"><button type="button" class="media-card" data-action="preview-doc" data-id="${esc(d.id)}" ${exists?"":"disabled"} title="${esc(d.name)} gross anzeigen">${exists?(d.status==="bild"?`<img src="${url}" alt="${esc(d.name)}" loading="lazy">`:`<span class="pdf-thumb"><iframe src="${url}#page=1&view=Fit&toolbar=0" title="Erste Seite von ${esc(d.name)}" tabindex="-1" loading="lazy"></iframe><span>PDF · Vorschau öffnen</span></span>`):icon("file")}<span>${esc(d.name)}${exists?"":" · Original gelöscht"}</span></button>${removable?`<button type="button" class="media-remove" data-remove-source="${esc(d.id)}" aria-label="${esc(d.name)} aus der Auswahl entfernen">${icon("x")}</button>`:""}${d.sent_as==="preview_only"||["ohne_text","ablage"].includes(d.status)?'<small class="media-note">Nur Vorschau · keine Textebene übergeben</small>':""}</div>`;
 }).join("")}</div>`:"";
}
function outputCeiling(id){
 const m=S.data.models.find(m=>m.id===id)||{};
 return Math.max(1,Math.min(limitValue("output_max_tokens"),m.deployment_output_tokens||Infinity,m.deployment_context_tokens?m.deployment_context_tokens-1:Infinity));
}
const numberLabel=n=>Number(n).toLocaleString("de-CH");
function modelInfo(id){
 const m=S.data.models.find(m=>m.id===id)||{},r=m.reference;
 return `<div class="model-capacity"><b>Kontext: ${esc(id||"Modell wählen")}</b><dl><dt>GPUStack-Deployment</dt><dd>${m.deployment_context_tokens?numberLabel(m.deployment_context_tokens)+" Tokens":"Nicht vom Server gemeldet / eingetragen"}</dd><dt>Deployment-Ausgabelimit</dt><dd>${m.deployment_output_tokens?numberLabel(m.deployment_output_tokens)+" Tokens":"Unbekannt; geteilt mit Input"}</dd><dt>Herstellerreferenz</dt><dd>${r?numberLabel(r.context_tokens)+` Tokens · <a href="${safeURL(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.model)}</a>`:"Keine geprüfte Referenz hinterlegt"}</dd></dl>${r?`<p class="footnote">${esc(r.note)} Stand ${esc(r.checked)}. Das Deployment kann kleiner oder anders konfiguriert sein.</p>`:""}${m.context_source?`<p class="footnote">Deployment-Angabe: ${esc(m.context_source)}</p>`:""}<p class="footnote">Input + Ausgabe teilen das Kontextfenster. Bilder, Chat-Template und je nach Backend Reasoning benötigen ebenfalls Tokens. Es gibt keine feste Umrechnung von Zeichen in Tokens.</p></div>`;
}
function usageLabel(u){
 const values=[];if(Number.isFinite(u.prompt_tokens))values.push("Input: "+numberLabel(u.prompt_tokens));if(Number.isFinite(u.completion_tokens))values.push("Ausgabe: "+numberLabel(u.completion_tokens));if(Number.isFinite(u.completion_tokens_details?.reasoning_tokens))values.push("davon Reasoning: "+numberLabel(u.completion_tokens_details.reasoning_tokens));
 return "GPUStack-Tokenverbrauch · "+esc(values.join(" · ")||"keine aufgeschlüsselten Werte");
}
async function checkBudget(){
 const revision=budgetRevision;
 await saveThread();if(revision!==budgetRevision)return;
 const thread=S.thread,r=await api("/api/threads/"+thread+"/budget","POST",{content:S.draft,document_ids:[...S.selected],preview_ids:[...S.attachments],skill_ids:[...S.skills]});
 if(revision!==budgetRevision||thread!==S.thread)return;
 const m=S.data.models.find(m=>m.id===S.settings.model),remaining=m?.deployment_context_tokens?m.deployment_context_tokens-S.settings.max_tokens:null;
 budgetResult=numberLabel(r.input_chars)+" Zeichen in der zusammengestellten Eingabe. Grobe Textschätzung (kann stark abweichen): "+numberLabel(r.token_estimate.low)+"–"+numberLabel(r.token_estimate.high)+" Tokens; kein Tokenizer, Bildtokens und Chat-Template fehlen. "+(remaining!==null?"Deployment-Kontext abzüglich Ausgabebudget: "+numberLabel(remaining)+" Tokens. ":"")+esc(r.note);
 renderInspector();
}
function showChatExport(){
 modal("Chat herunterladen",`<p>Gespräch und Quellenstellen als Markdown oder JSON. JSON enthält zusätzlich Parameter und verwendete Anweisungen.</p><label class="check-label"><input type="checkbox" id="export-reasoning">Vom Modell gelieferte Begründungen / CoT einschliessen</label><p class="footnote">Standard: aus. Nur tatsächlich gelieferter und gespeicherter Reasoning-Text kann exportiert werden.</p><div class="card-footer"><a id="export-md" class="button">Markdown herunterladen</a><a id="export-json" class="button">JSON herunterladen</a></div>`);
 const update=()=>{for(const f of ["md","json"])$("#export-"+f).href="/api/threads/"+S.thread+"/export?format="+f+"&include_reasoning="+$("#export-reasoning").checked;};
 $("#export-reasoning").onchange=update;update();
}
function showAnswerExport(index){
 const m=S.messages[index];modal("Antwort herunterladen",`<label class="check-label"><input type="checkbox" name="include_reasoning" ${m.metadata?.reasoning?"":"disabled"}>Vom Modell gelieferte Begründung / CoT einschliessen</label><p class="footnote">${m.metadata?.reasoning?"Der Reasoning-Text wird nur bei Auswahl ergänzt.":"Für diese Antwort wurde kein Reasoning-Text geliefert."}</p>`,"Markdown herunterladen",async fd=>{
  let text=m.content;if(fd.has("include_reasoning"))text+="\n\n## Vom Modell gelieferte Begründung / CoT\n\n"+m.metadata.reasoning;
  if(m.metadata?.sources?.length)text+="\n\n## Quellen dieser Antwort\n\n"+m.metadata.sources.map(s=>`[${s.label}] ${s.name} · ${s.location}\n\n${s.content}`).join("\n\n");
  if(m.metadata?.finish_reason==="length")text+="\n\nHinweis: Ausgabelimit erreicht; Antwort unvollständig.";
  download("antwort.md",text,"text/markdown");
 });
}
async function boot() {
 try {await refresh();render();}
 catch(e) {$("#app").innerHTML=`<div class="boot"><h1>Arbeitsraum nicht erreichbar</h1><p>Starte den lokalen Python-Dienst und öffne die angezeigte localhost-Adresse. Diese Oberfläche benötigt ihr lokales Backend.</p><p class="muted">${esc(e.message)}</p><button class="button" id="retry">Erneut versuchen</button></div>`;$("#retry").onclick=boot;}
}
await boot();
// Optional browser capability: stage a draft only; never send a model request.
if(document.modelContext?.registerTool) {
 const lifecycle=new AbortController();
 window.addEventListener("pagehide",()=>lifecycle.abort(),{once:true});
 try {
  Promise.resolve(document.modelContext.registerTool({
   name:"stage_chat_draft",title:"Chatentwurf vorbereiten",
   description:"Füllt den sichtbaren Chatentwurf im aktuellen Projekt. Sendet nichts an ein Modell und speichert keine Nachricht.",
   inputSchema:{type:"object",properties:{text:{type:"string",minLength:1,maxLength:4000000}},required:["text"],additionalProperties:false},
   annotations:{readOnlyHint:false,untrustedContentHint:true},
   async execute(input) {
    if(!input || typeof input.text!=="string" || !input.text.trim() || input.text.length>limitValue("message_chars") || Object.keys(input).some(k=>k!=="text"))throw new Error("Ein gültiger Text ist erforderlich.");
    if(S.busy)throw new Error("Bitte zuerst die laufende Antwort beenden.");
    S.draft=input.text;invalidateBudget();S.view="chat";render();
    return {staged:true,sent:false,project:project().name};
   }
  },{signal:lifecycle.signal})).catch(()=>{});
 }catch{}
}
