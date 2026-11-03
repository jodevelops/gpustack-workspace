// Audio is opt-in. Recording, local import and inference are separate operations.
export function createAudioWorkspace(h){
 const {state,api,refresh,render,esc,icon,btn,ibtn,field,options,modelOptions,modal,toast,prettyDate,prettySize,download,modelInfo,outputCeiling}=h;
 const $=s=>document.querySelector(s);
 const A={model:"",language:"",format:"text",audioId:"",list:[],current:null,dirty:false,editRevision:0,savePromise:null,page:0,busy:false,minutesModel:"",minutesTokens:8192,minutesChars:0,
  recorder:null,stream:null,writable:null,handle:null,chunks:[],recorded:null,recordURL:"",recordName:"",recordProject:"",recording:false,preparing:false,bytes:0,start:0,timer:null,writeChain:Promise.resolve(),recordError:"",fallback:false,imported:false};
 const audioModels=()=>state().data.models.filter(m=>m.type==="audio");
 const audioDocs=()=>state().docs.filter(d=>d.status==="audio");
 const active=()=>A.recording||A.preparing;
 const time=v=>{const s=Math.max(0,Number(v)||0);return `${String(Math.floor(s/3600)).padStart(2,"0")}:${String(Math.floor(s/60)%60).padStart(2,"0")}:${(s%60).toFixed(3).padStart(6,"0")}`;};
 async function loadList(){A.list=await api("/api/transcripts?project_id="+encodeURIComponent(state().project));}
 function chooseAudio(id){A.audioId=id;}
 function reset(){A.audioId="";A.current=null;A.list=[];A.dirty=false;A.editRevision++;A.imported=false;A.page=0;}
 function hasUnsaved(){return active()||A.dirty||!!A.savePromise||!!(A.recorded&&A.fallback);}
 async function beforeNavigate(projectChange=false){
  if(active())throw new Error("Aufnahme zuerst stoppen und speichern.");
  if(A.busy)throw new Error("Bitte die laufende Audio-/Protokollverarbeitung abwarten.");
  if(projectChange&&A.recorded)throw new Error("Gespeicherte Aufnahme zuerst ins aktuelle Projekt übernehmen oder die Aufnahmevorschau schliessen.");
  if(A.dirty||A.savePromise)await save(false);
 }
 function view(){
  if(!audioModels().some(m=>m.id===A.model))A.model=audioModels()[0]?.id||"";
  if(!state().data.models.some(m=>m.id===A.minutesModel&&m.type==="chat"))A.minutesModel=state().settings.model;
  return `<div class="page-heading"><div><h2>Audio aufnehmen. Transkripte bearbeiten.</h2><p>Zuerst lokal speichern, dann gezielt an dein Audio-Modell übergeben.</p></div></div>
  <div class="audio-layout"><div class="panel"><h3>1 · Aufnahme auf deinem Rechner</h3><p class="muted">Mikrofon startet erst nach deinem Klick. Es geht dabei nichts an GPUStack. In Edge / Chrome kannst du den Speicherort vor der Aufnahme wählen.</p>
   <div class="card-footer">${btn("Aufnehmen & Speicherort wählen","audio-record","audio","primary",active()?"disabled":"")}${btn("Stoppen & Datei fertig speichern","audio-stop","stop","",A.recording?"":"disabled")}</div>
   <p id="record-status" class="record-status" role="status">${recordStatus()}</p>
   ${A.recorded?`<audio controls preload="metadata" src="${esc(A.recordURL)}"></audio><p><b>${esc(A.recordName)}</b> · ${prettySize(A.recorded.size)}</p><div class="card-footer">${A.fallback?btn("Aufnahme herunterladen","audio-download-recording","download"):btn("Gespeicherte Aufnahme ins Projekt übernehmen","audio-import-recording","upload","primary",A.busy?"disabled":"")}${btn(A.fallback?"Ungespeicherte Aufnahme verwerfen":"Aufnahmevorschau schliessen","audio-clear-recording","x","subtle")}</div>${A.fallback?'<p class="footnote">Dieser Browser kann nicht direkt auf die Festplatte schreiben. Aufnahme herunterladen und danach über „Gespeicherte Datei wählen“ wieder auswählen. Der Download allein bestätigt keinen erfolgreichen Speichervorgang.</p>':""}`:""}
   <p class="footnote">Aufnahmegrenze richtet sich nach der Uploadgrenze (${state().data.limits.file_mb} MiB). WebM / MP4-Unterstützung hängt vom Audio-Backend ab. Mikrofon und Speicherzugriff müssen vom Browser und gegebenenfalls von der IT erlaubt sein.</p></div>
  <div class="panel"><h3>2 · Gespeicherte Datei transkribieren</h3><input type="file" id="audio-file" accept=".wav,.mp3,.m4a,.mp4,.ogg,.webm" class="hidden">
   ${btn("Gespeicherte Datei wählen","audio-pick-file","upload","",A.busy?"disabled":"")}
   <div class="field"><label for="audio-document">Aufnahme im Projekt</label><select id="audio-document" ${A.busy?"disabled":""}><option value="">Aufnahme wählen …</option>${options(audioDocs().map(d=>[d.id,d.name+" · "+prettySize(d.size)]),A.audioId)}</select></div>
   ${A.audioId?`<audio controls preload="metadata" src="/api/documents/${esc(A.audioId)}/download?inline=true"></audio>`:""}
   <div class="field"><label for="audio-model">Whisper / Transkriptmodell</label><select id="audio-model" ${A.busy?"disabled":""}>${options(audioModels().map(m=>[m.id,m.id]),A.model)}</select><small>Weitere tatsächlich bereitgestellte Audio-Modelle unter Einstellungen → Modellprofile zuordnen.</small></div>
   <div class="field-row"><div class="field"><label for="audio-language">Sprache</label><select id="audio-language">${options([["","Automatisch"],["de","Deutsch"],["en","Englisch"],["fr","Französisch"],["it","Italienisch"]],A.language)}</select></div><div class="field"><label for="audio-format">Ausgabe</label><select id="audio-format">${options([["text","Text (kompatibel)"],["verbose_json","Mit Zeitsegmenten (verbose_json)"]],A.format)}</select></div></div>
   <p class="footnote">Zeitsegmente nur, wenn das konkrete Backend verbose_json unterstützt. Whisper allein garantiert keine Sprecherdiarisierung. Ungeprüfte automatische Zeiten sind keine bestätigten Zeitstempel.</p>
   ${btn(A.busy?"Verarbeitung läuft …":"An GPUStack senden & transkribieren","audio-transcribe","play","primary",!A.audioId||!A.model||A.busy?"disabled":"")}
   <p class="footnote">Nur diese gespeicherte Aufnahme wird an ${esc(state().data.connection.base_url)} gesendet. Transkripte bleiben lokal im Projekt.</p></div></div>
  <div class="panel"><div class="panel-title"><h3>3 · Transkript & Meeting-Protokoll</h3>${btn("Liste aktualisieren","audio-refresh","clock","compact",A.busy?"disabled":"")}</div>
   <div id="transcript-list">${listView()}</div>
   ${A.current?editor():'<p class="muted">Eine Transkription öffnen oder oben eine gespeicherte Aufnahme transkribieren.</p>'}</div>`;
 }
 function recordStatus(){
  if(A.preparing)return "Speicherort / Mikrofon wird vorbereitet …";
  if(A.recording)return "● Aufnahme läuft · "+time((Date.now()-A.start)/1000)+" · "+prettySize(A.bytes);
  if(A.recordError)return A.recordError;
  if(A.recorded)return A.fallback?"Aufnahme im Browser. Jetzt auf die Festplatte herunterladen.":"Auf Festplatte gespeichert. Upload erfolgt erst über den separaten Button.";
  return "Bereit · keine aktive Aufnahme";
 }
 function listView(){return A.list.length?`<div class="transcript-list">${A.list.map(t=>btn(esc(t.title)+` <small>· ${esc(t.model)} · ${prettyDate(t.updated)}${t.has_minutes?" · mit Protokoll":""}</small>`,"audio-open-transcript","file",A.current?.id===t.id?"active":"",`data-id="${esc(t.id)}" ${A.busy?"disabled":""}`)).join("")}</div>`:'<p class="muted">Noch keine Transkripte in diesem Projekt.</p>';}
 function editor(){
  const row=A.current,w=row.working,segments=w.segments,original=row.original;
  const start=A.page*50;
  return `<div class="transcript-editor"><div class="panel-rule"></div><div class="panel-title"><h3>${esc(w.title)}</h3><span id="transcript-save-state" class="badge">${A.dirty?"Ungespeicherte Änderungen":"Lokal gespeichert · Version "+row.version}</span></div>
   <div class="card-footer">${btn("Änderungen lokal speichern","audio-save","check","primary",A.busy?"disabled":"")}${btn("Als Projektquelle speichern","audio-source","folder","",A.busy?"disabled":"")}${btn("MD herunterladen","audio-export-md","download","",A.busy?"disabled":"")}${btn("JSON mit Original","audio-export-json","download","",A.busy?"disabled":"")}${btn("Entwurf sichern","audio-download-draft","download","subtle")}${btn("Gespeicherte Fassung laden","audio-reload","clock","subtle")}</div>
   <p class="footnote">Der Download speichert Änderungen zuerst lokal und exportiert genau diese Version. Originaltranskript bleibt unverändert; eine Projektquelle ist ein separater Stand.</p>
   <div class="field-row">${workingField("Titel","title",w.title)}${workingField("Meetingdatum / Uhrzeit","meeting_date",w.meeting_date)}</div>
   <div class="field-row">${workingField("Teilnehmende · bekannte Angaben","participants",w.participants,"textarea")}${workingField("Traktanden / Agenda","agenda",w.agenda,"textarea")}</div>
   ${row.audio_document_id?`<audio id="transcript-audio" controls preload="metadata" src="/api/documents/${row.audio_document_id}/download?inline=true"></audio>`:'<p class="message-error">Originalaudio wurde gelöscht; Abhören ist nicht mehr möglich.</p>'}
   <p class="footnote">${esc(w.segment_source)}. Sprecherlabels können manuell zugeordnet werden; bestätige Zeit und Zuordnung erst nach dem Abhören.</p>
   ${segments.length?`<div class="segments">${segments.slice(start,start+50).map((s,i)=>segmentEditor(s,start+i,!!row.audio_document_id)).join("")}</div><div class="card-footer"><span>${start+1}–${Math.min(start+50,segments.length)} von ${segments.length} Segmenten</span>${btn("Zurück","audio-prev","chevron","compact",A.page?"":"disabled")}${btn("Weitere Segmente","audio-next","chevron","compact",start+50<segments.length?"":"disabled")}</div>${btn("Als freien Text weiterbearbeiten","audio-flatten","edit","subtle")}`:workingField("Transkript bearbeiten","text",w.text,"textarea",'rows="14" class="transcript-text"')}
   <div class="card-footer">${btn("Zeitsegmente / Diarisierung importieren","audio-import-segments","upload","",A.busy?"disabled":"")}${btn("Sprecher- und Zeitstempelverfahren","audio-diarization","info","subtle")}</div>
   <input type="file" id="segments-file" accept=".json" class="hidden">
   ${workingField("Prüfnotizen / Herkunft der Sprecherlabels","notes",w.notes,"textarea")}
   <details class="original-transcript"><summary>Unverändertes Originaltranskript anzeigen</summary><pre>${esc(original.text||"")}</pre><p class="footnote">Originaldaten einschliesslich gelieferter Segmente / Wörter im JSON-Export.</p></details>
   <div class="panel-rule"></div><h3>Meeting-Protokoll erstellen</h3><p class="muted">Ein lokales Chatmodell bündelt die vollständige gespeicherte Arbeitsfassung in Themen, Beschlüsse, Aufgaben, offene Fragen und nächste Schritte. Fehlende Angaben bleiben als „nicht genannt“ sichtbar.</p>
   <div class="field"><label for="minutes-model">Modell für Protokollentwurf</label><select id="minutes-model">${modelOptions(A.minutesModel)}</select></div>${modelInfo(A.minutesModel)}
   <div class="field-row"><div class="field"><label for="minutes-tokens">Maximale Ausgabetokens</label><input id="minutes-tokens" type="number" min="1" max="${outputCeiling(A.minutesModel)}" step="1" value="${A.minutesTokens}"></div><div class="field"><label for="minutes-chars">Zeichenbudget · 0 = deaktiviert</label><input id="minutes-chars" type="number" min="0" max="${state().data.limits.context_max_chars}" step="1" value="${A.minutesChars}"></div></div>
   ${btn(A.busy?"Protokoll wird verarbeitet …":"Gespeichertes Transkript an Modell senden","audio-minutes","play","primary",A.busy?"disabled":"")}
   ${w.minutes_stale?'<p class="message-error">Transkript / Metadaten wurden nach dem Protokollentwurf geändert. Protokoll abgleichen.</p>':""}${w.minutes_finish_reason==="length"?'<p class="message-error">Ausgabelimit erreicht. Protokollentwurf unvollständig; Budget erhöhen und neu erstellen.</p>':""}
   ${workingField("Protokollentwurf nachbearbeiten (Markdown)","minutes_md",w.minutes_md,"textarea",'rows="16" class="transcript-text"')}
   <p class="footnote">Der MD-Download bündelt Metadaten, Protokoll, Prüfnotizen und bearbeitetes Transkript samt vorhandenen Zeiten / Sprecherlabels.</p></div>`;
 }
 function workingField(label,key,value,type="text",extra=""){return field(label,key,value,type,extra).replace(`name="${key}"`,`name="${key}" data-transcript-field="${key}"`);}
 function segmentEditor(s,index,hasAudio){return `<div class="segment" data-segment="${index}"><div class="segment-head">${btn(time(s.start),"audio-seek","play","compact",`data-index="${index}" ${hasAudio?"":"disabled"}`)}<label>Start (s)<input type="number" step="0.001" min="0" value="${s.start}" data-segment-field="start" data-index="${index}"></label><label>Ende (s)<input type="number" step="0.001" min="0" value="${s.end}" data-segment-field="end" data-index="${index}"></label><label>Sprecherlabel<input maxlength="100" value="${esc(s.speaker)}" data-segment-field="speaker" data-index="${index}" placeholder="z.B. SPRECHER_01"></label></div><textarea rows="3" aria-label="Segment ${index+1} bearbeiten" data-segment-field="text" data-index="${index}">${esc(s.text)}</textarea><label class="check-label"><input type="checkbox" data-segment-field="verified" data-index="${index}" ${s.verified?"checked":""}>Zeit und Sprecherzuordnung durch Abhören geprüft</label></div>`;}
 function markDirty(){A.dirty=true;A.editRevision++;const badge=$("#transcript-save-state");if(badge)badge.textContent="Ungespeicherte Änderungen";}
 function downloadDraft(){
  if(!A.current)return;
  const row=A.current;
  download("transkript-entwurf-"+row.id.slice(0,8)+".json",JSON.stringify({format:"gpustack-transcript-draft-v1",id:row.id,project_id:row.project_id,version:row.version,working:row.working},null,2),"application/json");
 }
 function showReload(conflict=false){
  const row=A.current;if(!row)return;
  modal(conflict?"Transkript wurde zwischenzeitlich geändert":"Gespeicherte Fassung laden",`<p>Dein sichtbarer Entwurf für <b>${esc(row.working.title)}</b> (Version ${row.version}) bleibt bis zum Laden erhalten. Beim Laden werden seine ungespeicherten Änderungen durch die aktuelle gespeicherte Fassung ersetzt.</p><p>Bei Änderungen in einem anderen Fenster zuerst den Entwurf sichern und beide Fassungen abgleichen.</p><button type="button" class="button" id="download-transcript-draft">Entwurf als JSON sichern</button>`,"Gespeicherte Fassung laden",async()=>{
   const latest=await api("/api/transcripts/"+row.id);
   A.current=latest;A.dirty=false;A.imported=false;A.editRevision++;A.page=0;await loadList();render();
  });
  $("#download-transcript-draft").onclick=downloadDraft;
 }
 function bind(){
  if(A.busy||active())document.querySelectorAll(".page input,.page select,.page textarea,.page button").forEach(el=>{if(el.dataset.action!=="audio-stop"||!A.recording)el.disabled=true;});
  $("#audio-document")?.addEventListener("change",e=>{A.audioId=e.target.value;render();});
  $("#audio-model")?.addEventListener("change",e=>A.model=e.target.value);
  $("#audio-language")?.addEventListener("change",e=>A.language=e.target.value);
  $("#audio-format")?.addEventListener("change",e=>A.format=e.target.value);
  $("#audio-file")?.addEventListener("change",e=>importAudio(e.target.files[0]).catch(h.fail));
  $("#segments-file")?.addEventListener("change",e=>importSegments(e.target.files[0]).catch(h.fail));
  document.querySelectorAll("[data-transcript-field]").forEach(input=>input.addEventListener("input",e=>{A.current.working[e.target.dataset.transcriptField]=e.target.value;markDirty();}));
  document.querySelectorAll("[data-segment-field]").forEach(input=>input.addEventListener("input",e=>{
   const s=A.current.working.segments[+e.target.dataset.index],key=e.target.dataset.segmentField;
   s[key]=key==="verified"?e.target.checked:["start","end"].includes(key)?Number(e.target.value):e.target.value;
   if(key!=="verified"){s.verified=false;const checkbox=document.querySelector(`[data-segment-field="verified"][data-index="${e.target.dataset.index}"]`);if(checkbox)checkbox.checked=false;}
   A.current.working.text=A.current.working.segments.map(s=>s.text).join("\n");markDirty();
  }));
  $("#minutes-model")?.addEventListener("change",e=>{A.minutesModel=e.target.value;A.minutesTokens=Math.min(A.minutesTokens,outputCeiling(A.minutesModel));render();});
  $("#minutes-tokens")?.addEventListener("input",e=>A.minutesTokens=+e.target.value);
  $("#minutes-chars")?.addEventListener("input",e=>A.minutesChars=+e.target.value);
 }
 async function saveChanges(){
  let row=A.current;
  while(row&&A.current?.id===row.id&&A.dirty){
   const revision=A.editRevision,w=A.current.working;
   const body=JSON.parse(JSON.stringify({version:A.current.version,...Object.fromEntries(["title","text","segments","notes","meeting_date","participants","agenda","minutes_md"].map(k=>[k,w[k]])),imported_segments:A.imported}));
   const saved=await api("/api/transcripts/"+row.id,"PUT",body);
   if(A.current?.id!==row.id)return saved;
   if(revision===A.editRevision){A.current=saved;A.dirty=false;A.imported=false;}
   else{A.current.version=saved.version;A.current.updated=saved.updated;}
   row=A.current;
  }
  return row;
 }
 async function save(show=true){
  if(!A.current)return null;
  const operation=A.savePromise||(A.savePromise=saveChanges());
  try{
   const row=await operation;
   if(show&&row&&A.current?.id===row.id){render();toast("Arbeitsfassung lokal gespeichert. Original unverändert.");}
   return row;
  }catch(error){if(error.status===409)showReload(true);throw error;}
  finally{if(A.savePromise===operation)A.savePromise=null;}
 }
 async function exportCurrent(format){
  A.busy=true;render();
  try{
   const row=await save(false);if(!row)throw new Error("Kein Transkript geöffnet.");
   const response=await fetch("/api/transcripts/"+row.id+"/export?format="+format+"&version="+row.version);
   if(!response.ok){let detail="Download fehlgeschlagen; Arbeitsfassung bleibt gespeichert.";try{detail=(await response.json()).detail||detail;}catch{}if(response.status===409)showReload(true);throw new Error(detail);}
   download("protokoll-"+row.id.slice(0,8)+"."+format,await response.blob(),format==="json"?"application/json":"text/markdown");
  }finally{A.busy=false;render();}
 }
 async function importAudio(file){
  if(!file||A.busy)return;
  const project=state().project;
  if(file.size>state().data.limits.file_mb*1024*1024)throw new Error("Aufnahme übersteigt die Uploadgrenze. Ressourcengrenzen erhöhen oder Aufnahme teilen.");
  A.busy=true;render();
  try{const fd=new FormData();fd.append("file",file,file.name||A.recordName);fd.append("project_id",project);
   const doc=await api("/api/documents","POST",fd);A.audioId=doc.id;await refresh();clearRecording();toast("Audio lokal im Projekt gespeichert. Keine Modellanfrage.");
  }finally{A.busy=false;render();}
 }
 async function importSegments(file){
  if(!file||!A.current)return;
  if(file.size>state().data.limits.payload_mb*1024*1024)throw new Error("Segmentdatei übersteigt die Anfragegrösse.");
  const imported=JSON.parse(await file.text());const segments=Array.isArray(imported)?imported:imported.segments;
  if(!Array.isArray(segments)||!segments.length||segments.length>100000)throw new Error("JSON benötigt segments mit start, end, text und optional speaker (max. 100.000).");
  let previous=-1;
  for(const s of segments){if(!s||!Number.isFinite(s.start)||!Number.isFinite(s.end)||s.start<0||s.end<s.start||s.start<previous||typeof s.text!=="string"||(s.speaker!=null&&typeof s.speaker!=="string"))throw new Error("Ungültige / unsortierte Zeitsegmente. Sekundenwerte und Texte prüfen.");previous=s.start;}
  A.current.working.segments=segments.map(s=>({start:s.start,end:s.end,text:s.text,speaker:s.speaker||"",verified:false}));
  A.current.working.text=segments.map(s=>s.text).join("\n");A.current.working.segment_source="Importierte Zeitsegmente · noch nicht geprüft";
  A.imported=true;A.page=0;markDirty();render();toast("Import in der Arbeitsfassung. Prüfen und lokal speichern; Original erhalten.");
 }
 function clearRecording(){if(A.recordURL)URL.revokeObjectURL(A.recordURL);A.recordURL="";A.recorded=null;A.handle=null;A.writable=null;A.chunks=[];A.recordName="";A.recordError="";}
 async function startRecording(){
  if(active())return;
  if(A.recorded)throw new Error("Vorhandene Aufnahme zuerst übernehmen oder Vorschau schliessen.");
  if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder)throw new Error("Mikrofonaufnahme wird hier nicht unterstützt. Eine bereits gespeicherte Datei auswählen.");
  const formats=["audio/webm;codecs=opus","audio/webm","audio/mp4","audio/ogg;codecs=opus"];
  const mime=formats.find(v=>MediaRecorder.isTypeSupported(v));
  if(!mime)throw new Error("Kein unterstütztes Aufnahmeformat. Bereits gespeicherte Audiodatei wählen.");
  const suffix=mime.includes("mp4")?"m4a":mime.includes("ogg")?"ogg":"webm";
  A.preparing=true;A.recordName="aufnahme-"+new Date().toISOString().replace(/[:.]/g,"-")+"."+suffix;A.recordProject=state().project;
  A.bytes=0;A.chunks=[];A.recordError="";A.fallback=!window.showSaveFilePicker;A.writeChain=Promise.resolve();
  try{
   // The picker is called while the explicit button's user activation is live.
   if(!A.fallback){A.handle=await window.showSaveFilePicker({suggestedName:A.recordName,types:[{description:"Audioaufnahme",accept:{[mime.split(";")[0]]:["."+suffix]}}]});A.writable=await A.handle.createWritable();}
   A.stream=await navigator.mediaDevices.getUserMedia({audio:true});
   A.recorder=new MediaRecorder(A.stream,{mimeType:mime});
   A.recorder.ondataavailable=e=>{
    if(!e.data.size)return;
    A.bytes+=e.data.size;
    if(A.writable){const writer=A.writable;A.writeChain=A.writeChain.then(()=>writer.write(e.data));A.writeChain.catch(()=>{A.recordError="Schreiben auf Festplatte fehlgeschlagen. Datei prüfen; keine automatische Übernahme.";stopRecording();});}
    else A.chunks.push(e.data);
    if(A.bytes>=state().data.limits.file_mb*1024*1024){A.recordError="Aufnahme an der Uploadgrenze gestoppt. Datei prüfen; gegebenenfalls Grenze vor der Übernahme erhöhen.";stopRecording();}
   };
   A.recorder.onerror=()=>{A.recordError="Aufnahmefehler. Gespeicherte Datei prüfen; keine automatische Übernahme.";stopRecording();};
   A.recorder.onstop=async()=>{
    clearInterval(A.timer);A.stream?.getTracks().forEach(t=>t.stop());
    try{
     await A.writeChain;
     if(A.writable){await A.writable.close();A.writable=null;A.recorded=await A.handle.getFile();A.recordName=A.recorded.name||A.recordName;}
     else A.recorded=new File(A.chunks,A.recordName,{type:mime.split(";")[0]});
     if(A.recorded.size)A.recordURL=URL.createObjectURL(A.recorded);else{A.recorded=null;A.recordError="Leere Aufnahme; bitte erneut aufnehmen.";}
    }catch{A.recorded=null;A.recordError="Aufnahme konnte nicht vollständig auf Festplatte gespeichert werden. Gewählte Datei prüfen.";try{await A.writable?.abort();}catch{}A.writable=null;}
    finally{A.recording=false;A.preparing=false;A.recorder=null;A.stream=null;render();}
   };
   A.start=Date.now();A.recording=true;A.preparing=false;A.recorder.start(1000);
   A.timer=setInterval(()=>{const el=$("#record-status");if(el)el.textContent=recordStatus();},500);render();
  }catch(e){
   A.stream?.getTracks().forEach(t=>t.stop());try{await A.writable?.abort();}catch{}A.writable=null;A.preparing=false;A.recording=false;render();
   if(e.name!=="AbortError")throw new Error("Aufnahme nicht gestartet: "+e.message+". Mikrofon- und Speicherfreigabe prüfen.");
  }
 }
 function stopRecording(){if(A.recorder?.state==="recording"){A.preparing=true;A.recorder.stop();const el=$("#record-status");if(el)el.textContent="Aufnahme wird auf Festplatte fertig gespeichert …";}}
 async function action(button){
  const kind=button.dataset.action;if(!kind?.startsWith("audio-"))return false;
  if(kind!=="audio-stop"&&(active()||A.busy))throw new Error("Aufnahme zuerst fertig speichern oder laufende Verarbeitung abwarten.");
  switch(kind){
   case "audio-record":await startRecording();break;
   case "audio-stop":stopRecording();break;
   case "audio-clear-recording":clearRecording();render();break;
   case "audio-download-recording":if(A.recorded)download(A.recordName,A.recorded,A.recorded.type);break;
   case "audio-import-recording":if(!A.recorded||A.fallback)throw new Error("Zuerst eine auf Festplatte gespeicherte Datei wählen.");await importAudio(A.recorded);break;
   case "audio-pick-file":$("#audio-file").click();break;
   case "audio-refresh":await loadList();render();break;
   case "audio-open-transcript":A.busy=true;render();try{await save(false);A.current=await api("/api/transcripts/"+button.dataset.id);A.page=0;A.dirty=false;A.imported=false;A.editRevision++;}finally{A.busy=false;render();}break;
   case "audio-transcribe":{
    if(!A.audioId||A.busy)return true;const id=A.audioId,project=state().project;A.busy=true;render();
    try{await save(false);const r=await api("/api/documents/"+id+"/transcribe","POST",{model:A.model,language:A.language,response_format:A.format,project_id:project});A.current=await api("/api/transcripts/"+r.transcript_id);A.page=0;A.dirty=false;A.imported=false;A.editRevision++;await loadList();await refresh();toast(r.has_segments?"Transkript mit ungeprüften Zeitsegmenten gespeichert.":"Transkript gespeichert. Das Backend hat keine Zeitsegmente geliefert.");}finally{A.busy=false;render();}break;
   }
   case "audio-save":await save();await loadList();render();break;
   case "audio-export-md":await exportCurrent("md");break;
   case "audio-export-json":await exportCurrent("json");break;
   case "audio-download-draft":downloadDraft();break;
   case "audio-reload":if(A.savePromise)throw new Error("Laufende Speicherung zuerst abwarten.");showReload();break;
   case "audio-source":A.busy=true;render();try{const row=await save(false);await api("/api/transcripts/"+row.id+"/source","POST",{version:row.version});await refresh();toast("Gespeicherte Arbeitsfassung als separate Projektquelle übernommen.");}finally{A.busy=false;render();}break;
   case "audio-prev":A.page--;render();break;
   case "audio-next":A.page++;render();break;
   case "audio-seek":{const player=$("#transcript-audio");player.currentTime=A.current.working.segments[+button.dataset.index].start;player.play()?.catch(()=>toast("Audio ist noch nicht bereit. Aufnahme im Player starten.",true));break;}
   case "audio-flatten":A.current.working.text=A.current.working.segments.map(s=>s.text).join("\n");A.current.working.segments=[];A.current.working.segment_source="Freitext ohne Zeitsegmente · Original bleibt erhalten";markDirty();render();break;
   case "audio-import-segments":$("#segments-file").click();break;
   case "audio-diarization":modal("Sprecher und Zeitstempel",'<p>Whisper transkribiert Sprache. Für genauere Wortzeiten und automatische Sprecherwechsel eignet sich ein zusätzlicher lokal betriebener WhisperX-Dienst mit Alignment und pyannote-Diarisierung. Dieser muss von der IT bereitgestellt werden; er ist hier nicht installiert.</p><p>Die Ergebnisse kannst du als JSON importieren. Format: <code>{"segments":[{"start":0.0,"end":2.5,"text":"Guten Morgen.","speaker":"SPRECHER_01"}]}</code>. Sekunden sind relativ zum Beginn genau dieser Aufnahme. Überlappungen sind erlaubt, Startzeiten müssen sortiert sein.</p><p>Labels bezeichnen unterschiedliche Stimmen, keine bestätigten Identitäten. Sprecher manuell zuordnen und kritische Zeiten im Player abhören. Importierte und automatische Angaben bleiben ungeprüft, bis du sie bestätigt hast.</p><p><a href="https://github.com/m-bain/whisperX" target="_blank" rel="noopener noreferrer">WhisperX-Dokumentation öffnen</a></p>');break;
   case "audio-minutes":{
    if(A.busy)return true;A.busy=true;render();
    try{const row=await save(false);A.current=await api("/api/transcripts/"+row.id+"/minutes","POST",{version:row.version,model:A.minutesModel,max_tokens:A.minutesTokens,context_chars:A.minutesChars});A.dirty=false;await loadList();toast("Protokollentwurf lokal gespeichert. Am Transkript und Audio prüfen.");}finally{A.busy=false;render();}break;
   }
  }return true;
 }
 async function onOpen(){await loadList();}
 return {view,bind,action,beforeNavigate,reset,chooseAudio,hasUnsaved,onOpen};
}
