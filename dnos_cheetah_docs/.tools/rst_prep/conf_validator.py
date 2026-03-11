import os
from typing import List, Union

from rst_prep.consts import TARGET_KEY, DEST_KEY, FILES_KEY
from rst_prep.global_knobs import GlobalKnobs

class ConfValidator:
    @staticmethod
    def validate_target(target: str) -> List[str]:
        errors = []
        if target is None or "" == target:
            errors.append(f"{TARGET_KEY} attribute is missing")
        else:
            target = os.path.join(GlobalKnobs.get_in_dir(), target)
            if not os.path.exists(target):
                errors.append(f"{TARGET_KEY} path couldn't be found on your filesystem: {os.path.abspath(target)}")
        return errors

    @staticmethod
    def validate_target_and_dest(target: str, dest: str) -> List[str]:
        errors = []
        errors.extend(ConfValidator.validate_target(target))
        if dest is None or "" == dest:
            errors.append(f"{DEST_KEY} attribute is missing")
        if target == dest:
            errors.append(f"{TARGET_KEY} and {DEST_KEY} attributes cannot have the same value: {target} == {dest}")
        return errors

    @staticmethod
    def validate_target_and_files(target: str, files: Union[str, List[str]]) -> List[str]:
        errors = []
        errors.extend(ConfValidator.validate_target(target))
        if isinstance(files, str):
            files = [files]
        root = os.path.join(GlobalKnobs.get_in_dir(), target)
        for file in files:
            file_path = os.path.join(root, file)
            if not os.path.exists(file_path):
                errors.append(f"This file couldn't be found on your filesystem: {os.path.abspath(file_path)}")
        return errors
