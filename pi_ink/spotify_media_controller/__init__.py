import requests
from spotipy.client import Spotify
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from io import BytesIO
import logging


__all__ = ["SpotifyMediaController"]


logger = logging.getLogger(__name__)


def darken_image(img, factor):
    # Create an enhancer object
    enhancer = ImageEnhance.Brightness(img)

    # Darken the image
    darkened_img = enhancer.enhance(factor)

    return darkened_img


class SpotifyMediaController:
    spotify_client: Spotify

    def __init__(self, spotify_client: Spotify):
        self.spotify_client = spotify_client

    def get_currently_playing(self):
        current = self.spotify_client.current_playback()
        if current is None:
            return None

        return {
            'artist': current['item']['artists'][0]['name'],
            'song': current['item']['name'],
            'album_cover': current['item']['album']['images'][0]['url'],
        }

    def construct_mockup_display(self):
        current = self.get_currently_playing()
        if current is None:
            return None

        im = Image.new("RGBA", (800, 480), (0, 0, 0, 255))

        # fetch album cover
        resp = requests.get(current['album_cover'])
        album_img = Image.open(BytesIO(resp.content))

        # make album img rgba
        album_img = album_img.convert("RGBA")

        # fit using the cover algorithm to 600 x 480 pixels
        album_splash = album_img.copy()
        album_cover = album_img.copy()

        def cover(dest, src, size, xy, shadow=False):
            src_w = src.width
            src_h = src.height

            target_w = size[0]
            target_h = size[1]

            src_ratio = src_h / src_w
            target_ratio = target_h / target_w

            if target_ratio > src_ratio:
                # target is wider than source
                # scale to target height
                final_height = target_h
                scale = target_h / src_h
                final_width = round(src_w * scale)
            else:
                final_width = target_w
                scale = target_w / src_w
                final_height = round(src_h * scale)

            logger.debug(f"cover final size calculated: {final_width}x{final_height}")
            src = src.resize((final_width, final_height))

            # crop to target size
            if shadow:
                src = src.crop((0, 0, target_w, target_h))
            else:
                src = src.crop((0, target_h/2, target_w, target_h + target_h/2))

            logger.debug(f"cover final size actual: {src.width}x{src.height}")
            dest.paste(src, xy, src)  # use src as mask to merge transparent image

        # # dim the album splash
        # album_splash = album_splash.convert("RGBA")
        # album_splash.putalpha(255 - int(255 * 0.25))

        # darken album splash
        album_splash = album_splash.convert("RGBA")
        album_splash = darken_image(album_splash, 0.55)

        cover(im, album_splash, (800, 480), (0, 0), False)

        # -25 = half of border height in shadow algo
        cover(im, album_cover, (380 - 75, 380 - 75), (int(800/2 - (380-75)/2), 25), True)

        # set font to Source Code Pro
        font_size = 38
        font = ImageFont.truetype("C:/Users/dylan/PycharmProjects/pi-ink/pi_ink/fonts/SourceCodePro-Black.ttf", font_size)

        # limit song and artist name to 33 characters
        max_len = 33
        if len(current['artist']) > max_len:
            current['artist'] = current['artist'][:max_len-3] + '...'

        if len(current['song']) > max_len:
            current['song'] = current['song'][:max_len-3] + '...'

        # draw artist name and song in bottom left corner in white text with a black shadow
        draw = ImageDraw.Draw(im)
        draw.text((20, 480-font_size-20), current['artist'], font=font, fill=(0, 0, 0, 255))
        draw.text((20, 480-font_size-25), current['artist'], font=font, fill=(255, 255, 255, 255))

        draw.text((20, 480-font_size-20-font_size-5), current['song'], font=font, fill=(0, 0, 0, 255))
        draw.text((20, 480-font_size-25-font_size-5), current['song'], font=font, fill=(255, 255, 255, 255))

        return im
