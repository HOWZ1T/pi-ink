from .iapp import IApp
from .pictureframe import PictureFrame
from .spotipi import SpotiPi

__all__ = ["IApp", "SpotiPi", "PictureFrame"]


def app_factory(app_name: str, **kwargs) -> IApp:
    """
    Factory method for creating an app.

    Args:
        app_name (str): name of the app to create
        **kwargs: keyword arguments to pass to the app

    Returns:
        IApp: the app instance
    """
    app_name_copy = app_name.lower()
    if app_name_copy == "spotipi":
        return SpotiPi(**kwargs)
    elif app_name_copy == "pictureframe":
        return PictureFrame(**kwargs)
    else:
        raise ValueError(f"invalid app name: {app_name_copy}")
