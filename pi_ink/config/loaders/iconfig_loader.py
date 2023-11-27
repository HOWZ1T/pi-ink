from abc import ABC
from typing import Any, Dict, List


class IConfigLoader(ABC):
    def load_config(self, config_fp: str) -> Dict[str, Any]:
        """
        Loads the config file and returns a dictionary of the config key value pairs.

        Args:
            config_fp (str): path to config file

        Returns:
            Dict[str, Any]: dictionary of config key value pairs
        """
        raise NotImplementedError("load_config() not implemented")

    def get_type(self) -> List[str]:
        """
        Returns the type of config loader.

        Returns:
            str: type of config loader
        """
        raise NotImplementedError("get_type() not implemented")
