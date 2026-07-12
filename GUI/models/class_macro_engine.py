import json
from dataclasses import dataclass


@dataclass
class MacroOp:
    op_type: str
    args: dict


class MacroEngine:
    def __init__(self):
        self.ops: list[MacroOp] = []
        self.undo_stack: list[MacroOp] = []
        self.redo_stack: list[MacroOp] = []

    def add_op(self, op_type: str, **kwargs):
        op = MacroOp(op_type, kwargs)
        self.ops.append(op)
        self.undo_stack.append(op)
        self.redo_stack.clear()

    def undo_last(self):
        if not self.undo_stack:
            return None
        op = self.undo_stack.pop()
        self.redo_stack.append(op)
        return op  # controller decides how to undo in virtual model

    def redo_last(self):
        if not self.redo_stack:
            return None
        op = self.redo_stack.pop()
        self.undo_stack.append(op)
        return op

    def to_json(self) -> str:
        return json.dumps([{"op": o.op_type, "args": o.args} for o in self.ops], indent=2)

    def save_to_file(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
