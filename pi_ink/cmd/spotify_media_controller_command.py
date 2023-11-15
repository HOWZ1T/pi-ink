import logging
import os.path
import sys
import time
from os import environ

import click
import spotipy
import vyper
from pi_ink.spotify_media_controller import SpotifyMediaController
from tkinter import Tk, Label
from PIL import ImageTk


logger = logging.getLogger(__name__)
v = vyper.Vyper()


class LogFilter(logging.Filter):
    def filter(self, record):
        # determine which keys are extra based on base record keys
        base_keys = logging.LogRecord(
            "", logging.DEBUG, "", 0, "", None, None, ""
        ).__dict__.keys()
        extra_keys = [key for key in record.__dict__.keys() if key not in base_keys]

        if hasattr(record, "extra"):
            record.extra_ = record.extra
            extra_keys.append("extra_")

        record.extra = {}

        for key in extra_keys:
            record.extra[key] = record.__dict__[key]

        return True


def initialize_environment(
    config_path: str, config_name: str, default_scopes: str, debug: bool
):
    """
    Initializes the environment, including the logging and vyper setup, for the application.

    Args:
        config_path (str): path to config file
        config_name (str): name of config file (without extension)
        default_scopes (str): default scopes to use for spotify oauth
        debug (bool): whether or not to enable debug logging
    """

    # setup logging
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.addFilter(LogFilter())
    logging_handlers = [handler]
    if "PYCHARM_HOSTED" in environ or debug is True:
        logging.basicConfig(
            format="%(asctime)s | %(name)35s | %(funcName)35s() | %(levelname)8s | %(message)40s | extra=%(extra)s",
            datefmt="%b %d %H:%M:%S",
            level=logging.DEBUG,
            handlers=logging_handlers,
        )

        # disable spotipy debug logging
        logging.getLogger("spotipy").setLevel(logging.INFO)

        # disable urllib3 debug logging
        logging.getLogger("urllib3").setLevel(logging.INFO)
        logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)

        # disable vyper debug logging
        logging.getLogger("vyper").setLevel(logging.INFO)
        logging.getLogger("vyper.util").setLevel(logging.INFO)
    else:
        logging.basicConfig(
            format="%(asctime)s | %(name)60s | %(funcName)60s() | %(levelname)8s | %(message)s | extra=%(extra)s",
            datefmt="%b %d %H:%M:%S",
            level=logging.INFO,
            handlers=logging_handlers,
        )

    # setup vyper
    # remove file extension from config name
    if "." in config_name:
        config_name = config_name.split(".")[0]

    # make sure config path is absolute
    config_path = os.path.abspath(config_path)

    logging.info(
        "looking for config",
        extra={"config-path": config_path, "config-name": config_name},
    )

    # setup config from config file with vyper
    v.add_config_path(config_path)
    v.set_config_name(config_name)
    v.set_config_type("yaml")
    v.read_in_config()

    # set vyper defaults
    v.set_default("scope", default_scopes)


@click.command(name="spotify")
@click.argument("username")
@click.option("--config-path", "-c", default="./", help="path to config file")
@click.option(
    "--config-name",
    "-n",
    default="spotify-media-controller",
    help="name of config file",
)
@click.option(
    "--redirect-uri",
    "-r",
    default="http://localhost/spotify-redirect",
    help="redirect uri for spotify oauth",
)
@click.option("--debug", "-d", default=False, is_flag=True, help="enable debug logging")
def main(
    username: str, config_path: str, config_name: str, redirect_uri: str, debug: bool
):
    initialize_environment(
        config_path,
        config_name,
        "user-read-playback-state user-modify-playback-state user-read-currently-playing",
        debug,
    )

    client_id = v.get("client_id")
    client_secret = v.get("client_secret")

    assert client_id is not None, "client_id is required"
    assert client_secret is not None, "client_secret is required"

    # login to spotify using OAuth
    scope = v.get("scope")
    logger.info(f"logging in as {username}", extra={"scope": scope})
    logger.debug(
        "client details",
        extra={
            "client_id": f"{client_id[:-6]}******",
            "client_secret": f"{client_secret[:-6]}******",
        },
    )

    redirect_uri = (
        v.get("redirect_uri") if v.get("redirect_uri") is not None else redirect_uri
    )
    logger.info(f"redirect uri: {redirect_uri}")

    sp = spotipy.Spotify(
        auth_manager=spotipy.SpotifyOAuth(
            scope=scope,
            username=username,
            client_id=client_id,
            client_secret=client_secret,
            open_browser=False,
            redirect_uri=redirect_uri,
        )
    )

    app = SpotifyMediaController(sp)
    current = app.construct_mockup_display()

    # create a Tk window to display the image that changes every 40 seconds
    window = Tk()
    window.title("Spotify Media Controller")
    window.geometry("800x480")

    # create a label to display the image
    label = Label(window, image=ImageTk.PhotoImage(current))
    label.pack()

    def callback(e):
        current2 = app.construct_mockup_display()
        img2 = ImageTk.PhotoImage(current2)
        label.configure(image=img2)
        label.image = img2

    window.bind('<Return>', callback)
    window.mainloop()


if __name__ == "__main__":
    main()
