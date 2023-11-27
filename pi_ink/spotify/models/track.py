from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Self


@dataclass(frozen=True)
class Track:
    title: str
    album: str
    album_cover_url_300px: Optional[str]
    album_cover_url_640px: Optional[str]
    artist: str
    played_at: datetime
    is_loved: Optional[bool]

    @classmethod
    def construct_track_from_last_played(
        cls,
        is_loved_fn: Callable[[Any], List[bool]],
        last_played: Dict[str, Any],
        item_index: int = 0,
    ) -> Self:
        """
        Constructs a track from the last played response from Spotify API.

        Args:
            is_loved_fn (Callable[[Any], bool]): function that for a given list of tracks, returns a list of booleans indicating if it is loved or not
            last_played (Dict[str, Any]): last played response from Spotify API
            item_index (int, optional):
                index of the item in the last played response, if the index is invalid,
                the default will be used. Defaults to 0.

        Returns:
            Track: track constructed from the last played response
        """
        # TODO a lot of the destructing is similiar to the response from currently playing
        # TODO refactor
        idx = (
            0
            if (len(last_played["items"]) <= item_index or item_index < 0)
            else item_index
        )
        itm = last_played["items"][idx]
        played_at = datetime.strptime(itm["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        track_json = itm["track"]
        album_json = track_json["album"]
        artists_json = track_json["artists"]
        title = track_json["name"]
        album = album_json["name"]

        # get the album image
        album_cover_url_300px = None
        album_cover_url_640px = None
        for img in album_json["images"]:
            if img["height"] == 300:
                album_cover_url_300px = img["url"]
                continue

            if img["height"] == 640:
                album_cover_url_640px = img["url"]
                continue

        first_artist = artists_json[0]["name"]
        feat_artists = []
        if len(artists_json) > 1:
            for artist_json in artists_json[1:]:
                feat_artists.append(artist_json["name"])

        artist = first_artist
        if len(feat_artists) > 0:
            artist += f" (feat. {', '.join(feat_artists)})"

        is_loved = None
        track_id = track_json["id"]
        if track_id is not None:
            is_loved = is_loved_fn(track_id)[0]

        return cls(
            title=title,
            album=album,
            album_cover_url_300px=album_cover_url_300px,
            album_cover_url_640px=album_cover_url_640px,
            artist=artist,
            played_at=played_at,
            is_loved=is_loved,
        )

    @classmethod
    def construct_song_from_currently_playing(
        cls, is_loved_fn: Callable[[Any], List[bool]], currently_playing: Dict[str, Any]
    ) -> Self:
        """
        Constructs a track from the currently playing response from Spotify API.

        Args:
            is_loved_fn (Callable[[Any], List[bool]): function that for a given list of tracks, returns a list of booleans indicating if it is loved or not
            currently_playing (Dict[str, Any]): currently playing response from Spotify API

        Returns:
            Track: track constructed from the currently playing response
        """
        # TODO a lot of the destructing is similiar to the response from last played
        # TODO refactor
        itm = currently_playing["item"]

        timestamp = currently_playing["timestamp"]
        track_progress = currently_playing["progress_ms"]

        # fromtimestamp expects timestamp in seconds not milliseconds, thereby divide by 1000 to convert to seconds
        played_at = datetime.fromtimestamp((timestamp - track_progress) / 1000)
        album_json = itm["album"]
        artists_json = itm["artists"]
        title = itm["name"]
        album = album_json["name"]

        # get the album image
        album_cover_url_300px = None
        album_cover_url_640px = None
        for img in album_json["images"]:
            if img["height"] == 300:
                album_cover_url_300px = img["url"]
                continue

            if img["height"] == 640:
                album_cover_url_640px = img["url"]
                continue

        first_artist = artists_json[0]["name"]
        feat_artists = []
        if len(artists_json) > 1:
            for artist_json in artists_json[1:]:
                feat_artists.append(artist_json["name"])

        artist = first_artist
        if len(feat_artists) > 0:
            artist += f" (feat. {', '.join(feat_artists)})"

        is_loved = None
        track_id = itm["id"]
        if track_id is not None:
            is_loved = is_loved_fn(track_id)[0]

        return cls(
            title=title,
            album=album,
            album_cover_url_300px=album_cover_url_300px,
            album_cover_url_640px=album_cover_url_640px,
            artist=artist,
            played_at=played_at,
            is_loved=is_loved,
        )
