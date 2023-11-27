import logging
from typing import List, Optional, Self

import spotipy
from spotipy.client import Spotify as SpotifyClient

from pi_ink.config import Config
from pi_ink.spotify.models import Track

logger = logging.getLogger(__name__)
conf = Config.instance()


class Spotify:
    _instance: Self = None
    client: SpotifyClient

    @classmethod
    def instance(cls):
        if cls._instance is not None:
            return cls._instance

        cls._instance = cls.__new__(cls)
        client_id = conf.get("client_id")
        client_secret = conf.get("client_secret")
        username = conf.get("username")
        redirect_uri = conf.get("redirect_uri")
        scope = conf.get("scope")

        if client_id is None:
            logger.error("client_id is required")
            raise EnvironmentError("client_id is required")

        if client_secret is None:
            logger.error("client_secret is required")
            raise EnvironmentError("client_secret is required")

        if username is None:
            logger.error("username is required")
            raise EnvironmentError("username is required")

        if redirect_uri is None:
            logger.error("redirect_uri is required")
            raise EnvironmentError("redirect_uri is required")

        if scope is None:
            logger.error("scope is required")
            raise EnvironmentError("scope is required")

        # login to spotify using OAuth
        logger.info(f"logging in as {username}", extra={"scope": scope})
        logger.debug(
            "client details",
            extra={
                "client_id": f"{client_id[:-6]}******",
                "client_secret": f"{client_secret[:-6]}******",
            },
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

        cls._instance.client = sp
        logging.info("spotify client created")
        return cls._instance

    def get_currently_playing(self) -> Optional[Track]:
        resp = self.client.current_playback()
        if resp is None:
            return None

        return Track.construct_song_from_currently_playing(self.is_track_saved, resp)

    def get_last_played(self, limit: int = 1) -> Optional[List[Track]]:
        """
        Gets the last played track from Spotify API.

        Args:
            limit (int, optional): number of tracks to get. Defaults to 1.

        Returns:
            Track: last played track
        """
        resp = self.client.current_user_recently_played(limit=limit)
        if resp is None:
            return None

        tracks = list(
            map(
                lambda idx: Track.construct_track_from_last_played(
                    self.is_track_saved, resp, idx
                ),
                range(len(resp["items"])),
            )
        )
        return tracks

    def is_track_saved(self, tracks) -> List[bool]:
        if (
            type(tracks) is not list
            and type(tracks) is not tuple
            and type(tracks) is not set
        ):
            tracks = [tracks]
        return self.client.current_user_saved_tracks_contains(tracks)
