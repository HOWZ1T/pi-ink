import logging
from typing import Any, Dict, Self

from .loaders import __all__ as _loader_names
from .loaders.iconfig_loader import IConfigLoader

logger = logging.getLogger(__name__)


def _dyn_import(name: str):
    """
    Dynamically imports a module.
    Args:
        name (str): name of module to import

    Returns:
        module: imported module
    """
    components = name.split(".")
    mod = __import__(components[0])
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod


class Config:
    _kv_dict: Dict[str, Any] = {}
    _loaders: Dict[str, IConfigLoader] = {}
    _instance: Self = None

    def __init__(self):
        raise RuntimeError("Call instance() instead")

    @classmethod
    def instance(cls) -> Self:
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            for loader_name in _loader_names:
                loader = _dyn_import(f"pi_ink.config.loaders.{loader_name}")
                loader_instance = loader()
                for typ in loader_instance.get_type():
                    typ = typ.lower()
                    cls._instance._loaders[typ] = loader_instance
                    logger.info(f"registered config loader {loader} for type {typ}")
        return cls._instance

    def read_config(self, config_fp: str):
        """
        Reads in the config file and sets the values in the config store.

        Args:
            config_fp (str): path to config file
        """
        file_ext = config_fp.split(".")[-1].lower()
        if file_ext not in self._loaders:
            logger.error(f"no config loader found for file extension {file_ext}")
            raise RuntimeError(f"no config loader found for file extension {file_ext}")

        loader = self._loaders[file_ext]
        self._kv_dict = loader.load_config(config_fp)
        logger.info(f"loaded config file {config_fp}")

    def set(self, key: str, value: Any):
        """
        Sets the value of the config key.

        Args:
            key (str): config key
            value (Any): config value
        """
        self._kv_dict[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Gets the value of the config key.

        Args:
            key (str): config key
            default (Any, optional): default value if key not found. Defaults to None.

        Returns:
            Any: config value
        """
        return self._kv_dict.get(key, default)

    def get_int(self, key: str, default: int = None) -> int:
        """
        Gets the value of the config key as an int.

        Args:
            key (str): config key
            default (int, optional): default value if key not found. Defaults to None.

        Returns:
            int: config value
        """
        return int(self.get(key, default))

    def get_float(self, key: str, default: float = None) -> float:
        """
        Gets the value of the config key as a float.

        Args:
            key (str): config key
            default (float, optional): default value if key not found. Defaults to None.

        Returns:
            float: config value
        """
        return float(self.get(key, default))

    def get_bool(self, key: str, default: bool = None) -> bool:
        """
        Gets the value of the config key as a bool.

        Args:
            key (str): config key
            default (bool, optional): default value if key not found. Defaults to None.

        Returns:
            bool: config value
        """
        return bool(self.get(key, default))
