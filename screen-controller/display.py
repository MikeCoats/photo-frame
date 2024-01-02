"""Control the attached display.
"""
import asyncio
import re
from distutils.util import strtobool


async def get_power() -> bool:
    """Get the current power state of the display.

    True is returned if the display is turned on. False if the display is off.
    """
    proc = await asyncio.create_subprocess_shell(
        'xset -display :0 q | grep "Monitor is"',
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    value = strtobool(
        re.findall(r"^Monitor is ([a-zA-Z]+)$", stdout.decode().strip())[0]
    )

    return value == 1


async def set_power(power: bool = True):
    """Set the current power state of the display.

    A power value of True will turn the display on. A power value of False will
    turn off the display. If called without a power value, it will default to
    True, turning on the display.
    """
    await asyncio.create_subprocess_shell(
        "xset -display :0 dpms force " + ("on" if power else "off")
    )
    return


async def get_brightness() -> float:
    """Get the current brightness state of the display.

    Returns a float between 0.0 for full dark and 1.0 for full bright. A value
    greater than 1.0 is possible, but this means that "quite" bright pixels are
    being clipped on screen.
    """
    proc = await asyncio.create_subprocess_shell(
        'xrandr -display :0 --verbose | grep "Brightness: "',
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return float(
        re.findall(r"^Brightness: ([0-9]+\.[0-9]+)$", stdout.decode().strip())[0]
    )


async def set_brightness(brightness: float = 1.0):
    """Set the brightness value of the display.

    A brightness value of 0.0 is effectively dark enough to be comparable to
    off. A brightness value of 1.0 is as bright as the display can go. If
    called without a brightness value, it will default to 1.0, the full
    brightness available.
    """
    await asyncio.create_subprocess_shell(
        "xrandr -display :0 --output HDMI-1 --brightness " + str(brightness)
    )
    return
