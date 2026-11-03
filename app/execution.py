"""Opt-in, networkless container execution. Never falls back to host Python."""
import asyncio
import os
import shutil
from pathlib import Path
from . import store, documents, limits

IMAGE = "gpustack-workroom-runner:local"

def enabled():
    return os.environ.get("WORKROOM_ENABLE_RUNNER") == "1"

async def run_python(project_id, code, docs):
    if not enabled():
        raise ValueError("Das Datenlabor ist nicht aktiviert. Docker-Runner gemäß README einrichten.")
    if not shutil.which("docker"):
        raise ValueError("Docker wurde nicht gefunden. Es wird kein Code auf dem Host ausgeführt.")
    if len(code)>500_000:
        raise ValueError("Code ist zu lang.")
    ident=store.uid()
    cfg=limits.current()
    root=store.DATA/"jobs"/ident
    inputs,outputs=root/"input",root/"output"
    inputs.mkdir(parents=True); outputs.mkdir()
    outputs.chmod(0o777)
    names=set()
    for doc in docs:
        name=doc["name"]
        if name in names: name=doc["id"][:8]+"_"+name
        names.add(name)
        shutil.copyfile(documents.path_for(doc),inputs/name)
    script=root/"task.py"
    script.write_text(code,encoding="utf-8")
    name="workroom-"+ident
    args=["docker","run","--rm","--pull","never","--name",name,"--network","none",
        "--memory",f"{cfg['runner_memory_mb']}m","--memory-swap",f"{cfg['runner_memory_mb']}m","--cpus","1","--pids-limit","64",
        "--read-only","--cap-drop","ALL","--security-opt","no-new-privileges",
        "--user","65534:65534","--tmpfs",f"/tmp:rw,noexec,nosuid,size={cfg['runner_tmp_mb']}m",
        "--ulimit",f"fsize={cfg['runner_output_mb']*1024*1024}:{cfg['runner_output_mb']*1024*1024}",
        "--mount",f"type=bind,src={inputs},dst=/input,readonly",
        "--mount",f"type=bind,src={outputs},dst=/output",
        "--mount",f"type=bind,src={script},dst=/task.py,readonly",
        "--workdir","/output",IMAGE,"python","/task.py"]
    output=bytearray()
    process=None
    status="Fehler"
    truncated=False
    try:
        process=await asyncio.create_subprocess_exec(*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.STDOUT)
        async def consume():
            nonlocal truncated
            while True:
                block=await process.stdout.read(8192)
                if not block: break
                if len(output)+len(block)>1_000_000: truncated=True
                if len(output)<1_000_000: output.extend(block[:1_000_000-len(output)])
            return await process.wait()
        async with asyncio.timeout(cfg["runner_seconds"]):
            returncode=await consume()
        status="Fertig" if returncode==0 else "Fehler"
    except TimeoutError:
        output.extend(f"\nZeitlimit: {cfg['runner_seconds']} Sekunden. Container beendet.".encode())
    finally:
        if process and process.returncode is None:
            stop=await asyncio.create_subprocess_exec("docker","rm","-f",name,
                stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL)
            try: await asyncio.wait_for(stop.wait(),10)
            except TimeoutError: stop.kill()
            process.kill()
            await process.wait()
    allowed={".csv",".xlsx",".pptx",".pdf",".png",".jpg",".txt",".md",".json"}
    artifacts=[]
    total=0
    for p in outputs.iterdir():
        if p.is_symlink() or not p.is_file() or p.suffix.lower() not in allowed:
            continue
        total+=p.stat().st_size
        if total>cfg["runner_output_mb"]*1024*1024:
            status="Ausgabe zu groß"
            break
        artifacts.append({"name":p.name,"size":p.stat().st_size})
    result=output.decode("utf-8",errors="replace")
    if truncated: result+="\nTextausgabe nach 1 Mio. Bytes begrenzt. Vollständige Ergebnisse im Skript als Datei unter /output speichern."
    store.run("INSERT INTO jobs VALUES(?,?,?,?,?)",(ident,project_id,status,result,store.now()))
    return {"id":ident,"status":status,"output":result,"files":artifacts}
