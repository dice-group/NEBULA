import tomlkit
from tomlkit import load

import layout_and_formal
import rhetorical
import topical

CONFIG_PATH: str = "../config.toml"


def load_config() -> tomlkit.TOMLDocument:
    with open(CONFIG_PATH, "rb") as config_file:
        return load(config_file)


def run_layout_and_formal_checks(text):
    pass


def run_rhetorical_checks():
    pass


def run_topical_checks():
    pass
