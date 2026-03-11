import os
import shutil
from typing import Dict

from .operation_type import OperationType
from .abstract_operation import AbstractOperation
from rst_prep.conf_validator import ConfValidator
from rst_prep.global_knobs import GlobalKnobs
from rst_prep.consts import TARGET_KEY, FILES_KEY

class DeleteOperation(AbstractOperation):
    def __init__(self, params: Dict, validate_params: bool = True) -> None:
        if validate_params:
            self._validate_params(params)
        self._target = params[TARGET_KEY]
        if not os.path.isabs(self._target):
            self._target = os.path.abspath(os.path.join(GlobalKnobs.get_out_dir(), self._target))
        self._files = params.get(FILES_KEY, [])
        if not isinstance(self._files, list):
            self._files = [self._files]
        for i in range(len(self._files)):
            self._files[i] = os.path.join(self._target, self._files[i])

    def _validate_params(self, params: Dict) -> None:
        target = params.get(TARGET_KEY, None)
        files = params.get(FILES_KEY, [])
        errors = ConfValidator.validate_target_and_files(target, files)
        if any(errors):
            raise Exception({OperationType.DELETE: errors})

    def run(self) -> None:
        if self._files and len(self._files) > 0:
            for file in self._files:
                os.remove(file)
        else:
            shutil.rmtree(self._target)
