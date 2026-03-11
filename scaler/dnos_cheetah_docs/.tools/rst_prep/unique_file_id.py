import os


class UniqueFileId:
    _unique_ids = {}

    @staticmethod
    def get_next(file: str):
        abs_file = os.path.abspath(file)
        if not UniqueFileId._unique_ids.get(abs_file, None):
            UniqueFileId._unique_ids[abs_file] = 1
        unique_id = UniqueFileId._unique_ids[abs_file]
        UniqueFileId._unique_ids[abs_file] += 1
        return unique_id

    @staticmethod
    def has_key(file: str):
        abs_file = os.path.abspath(file)
        return UniqueFileId._unique_ids.get(abs_file, None) is not None
