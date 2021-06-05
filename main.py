import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, StreamingResponse, PlainTextResponse
import air_telemetry as telemetry
from dotenv import load_dotenv
import os
from deta import Deta
from typing import Optional


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

@app.get("/sites.yaml", response_class=PlainTextResponse)
def yaml(game: Optional[str] = None):
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


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=80)