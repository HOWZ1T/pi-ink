import logging
import os
import tempfile
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from pi_ink.spotify import Spotify
from pi_ink.spotify.models import Track

from .irenderer import IRenderer

logger = logging.getLogger(__name__)


class ImageRenderer(IRenderer):
    _font_path: str
    _heart_outline_white_512px: Image
    _heart_solid_white_512px: Image
    _drop_shadow_300px: Image

    def __init__(self):
        self._font_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "assets",
                "fonts",
                "SourceCodePro-Black.ttf",
            )
        )
        self._drop_shadow_300px = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "assets",
                "spotify_300px_drop_shadow_x_7.png",
            )
        )
        self._heart_outline_white_512px = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "assets", "heart_outline_white_512.png"
            )
        )
        self._heart_solid_white_512px = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "assets", "heart_solid_white_512.png"
            )
        )

        # read in RGBA image assets
        self._drop_shadow_300px = Image.open(self._drop_shadow_300px).convert("RGBA")
        self._heart_outline_white_512px = Image.open(
            self._heart_outline_white_512px
        ).convert("RGBA")
        self._heart_solid_white_512px = Image.open(
            self._heart_solid_white_512px
        ).convert("RGBA")

    def __draw_bg_and_album_cover_art(self, track: Track, frame_img: Image) -> None:
        """
        Draws the background and album cover art onto the frame image.

        Args:
            track (Track): track to draw bg and album cover art for.
            frame_img (Image): frame image to draw bg and album cover art onto.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # download 300px and 640px album art
            album_cover_300px_fp = os.path.join(temp_dir, "album_cover_300px.jpg")
            album_cover_640px_fp = os.path.join(temp_dir, "album_cover_640px.jpg")

            logger.info(
                f"downloading album cover 300px from {track.album_cover_url_300px}"
            )
            resp = requests.get(track.album_cover_url_300px, allow_redirects=True)
            with open(album_cover_300px_fp, "wb") as f:
                f.write(resp.content)
            logger.info(f"saved album cover 300px to {album_cover_300px_fp}")

            logger.info(
                f"downloading album cover 640px from {track.album_cover_url_640px}"
            )
            resp = requests.get(track.album_cover_url_640px, allow_redirects=True)
            with open(album_cover_640px_fp, "wb") as f:
                f.write(resp.content)
            logger.info(f"saved album cover 640px to {album_cover_640px_fp}")

            # open album cover images
            album_cover_300px_img = Image.open(album_cover_300px_fp)
            album_cover_640px_img = Image.open(album_cover_640px_fp)

            # background album cover 640px, offsets to center:
            #   x: (600 - 640) / 2 = -20
            #   y: (448 - 640) / 2 = -96

            # gaussian blur background album cover 640px
            bg = album_cover_640px_img.filter(ImageFilter.GaussianBlur(radius=2.5))

            # darken background
            bg = bg.point(lambda p: p * 0.7)

            # draw bg centered on frame_img
            frame_img.paste(bg, (-20, -96))

            # paste drop shadow
            # 7 px comes from the drop shadow image width being 14px larger

            # get portion of background covered by drop shadow
            bg_drop_shadow = bg.crop(
                (20 + 150 - 7, 96 + 25, 20 + 150 - 7 + 300 + 14, 96 + 25 + 311)
            )

            # make sure bg_drop_shadow is RGBA
            bg_drop_shadow = bg_drop_shadow.convert("RGBA")

            # alpha composite drop shadow onto bg portion it covers
            shadow = Image.alpha_composite(bg_drop_shadow, self._drop_shadow_300px)

            # finally paste the shadow with the bg information preserved
            frame_img.paste(shadow, (150 - 7, 25))

            # draw album cover 300px centered on frame_img horizontally and 25 px from the top
            frame_img.paste(album_cover_300px_img, (150, 25))

    def __draw_info(
        self, track: Track, frame_img: Image, left_margin: int, text_anchor_y: int
    ) -> None:
        target_font_size = 25

        def trunc_str(s: str, max_len: int = 40, trunc_chars: str = "...") -> str:
            # helper function to truncate strings
            trunc_str_len = len(trunc_chars)
            if len(s) > max_len:
                return s[: max_len - trunc_str_len] + trunc_chars
            return s

        title = trunc_str(track.title, max_len=50)
        album = trunc_str(track.album, max_len=50)
        artist = trunc_str(track.artist, max_len=50)

        def __get_title_font(font_size: int):
            # helper function to get the size of the title font whilst allowing for down scaling
            parent_font = ImageFont.truetype(self._font_path, font_size)

            # get width of text
            title_width = parent_font.getlength(title)

            if title_width > 600 - (left_margin * 2):
                # title is too long, scale down font size
                return __get_title_font(font_size - 1)

            return parent_font, font_size, title_width

        title_font, used_font_size, title_width = __get_title_font(target_font_size)
        subtitle_font = ImageFont.truetype(self._font_path, int(used_font_size * 0.75))
        logger.debug(
            "font and text sizes",
            extra={
                "title_font_size": used_font_size,
                "title chars": len(title),
                "subtitle_font_size": subtitle_font.size,
                "album chars": len(album),
                "artist chars": len(artist),
            },
        )

        # start drawing info
        draw = ImageDraw.Draw(frame_img)

        def __text_with_shadow(
            text, ts_font, ts_font_size, tx, ty, strength, blur_radius
        ):
            text_width = ts_font.getlength(text)
            canvas_margin = 60
            canvas_half_margin = int(canvas_margin / 2)
            canvas_quarter_margin = int(canvas_margin / 4)

            # adjust to draw text where we actually intended at for ty, tx is unaffected
            ty += canvas_quarter_margin

            # draw text shadow
            txt_shadow_img = Image.new(
                "RGBA",
                (int(text_width + canvas_margin), int(ts_font_size + canvas_margin)),
                (0, 0, 0, 0),
            )
            txt_shadow_draw = ImageDraw.Draw(txt_shadow_img)
            txt_shadow_draw.text(
                (
                    canvas_half_margin,
                    int(
                        txt_shadow_img.height / 2
                        - ts_font_size / 2
                        - canvas_quarter_margin
                    ),
                ),
                text,
                font=ts_font,
                fill=(0, 0, 0, 255),
                stroke_width=strength,
                stroke_fill=(0, 0, 0, 255),
            )
            txt_shadow_img = txt_shadow_img.filter(
                ImageFilter.GaussianBlur(radius=blur_radius)
            )
            txt_shadow_draw = ImageDraw.Draw(txt_shadow_img)

            # draw clean text onto of shadow
            txt_shadow_draw.text(
                (
                    canvas_half_margin,
                    int(
                        txt_shadow_img.height / 2
                        - ts_font_size / 2
                        - canvas_quarter_margin
                    ),
                ),
                text,
                font=ts_font,
                fill=(255, 255, 255, 255),
            )

            # get portion of frame_img being drawn over
            frame_img_portion = frame_img.crop(
                (
                    tx - canvas_half_margin,
                    ty - canvas_half_margin,
                    tx - canvas_half_margin + txt_shadow_img.width,
                    ty - canvas_half_margin + txt_shadow_img.height,
                )
            )

            # make sure frame_img_portion is RGBA
            frame_img_portion = frame_img_portion.convert("RGBA")

            # alpha composite text shadow onto frame_img_portion
            txt_shadow_img = Image.alpha_composite(frame_img_portion, txt_shadow_img)
            frame_img.paste(
                txt_shadow_img, (tx - canvas_half_margin, ty - canvas_half_margin)
            )

        # draw info text with text shadow
        __text_with_shadow(
            artist,
            subtitle_font,
            subtitle_font.size,
            left_margin,
            text_anchor_y + used_font_size + 5 + subtitle_font.size + 5,
            3,
            6,
        )
        __text_with_shadow(
            album,
            subtitle_font,
            subtitle_font.size,
            left_margin,
            text_anchor_y + used_font_size + 5,
            3,
            6,
        )
        __text_with_shadow(
            title, title_font, used_font_size, left_margin, text_anchor_y, 3, 6
        )

        def __text_with_hard_shadow(hs_text, hs_font, hs_font_size, hs_x, hs_y):
            # TODO: UNUSED, left for reference/future use
            # DEAD CODE
            # helper function to draw text with a hard shadow
            draw.text(
                (hs_x, hs_y + 2.5),
                hs_text,
                font=hs_font,
                fill=(0, 0, 0, 255),
            )
            draw.text(
                (hs_x, hs_y),
                hs_text,
                font=hs_font,
                fill=(255, 255, 255, 255),
            )

    def __draw_is_loved(self, track: Track, frame_img: Image) -> None:
        if not track.is_loved:
            return

        # get spotify green copy of heart image
        heart = self._heart_solid_white_512px.copy()

        # resize heart to 50px
        heart = heart.resize((50, 50))

        # make heart spotify green #1DB954
        # https://developer.spotify.com/documentation/design#using-our-colors
        spotify_green_rgb = (30, 215, 96)
        heart_data = list(
            map(
                lambda p: (
                    spotify_green_rgb[0],
                    spotify_green_rgb[1],
                    spotify_green_rgb[2],
                    p[3],
                )
                if p[3] > 0
                else p,
                heart.getdata(),
            )
        )
        heart.putdata(heart_data)

        # make black copy
        heart_shadow_diff = 10
        heart_shadow_diff_half = int(heart_shadow_diff / 2)
        heart_black = heart.copy()
        heart_black = heart_black.resize(
            (heart.width + heart_shadow_diff, heart.height + heart_shadow_diff)
        )
        heart_black_data = list(
            map(lambda p: (0, 0, 0, p[3]) if p[3] > 0 else p, heart_black.getdata())
        )
        heart_black.putdata(heart_black_data)

        # make bigger image for shadow
        shadow_margin = 40
        shadow_half_margin = int(shadow_margin / 2)
        heart_shadow = Image.new(
            "RGBA",
            (heart_black.width + shadow_margin, heart_black.height + shadow_margin),
            (0, 0, 0, 0),
        )

        # draw black heart onto shadow
        heart_shadow.paste(
            heart_black, (int(shadow_margin / 2), int(shadow_margin / 2)), heart_black
        )

        # blur shadow
        heart_shadow = heart_shadow.filter(ImageFilter.GaussianBlur(radius=8))

        # paste clean heart on top
        heart_shadow.paste(
            heart,
            (
                int(shadow_margin / 2) + heart_shadow_diff_half,
                int(shadow_margin / 2) + heart_shadow_diff_half,
            ),
            heart,
        )

        # target top left corner of heart_shadow to place over cover art
        dest_x = 150 + 300 - heart_shadow.width - 5 - 4 + shadow_half_margin
        dest_y = 325 - heart_shadow.height - 5 + shadow_half_margin

        # get portion of frame covered by heart_shadow
        frame_img_portion = frame_img.crop(
            (dest_x, dest_y, dest_x + heart_shadow.width, dest_y + heart_shadow.height)
        )

        # make sure frame_img_portion is RGBA
        frame_img_portion = frame_img_portion.convert("RGBA")

        # alpha composite heart_shadow onto frame_img_portion
        heart_shadow = Image.alpha_composite(frame_img_portion, heart_shadow)

        # finally paste the shadow with the bg information preserved
        frame_img.paste(heart_shadow, (dest_x, dest_y))

    def render_frame_from_track(self, track: Track) -> Image:
        frame_img = Image.new("RGBA", (600, 448), (255, 255, 255, 255))
        self.__draw_bg_and_album_cover_art(track, frame_img)
        self.__draw_is_loved(track, frame_img)
        self.__draw_info(track, frame_img, left_margin=25, text_anchor_y=(25 * 2) + 300)
        return frame_img

    def render_frame(self, spotify: Spotify) -> Any:
        # either get the current playing track or the last played track
        track = spotify.get_currently_playing()
        if track is None:
            track = spotify.get_last_played(limit=1)[0]

        # TODO photo frame mode of last 50 played tracks if no track has been played in the last 15 minutes
        # this (photo frame) functionality should be in the driver (cmd/spotify_media_controller_command.py)
        return self.render_frame_from_track(track), track
