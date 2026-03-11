import os
import shutil
from typing import Dict

from .operation_type import OperationType
from .abstract_operation import AbstractOperation
from .delete_operation import DeleteOperation
from rst_prep.conf_validator import ConfValidator
from rst_prep.global_knobs import GlobalKnobs
from rst_prep.consts import TARGET_KEY, DEST_KEY, FILES_KEY
from rst_prep.unique_file_id import UniqueFileId


class MoveContentsOperation(AbstractOperation):
    def __init__(self, params: Dict, validate_params: bool = True) -> None:
        if validate_params:
            self._validate_params(params)
        self._target = params[TARGET_KEY]
        self._dest = params[DEST_KEY]
        self._files = params.get(FILES_KEY, [])
        if not os.path.isabs(self._target):
            self._target = os.path.abspath(os.path.join(GlobalKnobs.get_out_dir(), self._target))
        if not os.path.isabs(self._dest):
            self._dest = os.path.abspath(os.path.join(GlobalKnobs.get_out_dir(), self._dest))
        if not isinstance(self._files, list):
            self._files = [self._files]
        for i in range(len(self._files)):
            self._files[i] = os.path.join(self._target, self._files[i])

    def _validate_params(self, params: Dict) -> None:
        target = params.get(TARGET_KEY, None)
        dest = params.get(DEST_KEY, None)
        files = params.get(FILES_KEY, [])
        errors = [*ConfValidator.validate_target_and_dest(target, dest),
                  *ConfValidator.validate_target_and_files(target, files)]
        if any(errors):
            raise Exception({OperationType.MOVE_CONTENTS: errors})

    def run(self) -> None:
        if not os.path.exists(self._dest):
            os.makedirs(self._dest)

        if self._files and len(self._files) > 0:
            files_list = self._files
        else:
            files_list = map(lambda x: os.path.join(self._target, x), os.listdir(self._target))

        for file in files_list:
            if not file.endswith(".rst"):
                continue

            new_file_name = os.path.join(self._dest, f"{os.path.splitext(os.path.basename(file))[0]}.rst")
            # rename files to avoid name conflincts
            if os.path.exists(new_file_name) or UniqueFileId.has_key(new_file_name):
                if not UniqueFileId.has_key(new_file_name):
                    # rename the file only once for alphanumerical order to be preserved
                    os.rename(new_file_name, f"{os.path.join(self._dest, os.path.splitext(os.path.basename(file))[0])}_0.rst")
                new_file_name = os.path.join(self._dest, f"{os.path.splitext(os.path.basename(file))[0]}_{UniqueFileId.get_next(new_file_name)}.rst")

            shutil.move(file, new_file_name)

        if not self._files or len(self._files) <= 0:
            # cleanup emtpy dir
            DeleteOperation({TARGET_KEY: os.path.abspath(self._target)}, validate_params=False).run()
