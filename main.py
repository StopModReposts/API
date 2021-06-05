from urllib.parse import SplitResult
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, Response
from fastapi.responses import RedirectResponse, StreamingResponse, PlainTextResponse, FileResponse
import air_telemetry as telemetry
from dotenv import load_dotenv
import os
from deta import Deta
from typing import Optional
import yaml
from datetime import date, datetime, time
from lxml import objectify, etree


load_dotenv()
TELEMETRY_TOKEN = os.getenv("TELEMETRY_TOKEN")
DETA_TOKEN = os.getenv("DETA_TOKEN")

app = FastAPI(title="StopModReposts API",
              description="The official StopModReposts API to get our list in all kinds of formats.",
              version="2.0",
              docs_url=None,
              redoc_url="/docs")
logger = telemetry.Endpoint("https://telemetry.brry.cc", "smr-api", TELEMETRY_TOKEN)
deta = Deta(DETA_TOKEN)
drive = deta.Drive("formats")
stats = deta.Base("smr-stats")
        

def statcounter():
    try:
        month = str(datetime.now().month)
        request = next(stats.fetch({"month": month}))[0]
        stats.put({
            "month": month,
            "total": int(request["total"]) + 1
        }, request["key"])
    except:
        month = str(datetime.now().month)
        stats.insert({
            "month": month,
            "total": 1
        })

@app.get("/")
def root():
    return RedirectResponse("https://stopmodreposts.org")

@app.get("/favicon.ico")
def favicon():
    return FileResponse("favicon.ico")

@app.get("/sites.yaml")
def get_yaml(background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the YAML format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}.yaml".format(game))
    return StreamingResponse(res.iter_chunks(1024), media_type="application/yaml")
        
@app.get("/sites.json")
def get_json(background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the JSON format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}.yaml".format(game))
    return yaml.load(res.read(), Loader=yaml.FullLoader)
        
@app.get("/sites.txt", response_class=PlainTextResponse)
def get_txt(background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the TXT format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}.yaml".format(game))
    data = yaml.load(res.read(), Loader=yaml.FullLoader)
    txt = ""
    for item in data:
        txt = txt + item["domain"] + "\n"
    return txt
    
@app.get("/hosts.txt", response_class=PlainTextResponse)
def get_hosts(background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the HOSTS.TXT format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}.yaml".format(game))
    data = yaml.load(res.read(), Loader=yaml.FullLoader)
    with open("templates/hosts.txt", "r") as f:
        hosts = f.read().format(str(datetime.now()))
    hosts = hosts + "\n \n"
    for item in data:
        hosts = hosts  + "0.0.0.0 " + item["domain"] + "\n" 
    hosts = hosts + "\n" + "# === End of StopModReposts site list ==="
    return hosts

@app.get("/ublacklist",response_class=PlainTextResponse)
def get_ublacklist(background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the uBlacklist format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}.yaml".format(game))
    data = yaml.load(res.read(), Loader=yaml.FullLoader)
    blacklist = ""
    for item in data:
        try:
            # -------------------------------------
            # remove/change with list yaml format
            # -------------------------------------
            path = item["path"] + "/*"
        except:
            path = "/*"
        blacklist = blacklist + "*://*." + item["domain"] + path + "\n"
    return blacklist

@app.get("/sites.xml")
def get_xml(background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the XML format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}.yaml".format(game))
    data = yaml.load(res.read(), Loader=yaml.FullLoader)
    sites = objectify.Element("sites", nsmap='', _pytype='')
    # -------------------------------------
    # change with list yaml format
    # -------------------------------------
    for item in data:
        site = objectify.Element("site", nsmap='', _pytype='')
        site.domain = item["domain"]
        site.date = "15. September 2019"
        site.reason = "Reposting site"
        site.notes = "Reposting site"
        site.path = "/"
        sites.append(site)
    
    objectify.deannotate(sites)
    etree.cleanup_namespaces(sites)
    return Response(content=etree.tostring(sites, pretty_print=True, xml_declaration=True, with_tail=False), media_type="application/xml")

@app.get("/sites.nbt")
def get_nbt(background_tasks: BackgroundTasks):
    """
    Get the combined list in the NBT format **(deprecated - will be removed soon)**.
    """
    
    background_tasks.add_task(statcounter)
    raise HTTPException(status_code=400, detail="This format is deprecated and will soon be removed. Please use a different one: https://github.com/StopModReposts/Illegal-Mod-Sites/wiki/API-access-and-formats")

    
if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=80)