import asyncio
import importlib
import itertools
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

import nltk

from piwrite.editor import Editor

HOST = os.getenv("PIWRITE_HOST", "127.0.0.1")
DEBUG = os.getenv("PIWRITE_DEBUG", "False") == "True"
INFO = os.getenv("PIWRITE_INFO", "False") == "True"
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


v = None
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
        for _key_press in itertools.chain(inp.read_keys(), inp.flush_keys()):
            key.set()
            key_press = _key_press

    with inp.raw_mode():
        with inp.attach(keys_ready):
            while True:
                await key.wait()
                logger.debug(key_press)
                v.dispatch(key_press)
                await sio.emit("buffer", {"data": v.get()})
                if v.refresh:
                    logger.info("Sending a full refresh")
                    for field, val in update_only_map.items():
                        await sio.emit(field, {"data": val["exec"]()})
                    v.refresh = False
                logger.info(f"Updating {len(v.updating_fields)} fields")
                for field in v.updating_fields:
                    new_val = update_only_map[field]["exec"]()
                    await sio.emit(field, {"data": new_val})
                v.updating_fields.clear()
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
    logger.warning(f"Server started at '{HOST}:{PORT}'")
    await the_loop()
    await asyncio.Event().wait()


def start():
    global v
    configure_logger()
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    elif INFO:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        logger.warning("Punkt not available")
        try:
            # This means you need to run it at least
            # once without access point mode
            nltk.download("punkt")
        except:
            pass
    v = Editor(skip_config=False)
    asyncio.run(main())


if __name__ == "__main__":
    start()
