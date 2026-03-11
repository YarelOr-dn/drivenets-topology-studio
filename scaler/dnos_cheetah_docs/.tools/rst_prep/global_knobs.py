from typing import Dict, List

from rst_prep import consts

class GlobalKnobs:
    _in_dir: str = ".."
    _out_dir: str = ".."
    _rename_rsts_based_on_cmd_name: bool = False

    def __init__(self) -> None:
        raise Exception("Don't you dare instantiate me!")

    @staticmethod
    def set_in_dir(val: str) -> None:
        GlobalKnobs._in_dir = val

    @staticmethod
    def get_in_dir() -> str:
        return GlobalKnobs._in_dir

    @staticmethod
    def set_out_dir(val: str) -> None:
        GlobalKnobs._out_dir = val

    @staticmethod
    def get_out_dir() -> str:
        return GlobalKnobs._out_dir

    @staticmethod
    def set_rename_rsts_based_on_cmd_name(val: bool) -> None:
        GlobalKnobs._rename_rsts_based_on_cmd_name = val

    @staticmethod
    def get_rename_rsts_based_on_cmd_name() -> bool:
        return GlobalKnobs._rename_rsts_based_on_cmd_name

    @staticmethod
    def load_from_config(config: List[Dict]) -> None:
        for el in config:
            if consts.GLOBAL_KNOBS_KEY in el.keys():
                global_knobs = el[consts.GLOBAL_KNOBS_KEY]
                GlobalKnobs.set_in_dir(global_knobs.get(consts.RSTS_ROOT_KEY, GlobalKnobs.get_in_dir()))
                GlobalKnobs.set_out_dir(global_knobs.get(consts.OUT_RST_DIR_KEY, GlobalKnobs.get_out_dir()))
                GlobalKnobs.set_rename_rsts_based_on_cmd_name(global_knobs.get(consts.RENAME_RSTS_BASED_ON_CMD_NAME_KEY, GlobalKnobs.get_rename_rsts_based_on_cmd_name()))
                break
