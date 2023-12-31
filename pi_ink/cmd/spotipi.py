import logging
import sys
import time
from os import environ
from pathlib import Path

import click

from pi_ink.apps import app_factory
from pi_ink.config import Config

logger = logging.getLogger(__name__)


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
    username: str, redirect_uri: str, config_path: str, default_scopes: str, debug: bool
):
    """
    Initializes the environment, including the logging and vyper setup, for the application.

    Args:
        username (str): spotify username
        redirect_uri (str): redirect uri for spotify oauth
        config_path (str): path to config file
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

        # disable PIL debug logging
        logging.getLogger("PIL.PngImagePlugin").setLevel(logging.INFO)
    else:
        logging.basicConfig(
            format="%(asctime)s | %(name)60s | %(funcName)60s() | %(levelname)8s | %(message)s | extra=%(extra)s",
            datefmt="%b %d %H:%M:%S",
            level=logging.INFO,
            handlers=logging_handlers,
        )

    # setup config
    # make sure config path is absolute
    config_path = str(Path(config_path).resolve())
    conf = Config.instance()
    conf.read_config(config_path)

    # setup environment variables coming from cli args
    conf.set("username", username)

    if (
        redirect_uri is not None
    ):  # will override redirect uri from config file with uri from cli arg (if given)
        conf.set("redirect_uri", redirect_uri)

    if conf.get("scope") is None:
        # sets scope to defaults if no scope is given from the config file
        conf.set("scope", default_scopes)

    logging.info(f"environment initialized")


@click.command(name="spotify")
@click.argument("username")
@click.option("--config-path", "-c", help="path to config file")
@click.option(
    "--redirect-uri",
    "-r",
    default="http://localhost/spotify-redirect",
    help="redirect uri for spotify oauth",
)
@click.option("--debug", "-d", default=False, is_flag=True, help="enable debug logging")
@click.option("--app-name", "-a", default="spotipi", help="name of app to run")
@click.option("--saturation", "-s", default=0.5, help="saturation of display")
@click.option(
    "--dynamic-saturation", "-ds", default=False, help="enable dynamic saturation"
)
def main(
    username: str,
    config_path: str,
    redirect_uri: str,
    debug: bool,
    app_name: str,
    saturation: float,
    dynamic_saturation: bool,
):
    initialize_environment(
        username,
        redirect_uri,
        config_path,
        "user-read-playback-state user-read-currently-playing user-read-recently-played",
        debug,
    )

    app = app_factory(app_name)
    app.run(saturation=saturation, dynamic_saturation=dynamic_saturation)


if __name__ == "__main__":
    main()
