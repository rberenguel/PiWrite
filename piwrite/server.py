import asyncio
import importlib
import logging
import os

try:
    import importlib.resources as pkg_resources
except ImportError:
    # I shouldn't have to do this
    import importlib_resources as pkg_resources

import aiohttp.web
import socketio
from colorlog import ColoredFormatter
from prompt_toolkit.input import create_input
from prompt_toolkit.keys import Keys

logger = logging.getLogger("piwrite")

from piwrite.editor import Editor

import nltk

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    print("Punkt not available")
    try:
        # This means you need to run it at least
        # once without access point mode
        nltk.download("punkt")
    except:
        pass

HOST = os.getenv("PIWRITE_HOST", "127.0.0.1")
DEBUG = os.getenv("PIWRITE_DEBUG", "False") == "True"
PORT = int(os.getenv("PIWRITE_PORT", 80))

STATIC_FOLDER = pkg_resources.files("piwrite") / "static"


def configure_logger():
    """Fancy logging is nicer"""
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)s - %(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            "DEBUG": "yellow",
            "INFO": "cyan",
            "WARNING": "purple",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={},
        style="%",
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def staticHandle(file):
    async def handler(request):
        return aiohttp.web.FileResponse(file)

    return handler


v = Editor()

sio = socketio.AsyncServer(logger=False, engineio_logger=False, async_mode="aiohttp")


def init_map():
    update_only_map = {
        "saved": {"sent": False, "old": None, "exec": lambda: v.saved},
        "completions": {
            "sent": False,
            "old": None,
            "exec": lambda: v.completions_markdownified,
        },
        "mode": {"sent": False, "old": None, "exec": lambda: v.mode()},
        "err": {"sent": False, "old": None, "exec": lambda: v.err},
        "filename": {"sent": False, "old": None, "exec": lambda: v.filename},
        "command": {"sent": False, "old": None, "exec": lambda: v.command()},
        "modal": {"sent": False, "old": None, "exec": lambda: v.modal},
        "visual": {"sent": False, "old": None, "exec": lambda: v.visual},
        "status": {"sent": False, "old": None, "exec": lambda: v.status},
        "font": {"sent": False, "old": None, "exec": lambda: v.font},
        "fontsize": {"sent": False, "old": None, "exec": lambda: v.fontsize},
        "rot": {"sent": False, "old": None, "exec": lambda: v.rot},
        "dot": {"sent": False, "old": None, "exec": lambda: v.dot},
    }
    return update_only_map


async def the_loop():
    key = asyncio.Event()
    key_press = None
    done = asyncio.Event()
    inp = create_input()

    update_only_map = init_map()
    update_only_fields = list(update_only_map.keys())

    def keys_ready():
        nonlocal key_press
        for _key_press in inp.read_keys():
            key.set()
            key_press = _key_press
            if key_press.key == Keys.ControlC:
                done.set()

    with inp.raw_mode():
        with inp.attach(keys_ready):
            while True:
                await key.wait()
                logger.debug(key_press)
                v.dispatch(key_press)
                await sio.emit("buffer", {"data": v.get()})
                if v.refresh:
                    logger.info("Sending a full refresh")
                    for field, val in update_only_fields.items():
                        val["sent"] = False
                    v.refresh = False
                for field in update_only_fields:
                    # I was having issues in different versions of Python
                    # Not sure if because of globals, or editing the dict
                    # while traversing, so… ugly works here
                    new_val = update_only_map[field]["exec"]()
                    old_val = update_only_map[field]["old"]
                    sent = update_only_map[field]["sent"]
                    if new_val != old_val or not sent:
                        update_only_map[field]["old"] = new_val
                        logger.info(f"Sending {field}")
                        await sio.emit(field, {"data": new_val})
                        update_only_map[field]["sent"] = True
                key.clear()


async def main():
    app = aiohttp.web.Application()
    app.router.add_route("GET", "/", staticHandle(STATIC_FOLDER / "index.html"))
    app.add_routes([aiohttp.web.static("/static", STATIC_FOLDER, show_index=False)])
    app.add_routes([aiohttp.web.static("/docs", v.docs, show_index=True)])
    sio.attach(app)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, host=HOST, port=PORT)
    await site.start()
    logger.info(f"Server started at '{HOST}:{PORT}'")
    await the_loop()
    await asyncio.Event().wait()


def start():
    configure_logger()
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    asyncio.run(main())


if __name__ == "__main__":
    start()
