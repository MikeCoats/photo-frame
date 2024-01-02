"""Control the screen.
"""

import asyncio
import json
from contextlib import asynccontextmanager
from distutils.util import strtobool

import uvicorn
from fastapi import FastAPI

import display


async def read_saved_state():
    """Load the brightness value and power state from disk."""
    try:
        with open("saved_state.json", "r") as fp:
            return json.load(fp)
    except:
        return {"brightness": 1.0, "power": True}


async def write_saved_state(brightness: float, power: bool):
    """Save the brightness value and power state to disk."""
    with open("saved_state.json", "w") as fp:
        json.dump({"brightness": brightness, "power": power}, fp)
    return


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Load any presaved values from disk on start-up and save the
    current values to disk on shut-down.
    """
    # Startup  actions
    startup_state = await read_saved_state()
    await display.set_brightness(startup_state["brightness"])
    await display.set_power(startup_state["power"])

    # Run the app
    yield

    # Shutdown actions
    shutdown_brightness = await display.get_brightness()
    shutdown_power = await display.get_power()
    await write_saved_state(shutdown_brightness, shutdown_power)


app = FastAPI(lifespan=lifespan)


@app.get("/power")
async def get_power_handler():
    """Return the current power state to the REST client."""
    state = await display.get_power()
    return {"state": state}


@app.put("/power")
async def set_power_handler(state: str = "True"):
    """Set a new power state, supplied by the REST client."""
    new_power = strtobool(state) == 1
    await display.set_power(new_power)
    return await get_power_handler()


@app.get("/brightness")
async def get_brightness_handler():
    """Return the current brightness value to the REST client."""
    value = await display.get_brightness()
    return {"value": value}


@app.put("/brightness")
async def set_brightness_handler(value: float = 1.0):
    """Set a new brightness value, supplied by the REST client."""
    await display.set_brightness(value)
    return await get_brightness_handler()


async def main():
    """When the module is run directly, hook up a uvicorn server and
    host the app.
    """
    config = uvicorn.Config("main:app", host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
