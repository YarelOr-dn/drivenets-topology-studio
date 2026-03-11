from typing import Dict

from rst_prep.operations import DeleteOperation
from rst_prep.operations import FlattenAndMoveContentsOperation
from rst_prep.operations import FlattenOperation
from rst_prep.operations import MoveContentsOperation
from rst_prep.operations import MoveDirOperation
from rst_prep.operations import AbstractOperation
from rst_prep.operations import OperationType

class OperationDispatcher:
    _OPER_HANDLERS = {
        OperationType.DELETE: DeleteOperation,
        OperationType.FLATTEN_AND_MOVE_CONTENTS: FlattenAndMoveContentsOperation,
        OperationType.FLATTEN: FlattenOperation,
        OperationType.MOVE_CONTENTS: MoveContentsOperation,
        OperationType.MOVE_DIR: MoveDirOperation,
    }

    @staticmethod
    def dispatch(oper: str, params: Dict) -> AbstractOperation:
        oper_type = OperationType.from_str(oper)
        Handler = OperationDispatcher._OPER_HANDLERS[oper_type]
        return Handler(params)
