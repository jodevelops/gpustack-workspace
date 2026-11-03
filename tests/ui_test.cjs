/* DOM + backend integration test. Layout/browser rendering is not emulated. */
const fs=require("fs"),path=require("path"),vm=require("vm"),{spawn}=require("child_process"),assert=require("assert/strict");
const {JSDOM}=require(process.env.JSDOM_PATH || "jsdom");
const root=path.resolve(__dirname,"..");
const child=spawn(process.env.PYTHON || "python",["-m","tests.ui_bridge"],{cwd:root,stdio:["pipe","pipe","inherit"]});
const pending=new Map();let seq=0,buf="";
child.stdout.on("data",chunk=>{buf+=chunk;let n;while((n=buf.indexOf("\n"))>=0){const line=buf.slice(0,n);buf=buf.slice(n+1);const r=JSON.parse(line);pending.get(r.id)?.(new Response(r.body,{status:r.status,headers:r.headers}));pending.delete(r.id);}});
const dom=new JSDOM(fs.readFileSync(path.join(root,"web/index.html"),"utf8"),{url:"http://localhost/",runScripts:"outside-only",pretendToBeVisual:true});
const w=dom.window;
const NativeFormData=w.FormData;
w.File=File;w.FormData=class extends FormData {
 constructor(form) {
  super();
  if(form)for(const [key,value] of new NativeFormData(form).entries()) {
   assert.equal(typeof value,"string","HTML file fields need a separate fixture");
   this.append(key,value);
  }
 }
};
const requestLog=[];
w.fetch=async(url,opts={})=>{
 requestLog.push({url,method:opts.method||"GET"});
 const request={path:url,method:opts.method||"GET",headers:opts.headers||{},body:opts.body};
 if(opts.body instanceof FormData) {
  request.multipart={fields:{},files:[]};delete request.body;
  for(const [field,value] of opts.body.entries()) {
   if(typeof value==="string")request.multipart.fields[field]=value;
   else request.multipart.files.push({field,name:value.name,type:value.type,base64:Buffer.from(await value.arrayBuffer()).toString("base64")});
  }
 }
 return new Promise(resolve=>{const id=++seq;pending.set(id,resolve);child.stdin.write(JSON.stringify({id,...request})+"\n");});
};
w.Blob=Blob;
w.TextDecoder=TextDecoder;w.TextEncoder=TextEncoder;w.Response=Response;
const downloadedBlobs=[];
w.URL.createObjectURL=blob=>{downloadedBlobs.push(blob);return "blob:test";};
w.HTMLAnchorElement.prototype.click=function(){};w.URL.revokeObjectURL=()=>{};
w.navigator.clipboard={writeText:async()=>{}};
w.HTMLDialogElement.prototype.showModal=function(){this.open=true;};
w.HTMLDialogElement.prototype.close=function(){this.open=false;};
const recordingLog=[];
w.MediaRecorder=class {
 static isTypeSupported(mime){return mime.startsWith("audio/webm");}
 constructor(stream,opts){this.state="inactive";this.mimeType=opts.mimeType;}
 start(){this.state="recording";recordingLog.push("start");}
 stop(){this.state="inactive";this.ondataavailable({data:new Blob(["synthetic audio bytes"])});queueMicrotask(()=>this.onstop());}
};
w.navigator.mediaDevices={getUserMedia:async()=>{recordingLog.push("microphone");return {getTracks:()=>[{stop:()=>recordingLog.push("track-stop")}]};}};
w.showSaveFilePicker=async()=>{recordingLog.push("picker");const chunks=[];return {createWritable:async()=>({write:async b=>{recordingLog.push("write");chunks.push(b);},close:async()=>recordingLog.push("close"),abort:async()=>recordingLog.push("abort")}),getFile:async()=>{recordingLog.push("get-file");return new File(chunks,"recording.webm",{type:"audio/webm"});}};};
w.HTMLMediaElement.prototype.play=async function(){return;};
const registered=[];
w.document.modelContext={registerTool:tool=>registered.push(tool)};
const context=dom.getInternalVMContext();
vm.runInContext(fs.readFileSync(path.join(root,"web/websearch.js"),"utf8").replace("export function createWebWorkspace", "function createWebWorkspace"),context);
vm.runInContext(fs.readFileSync(path.join(root,"web/audio.js"),"utf8").replace("export function createAudioWorkspace", "function createAudioWorkspace"),context);
let source=fs.readFileSync(path.join(root,"web/app.js"),"utf8").replace(/^import .*\n/gm,"").replace("await boot();","globalThis.bootPromise=boot();");
vm.runInContext(source,context);
const evaluate=code=>vm.runInContext(code,context);
const q=s=>w.document.querySelector(s);
const click=s=>{const el=q(s);assert.ok(el,"Element not found: "+s);el.click();};
const input=(s,v)=>{const el=q(s);assert.ok(el,"Input not found: "+s);el.value=v;el.dispatchEvent(new w.Event("input",{bubbles:true}));};
const submit=s=>q(s).dispatchEvent(new w.Event("submit",{bubbles:true,cancelable:true}));
async function waitFor(fn){for(let i=0;i<100;i++){if(fn())return;await new Promise(r=>setTimeout(r,15));}throw new Error("UI condition timed out");}
async function test() {
 await w.bootPromise;
 assert.ok(q(".welcome"));assert.equal(q("#chat-model").options.length,4);
 assert.equal(registered[0].name,"stage_chat_draft");
 const draft=await registered[0].execute({text:"Vorbereiteter Entwurf"});
 assert.equal(draft.sent,false);assert.equal(q("#message-input").value,"Vorbereiteter Entwurf");
 await assert.rejects(()=>registered[0].execute({text:"",unexpected:true}));
 click('[data-view="projects"]');await waitFor(()=>q(".page-heading h2")?.textContent.includes("Ein Kontext"));
 click('[data-action="new-project"]');await waitFor(()=>q("#f-name"));input("#f-name","UI Testprojekt");input("#f-memory","Nachweise prüfen");submit("#modal-form");
 await waitFor(()=>!q("#modal").open);assert.ok(w.document.body.textContent.includes("UI Testprojekt"));
 click('[data-view="prompts"]');await waitFor(()=>q(".page-heading h2")?.textContent.includes("Arbeitsweisen"));
 click('[data-action="new-prompt"]');input("#f-name","Testvorlage");input("#f-content","Nur belegte Angaben.");submit("#modal-form");
 await waitFor(()=>!q("#modal").open);assert.ok(w.document.body.textContent.includes("Testvorlage"));
 click('[data-action="settings"]');await waitFor(()=>q("#connection-form"));
 input("#base-url","https://gpustack.test/v1");input("#api-key","TEST_SECRET_UI_ONLY");
 click('[data-action="test-connection"]');await waitFor(()=>q(".connection .connected"));
 assert.equal(q("#api-key").value,"");assert.ok(!w.document.body.innerHTML.includes("TEST_SECRET_UI_ONLY"));
 click('[data-view="chat"]');await waitFor(()=>q("#message-input"));
 input("#message-input","Was ist ein Arbeitsraum?");submit("#chat-form");
 await waitFor(()=>q(".message.assistant")&&!q(".waiting"));
 assert.ok(q(".message.assistant").textContent.includes("Testantwort"));
 assert.ok(q(".thread-link"));
 assert.ok(q(".model-reasoning").textContent.includes("Gelieferte Testbegründung"));
 assert.equal(q(".chat-layout").classList.contains("panel-open"),false);
 click('[data-action="toggle-panel"]');assert.equal(q(".chat-layout").classList.contains("panel-open"),true);
 assert.equal(q('[data-action="toggle-panel"]').getAttribute("aria-expanded"),"true");
 // Budget results expire on edits; delayed results cannot describe a newer draft.
 click('[data-tab="parameters"]');input("#message-input","Budgetprobe");
 await evaluate('checkBudget()');assert.ok(q("#budget-result").textContent.includes("zusammengestellten"));
 input("#max-tokens","9000");assert.ok(!q("#budget-result").textContent.includes("zusammengestellten"));
 const budgetFetch=w.fetch;let budgetHeld=false,releaseBudget;const budgetGate=new Promise(resolve=>releaseBudget=resolve);
 w.fetch=async(url,opts={})=>{const response=await budgetFetch(url,opts);if(url.endsWith("/budget")){budgetHeld=true;await budgetGate;}return response;};
 const checking=evaluate('checkBudget()');await waitFor(()=>budgetHeld);input("#message-input","Neuere Budgetprobe");releaseBudget();await checking;w.fetch=budgetFetch;
 assert.ok(!q("#budget-result").textContent.includes("zusammengestellten"));
 input("#message-input","");
 click('[data-action="close-panel"]');assert.equal(q(".inspector").classList.contains("open"),false);
 click('[data-action="export-chat"]');assert.equal(q("#export-reasoning").checked,false);assert.ok(q("#export-md").href.endsWith("include_reasoning=false"));
 q("#export-reasoning").checked=true;q("#export-reasoning").dispatchEvent(new w.Event("change"));assert.ok(q("#export-json").href.endsWith("include_reasoning=true"));q("[data-close]").click();
 // Persisted image/PDF cards open originals at large size; a scan needs no OCR to preview.
 await evaluate('uploadFiles([new File([Uint8Array.from(atob("iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAIAAADZF8uwAAAAFUlEQVR4nGP8z0AYMBGhZlQR3RUBAM/gARe7TQcrAAAAAElFTkSuQmCC"),c=>c.charCodeAt(0))],"preview.png",{type:"image/png"})])');
 assert.ok(q("#selection-chips .media-card img"));click('#selection-chips .media-card');await waitFor(()=>q(".media-viewer img"));assert.ok(q("#modal").classList.contains("media-modal"));q("[data-close]").click();
 await evaluate('uploadFiles([new File([Uint8Array.from(atob("JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovUHJvZHVjZXIgKHB5cGRmKQo+PgplbmRvYmoKMiAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyA0IDAgUiBdCj4+CmVuZG9iagozIDAgb2JqCjw8Ci9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKNCAwIG9iago8PAovVHlwZSAvUGFnZQovUmVzb3VyY2VzIDw8Cj4+Ci9NZWRpYUJveCBbIDAuMCAwLjAgMTAwIDEwMCBdCi9QYXJlbnQgMiAwIFIKPj4KZW5kb2JqCnhyZWYKMCA1CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAxNSAwMDAwMCBuIAowMDAwMDAwMDU0IDAwMDAwIG4gCjAwMDAwMDAxMTMgMDAwMDAgbiAKMDAwMDAwMDE2MiAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDUKL1Jvb3QgMyAwIFIKL0luZm8gMSAwIFIKPj4Kc3RhcnR4cmVmCjI1NgolJUVPRgo="),c=>c.charCodeAt(0))],"preview.pdf",{type:"application/pdf"})])');
 const pdfId=evaluate('S.docs.find(d=>d.name==="preview.pdf")?.id');assert.ok(pdfId);
 await evaluate('previewDoc('+JSON.stringify(pdfId)+')');assert.ok(q(".pdf-viewer"));q("[data-close]").click();
 // Audio has no implicit upload/inference, and the file is closed before import.
 click('[data-view="audio"]');await waitFor(()=>q("#audio-document"));
 const inferenceBefore=requestLog.filter(x=>x.url.endsWith("/transcribe")).length;
 const uploadBefore=requestLog.filter(x=>x.url==="/api/documents"&&x.method==="POST").length;
 click('[data-action="audio-record"]');await waitFor(()=>recordingLog.includes("start"));
 assert.deepEqual(recordingLog.slice(0,3),["picker","microphone","start"]);
 click('[data-action="audio-stop"]');await waitFor(()=>q('[data-action="audio-import-recording"]'));
 assert.ok(recordingLog.indexOf("write")<recordingLog.indexOf("close"));assert.ok(recordingLog.indexOf("close")<recordingLog.indexOf("get-file"));assert.ok(recordingLog.includes("track-stop"));
 assert.equal(requestLog.filter(x=>x.url==="/api/documents"&&x.method==="POST").length,uploadBefore);
 click('[data-action="audio-import-recording"]');await waitFor(()=>q("#audio-document").value);
 assert.equal(requestLog.filter(x=>x.url.endsWith("/transcribe")).length,inferenceBefore);
 q("#audio-format").value="verbose_json";q("#audio-format").dispatchEvent(new w.Event("change"));
 click('[data-action="audio-transcribe"]');await waitFor(()=>q(".segment"));
 input('[data-segment-field="text"][data-index="0"]',"Guten Tag.");input('[data-segment-field="speaker"][data-index="0"]',"Anna");
 assert.ok(q("#transcript-save-state").textContent.includes("Ungespeichert"));
 click('[data-action="audio-save"]');await waitFor(()=>q("#transcript-save-state").textContent.includes("Version 2"));
 // A delayed save must not overwrite text entered after the request snapshot.
 const transcriptId=(await evaluate('api("/api/transcripts?project_id="+S.project)'))[0].id;
 const originalFetch=w.fetch;let saveHeld=false,releaseSave;const saveGate=new Promise(resolve=>releaseSave=resolve);
 w.fetch=async(url,opts={})=>{const response=await originalFetch(url,opts);if(opts.method==="PUT"&&url==="/api/transcripts/"+transcriptId&&!saveHeld){saveHeld=true;await saveGate;}return response;};
 input("#f-notes","Vor der Speicherung");click('[data-action="audio-save"]');await waitFor(()=>saveHeld);
 input("#f-notes","Während der Speicherung ergänzt");click('[data-action="audio-save"]');releaseSave();
 await waitFor(()=>q("#transcript-save-state")?.textContent.includes("Lokal gespeichert"));
 assert.equal(q("#f-notes").value,"Während der Speicherung ergänzt","late edits must survive the save response");
 const savedAfterDelay=await evaluate('api("/api/transcripts/"+'+JSON.stringify(transcriptId)+')');
 assert.equal(savedAfterDelay.working.notes,"Während der Speicherung ergänzt");w.fetch=originalFetch;
 // Downloads save the visible edits first, even after a re-render.
 input("#f-notes","Aktuelle Downloadfassung − UTF-8");evaluate('render()');
 let downloadCount=downloadedBlobs.length;
 click('[data-action="audio-export-md"]');await waitFor(()=>downloadedBlobs.length>downloadCount);
 assert.ok((await downloadedBlobs.at(-1).text()).includes("Aktuelle Downloadfassung − UTF-8"));
 await waitFor(()=>!q('[data-action="audio-export-md"]').disabled);
 // A second window may have changed the version. Preserve and download the local draft before reloading.
 await evaluate('(async()=>{const row=await api("/api/transcripts/"+'+JSON.stringify(transcriptId)+');const keys=["title","text","segments","notes","meeting_date","participants","agenda","minutes_md"];await api("/api/transcripts/"+row.id,"PUT",{version:row.version,...Object.fromEntries(keys.map(k=>[k,row.working[k]])),notes:"Fassung aus anderem Fenster"});})()');
 input("#f-notes","Mein ungespeicherter Entwurf");click('[data-action="audio-export-json"]');
 await waitFor(()=>q("#modal").open&&q("#download-transcript-draft"));
 assert.equal(q("#f-notes").value,"Mein ungespeicherter Entwurf");
 downloadCount=downloadedBlobs.length;click("#download-transcript-draft");assert.equal(downloadedBlobs.length,downloadCount+1);
 const draftExport=JSON.parse(await downloadedBlobs.at(-1).text());assert.equal(draftExport.working.notes,"Mein ungespeicherter Entwurf");
 submit("#modal-form");await waitFor(()=>!q("#modal").open);assert.equal(q("#f-notes").value,"Fassung aus anderem Fenster");
 click('[data-action="audio-seek"][data-index="1"]');assert.equal(q("#transcript-audio").currentTime,1.6);
 click('[data-action="audio-minutes"]');await waitFor(()=>q("#f-minutes_md")?.value.includes("Testantwort"));
 assert.equal(q("#f-title").value,"recording");
 click('[data-action="audio-diarization"]');assert.ok(q("#modal").textContent.includes("nicht installiert"));q("[data-close]").click();
 // Browser fallback requires saving and then explicitly selecting a disk file.
 w.showSaveFilePicker=undefined;click('[data-action="audio-record"]');await waitFor(()=>q('[data-action="audio-stop"]')&&!q('[data-action="audio-stop"]').disabled);
 click('[data-action="audio-stop"]');await waitFor(()=>q('[data-action="audio-download-recording"]'));
 assert.equal(q('[data-action="audio-import-recording"]'),null);click('[data-action="audio-clear-recording"]');
 // Opening a thread from another project clears the audio editor and saves its current edits.
 const homeProject=evaluate('S.project'),homeThread=evaluate('S.thread');
 const otherProject=await evaluate('api("/api/projects","POST",{name:"Audio isolation"})');
 const otherThread=await evaluate('api("/api/threads","POST",{project_id:'+JSON.stringify(otherProject.id)+',title:"Anderes Projekt"})');
 // An unimported saved recording must block this route just as it blocks the project selector.
 click('[data-action="audio-record"]');await waitFor(()=>q('[data-action="audio-stop"]')&&!q('[data-action="audio-stop"]').disabled);
 click('[data-action="audio-stop"]');await waitFor(()=>q('[data-action="audio-download-recording"]'));
 await assert.rejects(()=>evaluate('openThread('+JSON.stringify(otherThread.id)+')'),/Aufnahme/);
 assert.equal(evaluate('S.project'),homeProject);click('[data-action="audio-clear-recording"]');
 input("#f-notes","Vor dem Projektwechsel sichern");
 await evaluate('openThread('+JSON.stringify(otherThread.id)+')');
 await evaluate('navigate("audio")');assert.equal(q("#f-notes"),null);
 assert.equal(q('[data-action="audio-open-transcript"]'),null,"other project must not show the previous transcript");
 const savedBeforeSwitch=await evaluate('api("/api/transcripts/"+'+JSON.stringify(transcriptId)+')');
 assert.equal(savedBeforeSwitch.working.notes,"Vor dem Projektwechsel sichern");
 await evaluate('openThread('+JSON.stringify(homeThread)+')');assert.equal(evaluate('S.project'),homeProject);
 click('[data-view="history"]');await waitFor(()=>q("#history-results"));
 assert.ok(q("#history-results").textContent.includes("Was ist ein Arbeitsraum?"));
 input("#history-search","doesnotexist");await waitFor(()=>q("#history-results").textContent.includes("Noch keine passenden"));
 click('[data-view="library"]');await waitFor(()=>q("#dropzone"));assert.ok(q("#library-global"));
 evaluate("S.selected.clear();S.attachments.clear()");
 // Resource settings, archive fallback, reprocessing and paginated preview use the real API.
 click('[data-action="settings"]');await waitFor(()=>q("#limits-form"));
 input("#f-text_chars","1000");submit("#limits-form");
 await waitFor(()=>evaluate('S.data.limits.text_chars===1000'));
 click('[data-view="chat"]');await waitFor(()=>q("#message-input"));
 await evaluate('uploadFiles([new File(["Zeile Bern −\\n".repeat(18000)],"ui-gross.txt")])');
 assert.ok(q("#modal").textContent.includes("Original gespeichert"));
 const largeId=evaluate('S.docs.find(d=>d.name==="ui-gross.txt").id');
 assert.equal(evaluate('S.selected.size'),0);q("[data-close]").click();
 click('[data-view="library"]');await waitFor(()=>q("#dropzone"));
 assert.equal(q('[data-source="'+largeId+'"]').disabled,true);
 click('[data-action="settings"]');await waitFor(()=>q("#limits-form"));
 input("#f-text_chars","20000000");submit("#limits-form");
 await waitFor(()=>evaluate('S.data.limits.text_chars===20000000'));
 click('[data-view="library"]');await waitFor(()=>q('[data-action="reprocess-doc"]'));
 click('[data-action="reprocess-doc"][data-id="'+largeId+'"]');
 await waitFor(()=>evaluate('S.docs.find(d=>d.id==='+JSON.stringify(largeId)+').status==="bereit"'));
 assert.equal(q('[data-source="'+largeId+'"]').disabled,false);
 click('[data-action="preview-doc"][data-id="'+largeId+'"]');await waitFor(()=>q("#preview-next"));
 q("#preview-next").click();await waitFor(()=>q("#preview-prev"));
 assert.ok(q("#modal").textContent.includes("101–"));q("[data-close]").click();
 q("#import-mode").value="original";q("#import-mode").dispatchEvent(new w.Event("change",{bubbles:true}));
 await evaluate('uploadFiles([new File(["Nur ablegen"],"ui-original.csv")])');
 assert.equal(evaluate('S.docs.find(d=>d.name==="ui-original.csv").status'),"ablage");q("[data-close]").click();
 click('[data-view="research"]');await waitFor(()=>q("#research-form"));assert.equal(q("#research-form button").disabled,true);
 click('[data-action="settings"]');await waitFor(()=>q("#connection-form"));
 input("#research-contact","operator@example.org");q("#internet-enabled").checked=true;submit("#connection-form");
 await waitFor(()=>q("#research-contact")?.value==="mailto:operator@example.org");
 click('[data-view="research"]');await waitFor(()=>q("#research-form"));
 assert.equal(q("#research-source").options.length,5);
 input("#research-query","Bern");input("#research-source","wikidata");
 q("#research-source").dispatchEvent(new w.Event("change",{bubbles:true}));submit("#research-form");
 await waitFor(()=>q(".result-card"));
 assert.ok(q(".result-card").textContent.includes("Bern"));
 const retrieved=evaluate("S.researchRetrievedAt");assert.ok(retrieved);
 // Selecting another provider must not relabel the already-returned source.
 input("#research-source","datacite");q("#research-source").dispatchEvent(new w.Event("change",{bubbles:true}));
 click('[data-action="save-research"]');
 await waitFor(()=>evaluate('S.docs.some(d=>d.name==="recherche-1.md")'));
 const savedId=evaluate('S.docs.find(d=>d.name==="recherche-1.md").id');
 const saved=await evaluate('api("/api/documents/"+'+JSON.stringify(savedId)+'+"/text")');
 assert.ok(saved.chunks[0].content.includes("Datenquelle: wikidata"));
 assert.ok(saved.chunks[0].content.includes("Suchtext: Bern"));
 assert.ok(saved.chunks[0].content.includes("Abruf: "+retrieved));
 // General web search is separately configured; the provider never receives the whole chat.
 click('[data-action="settings"]');await waitFor(()=>q("#web-config-form"));
 // Reading help and choosing a provider preserves unsaved credentials and makes no request.
 input("#web-api-key","UNSAVED_SEARCH_KEY");
 const helpRequests=requestLog.length;
 click('[data-action="web-setup"]');
 assert.ok(q("#modal").open);assert.ok(q("#modal").textContent.includes("API Keys → Add API Key"));
 assert.ok(q("#modal").textContent.includes("Speicherrechte"));
 assert.ok(!q("#modal").textContent.includes("UNSAVED_SEARCH_KEY"));
 assert.ok(q('#modal a[href="/static/websearch-guide.md"]').hasAttribute("download"));
 for(const link of q("#modal").querySelectorAll('a[href^="https:"]'))assert.equal(link.rel,"noopener noreferrer");
 click("#web-guide-brave");await waitFor(()=>!q("#modal").open);
 assert.equal(q("#web-provider").value,"brave");assert.equal(q("#web-api-key").value,"UNSAVED_SEARCH_KEY");
 assert.equal(q("#brave-storage-note").classList.contains("hidden"),false);
 assert.equal(w.document.activeElement.id,"web-api-key");
 click('[data-action="web-setup"]');click("#web-guide-searxng");await waitFor(()=>!q("#modal").open);
 assert.equal(q("#web-provider").value,"searxng");assert.equal(q("#web-api-key").value,"UNSAVED_SEARCH_KEY");
 assert.equal(w.document.activeElement.id,"searxng-url");assert.equal(requestLog.length,helpRequests);
 const localGuide=await w.fetch("/static/websearch-guide.md");assert.equal(localGuide.status,200);
 const guideText=await localGuide.text();assert.ok(guideText.includes("API Keys"));assert.ok(guideText.includes("search:"));
 assert.ok(!guideText.includes("UNSAVED_SEARCH_KEY"));input("#web-api-key","");
 input("#searxng-url","https://searx.public.example");submit("#web-config-form");
 await waitFor(()=>evaluate('S.data.web_search.ready')&&!q('[data-action="web-open-search"]').disabled);assert.equal(q("#web-api-key").value,"");
 click('[data-action="web-open-search"]');await waitFor(()=>q("#research-source")?.value==="web");
 click('[data-action="web-setup"]');assert.ok(q("#modal").open);
 click("#web-guide-searxng");await waitFor(()=>q("#web-config-form")&&!q("#modal").open);
 assert.equal(q("#web-provider").value,"searxng");assert.equal(q("#searxng-url").value,"https://searx.public.example");
 click('[data-action="web-open-search"]');await waitFor(()=>q("#research-source")?.value==="web");
 input("#research-query","IIIF");submit("#research-form");await waitFor(()=>q('[data-action="web-read-result"]'));
 assert.ok(q(".result-card").textContent.includes("Suchauszug"));
 click('[data-action="web-read-result"]');await waitFor(()=>q("#web-save-page"));
 assert.ok(q(".web-page-extract").textContent.includes("Gelesener Inhalt − Unicode."));
 assert.ok(!q(".web-page-extract").textContent.includes("BAD_SCRIPT"));
 const docsBefore=evaluate('S.docs.length');click("#web-save-page");await waitFor(()=>!q("#modal").open);
 assert.equal(evaluate('S.docs.length'),docsBefore+1);
 click('[data-view="chat"]');await waitFor(()=>q("#chat-web-enabled"));
 assert.equal(q("#chat-web-enabled").checked,false);q("#chat-web-enabled").checked=true;q("#chat-web-enabled").dispatchEvent(new w.Event("change"));
 input("#message-input","PRIVATE_CHAT_QUESTION");input("#chat-web-query","IIIF");
 q("#chat-web-pages").checked=true;q("#chat-web-pages").dispatchEvent(new w.Event("change"));
 submit("#chat-form");await waitFor(()=>!evaluate('S.busy')&&evaluate('S.messages.at(-1).metadata.web_search?.sent_query==="IIIF"'));
 assert.equal(evaluate('S.messages.at(-1).metadata.web_search.sent_query'),"IIIF");
 assert.equal(evaluate('S.messages.at(-1).metadata.sources.at(-1).kind'),"page");
 assert.equal(q("#chat-web-enabled").checked,false,"new searches require a fresh per-message opt-in");
 click('.source-tags button[data-proof]');assert.ok(q("#modal").textContent.includes("Extrahierter Webtext"));q("[data-close]").click();
 const blobsBefore=downloadedBlobs.length;click('[data-action="download-message"][data-index="'+evaluate('S.messages.length-1')+'"]');submit("#modal-form");await waitFor(()=>downloadedBlobs.length>blobsBefore);
 assert.ok((await downloadedBlobs.at(-1).text()).includes("https://public.example/iiif"));
 await waitFor(()=>!q("#modal").open);
 // Stopping before the response arrives must restore the unsent question.
 const beforeAbort=w.fetch;let pendingWeb=false;
 w.fetch=(url,opts={})=>{if(url.endsWith("/send")){pendingWeb=true;return new Promise((resolve,reject)=>opts.signal.addEventListener("abort",()=>reject(new w.DOMException("stopped","AbortError"))));}return beforeAbort(url,opts);};
 q("#chat-web-enabled").checked=true;q("#chat-web-enabled").dispatchEvent(new w.Event("change"));input("#message-input","Frage vor Abbruch");
 submit("#chat-form");await waitFor(()=>pendingWeb);click('[data-action="stop"]');await waitFor(()=>!evaluate('S.busy'));
 assert.equal(q("#message-input").value,"Frage vor Abbruch");w.fetch=beforeAbort;
 q("#chat-web-enabled").checked=false;q("#chat-web-enabled").dispatchEvent(new w.Event("change"));
 click('[data-view="routines"]');await waitFor(()=>q('[data-action="new-routine"]'));
 click('[data-action="new-routine"]');input("#f-name","UI Routine");input("#f-prompt","Prüfe Quellen.");submit("#modal-form");
 await waitFor(()=>!q("#modal").open);assert.ok(w.document.body.textContent.includes("UI Routine"));assert.ok(w.document.body.textContent.includes("Pausiert"));
 click('[data-view="lab"]');await waitFor(()=>q("#lab-code"));assert.equal(q('[data-action="run-code"]').disabled,true);
 click('[data-action="opencode"]');assert.ok(q("#modal").textContent.includes("nicht eingebettet"));q("[data-close]").click();
 // All user/model content must stay text; generated tags cannot execute.
 assert.ok(evaluate('markdown("<img src=x onerror=alert(1)>")').includes("&lt;img"));
 assert.equal(q('script[src^="http"]'),null);
 console.log("UI integration passed (DOM + real local API; model mocked; no visual layout test).");
}
test().then(()=>{child.stdin.end();dom.window.close();},e=>{console.error(e);child.kill();dom.window.close();process.exitCode=1;});
