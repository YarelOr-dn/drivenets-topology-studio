from enum import Enum, unique, auto

@unique
class OperationType(Enum):
    DELETE = auto()
    FLATTEN_AND_MOVE_CONTENTS = auto()
    FLATTEN = auto()
    MOVE_CONTENTS = auto()
    MOVE_DIR = auto()
    RENAME_RSTS_BASED_ON_CMD_NAMES = auto()
    FIX_MULTILINE_TABLES = auto()

    @staticmethod
    def from_str(oper: str):
        if oper not in OperationType._member_names_:
            raise Exception(f"Invalid operation: {oper}")
        return OperationType[oper.upper()]
