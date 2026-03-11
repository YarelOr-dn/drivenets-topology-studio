import os
import shutil
from typing import Dict

from .operation_type import OperationType
from .abstract_operation import AbstractOperation
from .delete_operation import DeleteOperation
from rst_prep.conf_validator import ConfValidator
from rst_prep.global_knobs import GlobalKnobs
from rst_prep.consts import TARGET_KEY
from rst_prep.unique_file_id import UniqueFileId


class FlattenOperation(AbstractOperation):
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
            raise Exception({OperationType.FLATTEN: errors})

    def run(self) -> None:
        # move all RST files found in subdirectories directly to target dir
        ignore_this_iteration = True # no need to move files in place
        for root, _, files in os.walk(self._target):
            if ignore_this_iteration:
                ignore_this_iteration = False
                continue
            for file in files:
                if not file.endswith(".rst"):
                    continue

                file_full_path = os.path.join(root, file)
                new_file_name = os.path.join(self._target, os.path.splitext(os.path.basename(file))[0] + ".rst")
                # rename files to avoid name conflincts
                if os.path.exists(new_file_name) or UniqueFileId.has_key(new_file_name):
                    if not UniqueFileId.has_key(new_file_name):
                        # rename the file only once for alphanumerical order to be preserved
                        os.rename(new_file_name, f"{os.path.join(self._target, os.path.splitext(os.path.basename(file))[0])}_0.rst")
                    new_file_name = os.path.join(self._target, f"{os.path.splitext(os.path.basename(file))[0]}_{UniqueFileId.get_next(new_file_name)}.rst")

                shutil.move(file_full_path, new_file_name)

        # clean up empty dirs
        for node in os.listdir(self._target):
            if not os.path.isdir(os.path.join(self._target, node)):
                continue
            DeleteOperation({TARGET_KEY: os.path.abspath(os.path.join(self._target, node))}, validate_params=False).run()
