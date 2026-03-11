import os
from typing import Dict

from .operation_type import OperationType
from .abstract_operation import AbstractOperation
from .flatten_operation import FlattenOperation
from .move_contents_operation import MoveContentsOperation
from rst_prep.conf_validator import ConfValidator
from rst_prep.global_knobs import GlobalKnobs
from rst_prep.consts import TARGET_KEY, DEST_KEY

class FlattenAndMoveContentsOperation(AbstractOperation):
    def __init__(self, params: Dict, validate_params: bool = True) -> None:
        if validate_params:
            self._validate_params(params)
        self._target = params[TARGET_KEY]
        self._dest = params[DEST_KEY]
        if not os.path.isabs(self._target):
            self._target = os.path.abspath(os.path.join(GlobalKnobs.get_out_dir(), self._target))
        if not os.path.isabs(self._dest):
            self._dest = os.path.abspath(os.path.join(GlobalKnobs.get_out_dir(), self._dest))

    def _validate_params(self, params: Dict) -> None:
        target = params.get(TARGET_KEY, None)
        dest = params.get(DEST_KEY, None)
        errors = ConfValidator.validate_target_and_dest(target, dest)
        if any(errors):
            raise Exception({OperationType.FLATTEN_AND_MOVE_CONTENTS: errors})

    def run(self) -> None:
        FlattenOperation({TARGET_KEY: os.path.abspath(self._target)}, validate_params=False).run()
        MoveContentsOperation({TARGET_KEY: os.path.abspath(self._target), DEST_KEY: os.path.abspath(self._dest)}, validate_params=False).run()

