import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import RedirectResponse, StreamingResponse, PlainTextResponse
import air_telemetry as telemetry
from dotenv import load_dotenv
import os
from deta import Deta
from typing import Optional
import yaml
from datetime import date, datetime


"""
Responses:
- yaml [DONE]
- txt [DONE]
- json [DONE]
- xml
- hosts.txt
- ublacklist
- nbt
"""


load_dotenv()
TELEMETRY_TOKEN = os.getenv("TELEMETRY_TOKEN")
DETA_TOKEN = os.getenv("DETA_TOKEN")
lists = ["minecraft.yaml", "stardewvalley.yaml", "subnautica.yaml"]

app = FastAPI()
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

@app.get("/sites.yaml")
def get_yaml(background_tasks: BackgroundTasks, game: Optional[str] = None):
    background_tasks.add_task(statcounter)
    if game is None:
        try:
            res = drive.get("minecraft.yaml")
            return StreamingResponse(res.iter_chunks(1024), media_type="application/yaml")
        except AttributeError:
            return {"msg": "Error - No file available"}
    else:
        try:
            res = drive.get("{0}.yaml".format(game))
            return StreamingResponse(res.iter_chunks(1024), media_type="application/yaml")
        except AttributeError:
            return {"msg": "Error - No file available"}
        
@app.get("/sites.json")
def get_json(background_tasks: BackgroundTasks, game: Optional[str] = None):
    background_tasks.add_task(statcounter)
    if game is None:
        res = drive.get("minecraft.yaml")
        return yaml.load(res.read(), Loader=yaml.FullLoader)
    else:
        res = drive.get("{0}.yaml".format(game))
        return yaml.load(res.read(), Loader=yaml.FullLoader)
        
@app.get("/sites.txt", response_class=PlainTextResponse)
def get_txt(background_tasks: BackgroundTasks, game: Optional[str] = None):
    background_tasks.add_task(statcounter)
    if game is None:
        res = drive.get("minecraft.yaml")
        data = yaml.load(res.read(), Loader=yaml.FullLoader)
        txt = ""
        for item in data:
            txt = txt + item["domain"] + "\n"
        return txt
    else:
        res = drive.get("{0}.yaml".format(game))
        data = yaml.load(res.read(), Loader=yaml.FullLoader)
        txt = ""
        for item in data:
            txt = txt + item["domain"] + "\n"
        return txt


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=80)