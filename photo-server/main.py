import asyncio
import configparser
import random
from os import listdir
from os.path import isfile, join

import uvicorn
import xdg.BaseDirectory
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Load the config containing our cache and output directories.
config_file = join(xdg.BaseDirectory.load_first_config("photo-server"), "config")
config = configparser.ConfigParser()
config.read(config_file)
root = config["photo-server"].get("root")

# Set up a FastAPI app and attach all of our routes.
app = FastAPI()
app.mount("/photos", StaticFiles(directory=root), name="photos")
templates = Jinja2Templates(directory=".")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # List out all of the photos we have. We do this on every request as the
    # list might have changed during run-time. Grab a random photo from the
    # list.
    resized_images = [
        f for f in listdir(root) if isfile(join(root, f)) and f.endswith(".jpg")
    ]
    photo = random.choice(resized_images)

    # Without a background colour, there's a chance that we might see a
    # full-white screen until the browser loads and renders the photograph.
    # Using a pre-computed average colour reduces the "feel" of the pop-in.
    rgb_file = join(root, photo + ".rgb")
    with open(rgb_file, "r") as fp:
        rgb = fp.read()

    # Saving our photos as "progressive" JPEGs should allow them to render in
    # gradually but our SBC is so underpowered that we still suffer from
    # pop-in. By using an EXTREMELY low res backound image, we allow the
    # underpowered computer's browser to transition from solid colour to full
    # photo via a reasonable fake "first step" on the progressive loader.
    lowres_file = join(root, photo + ".lowres")

    # We append ?cacheBuster=63928387 to the end of all URL calls to make sure
    # we always return here rather than accidentally letting the browser serve
    # the same photo again and again.
    rnd = random.randrange(10000000, 99999999)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "photo": join("/photos", photo),
            "lowres": lowres_file,
            "rgb": rgb,
            "cacheBuster": rnd,
        },
    )


async def main():
    # When the file is run directly, hook up a uvicorn server to host the app.
    config = uvicorn.Config("main:app", host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
