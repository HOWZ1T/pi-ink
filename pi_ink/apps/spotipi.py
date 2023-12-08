import logging
import time

from pi_ink.apps.iapp import IApp
from pi_ink.displays import EDisplayResponse, InkyImpressionDisplay
from pi_ink.renderers import ImageRenderer
from pi_ink.spotify import Spotify

logger = logging.getLogger(__name__)


class SpotiPi(IApp):
    def run(self, **kwargs):
        spotify = Spotify.instance()
        img_renderer = ImageRenderer()
        display = InkyImpressionDisplay()
        spotify_poll_interval = 15  # in seconds
        t0 = time.time()
        do_update = True

        def get_track():
            inner_track = spotify.get_currently_playing()
            if inner_track is None:
                inner_track = spotify.get_last_played(limit=1)[0]
            return inner_track

        track = get_track()
        new_track = track

        while True:
            t1 = time.time()
            if t1 - t0 >= spotify_poll_interval:
                logger.info(f"polling spotify & updating frame")
                new_track = get_track()
                t0 = time.time()  # not setting to t1 since render_frame takes time

            if new_track is not None and new_track.title.lower() != track.title.lower():
                do_update = True

            if not do_update:
                continue

            logger.info(f"new track detected, updating frame")
            frame = img_renderer.render_frame_from_track(new_track)
            display.set_frame(frame)
            res = display.display_frame()

            if res.response == EDisplayResponse.ERROR:
                logger.error(f"error displaying frame: {res.value}")
                break

            if res.response == EDisplayResponse.NOT_READY:
                logger.info(f"display not ready, waiting {res.value}s")
                time.sleep(res.value)
                continue

            do_update = False
            track = new_track
            new_track = None
