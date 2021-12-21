import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, Response, Request
from fastapi.responses import RedirectResponse, StreamingResponse, PlainTextResponse
from dotenv import load_dotenv
import os
from deta import Deta
from typing import Optional
import yaml
from datetime import datetime
from lxml import objectify, etree
import sentry_sdk
import secure

load_dotenv()
DETA_TOKEN = os.getenv("DETA_TOKEN")

sentry_sdk.init(
    "https://e7f6d56016d747bc88bbdb5a29d0fdd5@o309026.ingest.sentry.io/5834878",
    traces_sample_rate=1.0
)

app = FastAPI(title="StopModReposts API",
              description="The official StopModReposts API to get our list in all kinds of formats.",
              version="2.0",
              docs_url="/debug",
              redoc_url="/docs")
deta = Deta(DETA_TOKEN)
drive = deta.Drive("formats")
stats = deta.Base("smr-stats")
times = deta.Base("smr-timestamps")

"""
secure_headers = secure.Secure()

@app.middleware("http")
async def set_secure_headers(request, call_next):
    response = await call_next(request)
    secure_headers.framework.fastapi(response)
    return response
"""

def statcounter():
    try:
        month = str(datetime.now().month)
        request = stats.fetch({"month": month}).items[0]
        stats.update({
            "month": month,
            "total": int(request["total"]) + 1
        }, request["key"])
    except:
        month = str(datetime.now().month)
        stats.insert({
            "month": month,
            "total": 1
        })
        
def timestamps(game):
    try:
        if game is None:
            request = times.fetch({"job": "cron-all"}).items[0]
        else:
            request = times.fetch({"job": "cron-single"}).items[0]
    except:
        request = "ERROR - TIMESTAMP DB IS NOT WORKING"
    return request

@app.get("/")
def root(request: Request):
    return RedirectResponse("/docs")

@app.get("/sites.yaml")
def get_yaml(request: Request, background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the YAML format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}2.yaml".format(game))
    return StreamingResponse(res.iter_chunks(1024), media_type="application/yaml")
        
@app.get("/sites.json")
def get_json(request: Request, background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the JSON format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}2.yaml".format(game))
    return yaml.load(res.read(), Loader=yaml.FullLoader)
        
@app.get("/sites.txt", response_class=PlainTextResponse)
def get_txt(request: Request, background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the TXT format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}2.yaml".format(game))
    data = yaml.load(res.read(), Loader=yaml.FullLoader)
    txt = ""
    for item in data:
        if item["path"] != "/":
            path = item["path"]
        else:
            path = ""
        txt = txt + item["domain"] + path + "\n"
    return txt
    
@app.get("/hosts.txt", response_class=PlainTextResponse)
def get_hosts(request: Request, background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the HOSTS.TXT format.
    """
    
    background_tasks.add_task(statcounter)
    request = timestamps(game)
    if game is None: game = "sites"
    res = drive.get("{0}2.yaml".format(game))
    data = yaml.load(res.read(), Loader=yaml.FullLoader)
    with open("templates/hosts.txt", "r") as f:
        hosts = f.read().format(str(request["updated"]))
    hosts = hosts + "\n \n"
    wwwhosts = ""
    for item in data:
        if item["path"] == "/":
            hosts = hosts  + "0.0.0.0 " + item["domain"] + "\n" 
            wwwhosts = wwwhosts + "0.0.0.0 " + "www." + item["domain"] + "\n" 
    hosts = hosts + wwwhosts + "\n" + "# === End of StopModReposts site list ==="
    return hosts

@app.get("/ublacklist",response_class=PlainTextResponse)
def get_ublacklist(request: Request, background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the uBlacklist format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}2.yaml".format(game))
    data = yaml.load(res.read(), Loader=yaml.FullLoader)
    blacklist = ""
    for item in data:
        if item["path"] != "/":
            path = item["path"] + "/*"
        else:
            path = "/*"
        blacklist = blacklist + "*://*." + item["domain"] + path + "\n"
    return blacklist

@app.get("/sites.xml")
def get_xml(request: Request, background_tasks: BackgroundTasks, game: Optional[str] = None):
    """
    Get the combined list in the XML format.
    """
    
    background_tasks.add_task(statcounter)
    if game is None: game = "sites"
    res = drive.get("{0}2.yaml".format(game))
    data = yaml.load(res.read(), Loader=yaml.FullLoader)
    sites = objectify.Element("sites", nsmap='', _pytype='')

    for item in data:
        site = objectify.Element("site", nsmap='', _pytype='')
        site.domain = item["domain"]
        site.notes = item["notes"]
        site.path = item["path"]
        site.reason = item["reason"]

        sites.append(site)
    
    objectify.deannotate(sites)
    etree.cleanup_namespaces(sites)
    return Response(content=etree.tostring(sites, pretty_print=True, xml_declaration=True, with_tail=False), media_type="application/xml")

@app.get("/sites.nbt")
def get_nbt(request: Request, background_tasks: BackgroundTasks):
    """
    Get the combined list in the NBT format **(deprecated - will be removed soon)**.
    """
    
    background_tasks.add_task(statcounter)
    raise HTTPException(status_code=400, detail="This format is deprecated. Please use a different one: https://github.com/StopModReposts/Illegal-Mod-Sites/wiki/API-access-and-formats")
    
@app.get("/stats")
def get_stats(request: Request):
    """
    Get the API and refresh stats.
    """
    
    month = str(datetime.now().month)
    counter = stats.fetch({"month": month}).items[0]["total"]
    cronall = times.fetch({"job": "cron-all"}).items[0]["updated"]
    cronsingle = times.fetch({"job": "cron-single"}).items[0]["updated"]
    
    return {"requests_this_month": counter,
            "latest_cron_refresh": {
                "cron-all": cronall,
                "cron-single": cronsingle
            }}
    
@app.get("/shields/{shield}")
def get_shields(request: Request, shield: str):
    """
    Get the data needed to generate a shield.
    """
    
    if shield == "total":
        sites = 0
        res = drive.get("sites.yaml")
        data = yaml.load(res.read(), Loader=yaml.FullLoader)
        sites = len(data)
        return {"schemaVersion": 1,
                "label": "sites",
                "message": str(sites),
                "color": "blue"}
    elif shield == "refreshed":
        time = times.fetch({"job": "cron-all"}).items[0]["updated"]
        return {"schemaVersion": 1,
                "label": "refreshed",
                "message": str(time) + " UTC",
                "color": "blue"}
    elif shield == "visits":
        month = str(datetime.now().month)
        visits = stats.fetch({"month": month}).items[0]["total"]
        return {"schemaVersion": 1,
                "label": "visits this month",
                "message": str(visits),
                "color": "blue"}

#if __name__ == "__main__":
#    uvicorn.run(app, host="localhost", port=80)