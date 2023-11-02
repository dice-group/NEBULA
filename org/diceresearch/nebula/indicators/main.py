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
#ToDo Import check_for_excessive_capitalization, check_for_excessive_emojis, check_for_excessive_hashtags, check_for_incorrect_spelling

def run_rhetorical_checks():
    pass


def run_topical_checks():
    pass


#ToDo Import Json

#ToDo Save Json
