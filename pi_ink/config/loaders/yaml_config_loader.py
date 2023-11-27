from typing import Any, Dict, List

import yaml

from .iconfig_loader import IConfigLoader


class YamlConfigLoader(IConfigLoader):
    safe: bool

    def __init__(self, safe: bool = True):
        """
        Args:
            safe (bool, optional): whether to use safe yaml loader. Defaults to True.
        """
        self.safe = safe

    def get_type(self) -> List[str]:
        return ["yaml", "yml"]

    def load_config(self, config_fp: str) -> Dict[str, Any]:
        """
        Loads the config file and returns a dictionary of the config key value pairs.

        Args:
            config_fp (str): path to config file

        Returns:
            Dict[str, Any]: dictionary of config key value pairs
        """
        with open(config_fp, "r") as f:
            return yaml.load(f, Loader=yaml.SafeLoader if self.safe else yaml.Loader)
