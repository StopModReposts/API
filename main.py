import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, StreamingResponse, PlainTextResponse
import air_telemetry as telemetry
from dotenv import load_dotenv
import os
from deta import Deta
from typing import Optional
import yaml


"""
Responses:
- yaml [DONE]
- txt
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
db = deta.Base("formats")


@app.get("/")
def root():
    return RedirectResponse("https://stopmodreposts.org")

@app.get("/sites.yaml")
def get_yaml(game: Optional[str] = None):
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
def get_json(game: Optional[str] = None):
    if game is None:
        res = drive.get("minecraft.yaml")
        return yaml.load(res.read(), Loader=yaml.FullLoader)
    else:
        res = drive.get("{0}.yaml".format(game))
        return yaml.load(res.read(), Loader=yaml.FullLoader)
        


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=80)