import os
from typing import Dict

from .operation_type import OperationType
from .abstract_operation import AbstractOperation
from rst_prep.conf_validator import ConfValidator
from rst_prep.global_knobs import GlobalKnobs
from rst_prep.consts import TARGET_KEY

class RenameRstsBasedOnCmdNamesOperation(AbstractOperation):
    def __init__(self, params: Dict, validate_params: bool = True) -> None:
        if validate_params:
            self._validate_params(params)
        self._target = params[TARGET_KEY]
        if not os.path.isabs(self._target):
            self._target = os.path.abspath(os.path.join(GlobalKnobs.get_out_dir(), self._target))

    def _validate_params(self, params: Dict) -> None:
        target = params.get(TARGET_KEY, None)
        errors = ConfValidator.validate_target(target)
        if any(errors):
            raise Exception({OperationType.RENAME_RSTS_BASED_ON_CMD_NAMES: errors})

    def run(self) -> None:
        for root, _, files in os.walk(self._target):
            for file in files:
                if not file.endswith(".rst"):
                    continue
                file_full_path = os.path.join(root, file)
                new_file_name = os.path.join(root, self._get_first_line_of_file(file_full_path) + ".rst")
                if file_full_path != new_file_name:
                    if os.path.exists(new_file_name):
                        raise Exception(f"Trying to rename {file_full_path} failed. File already exists: {new_file_name}")
                    os.rename(file_full_path, new_file_name)

    def _get_first_line_of_file(self, file_path: str) -> str:
        with open(file_path, "r") as file:
            for line in file:
                line = line.strip()
                if len(line) > 0:
                    return line
