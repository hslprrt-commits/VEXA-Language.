
"""
VEXA Language Interpreter
Version: 0.1.0
Purpose: Experimental programming language with system simulation goals.
"""

import ast
import operator
import re
import sys
from pathlib import Path


VERSION = "0.1.0"

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}

COMPARE_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


class VEXAError(Exception):
    """Error raised while parsing or executing VEXA code."""


class VEXAInterpreter:
    def __init__(self):
        self.variables = {}
        self.stopped = False

    def fail(self, line, message):
        raise VEXAError(f"Line {line}: {message}")

    def evaluate(self, expression, line):
        try:
            tree = ast.parse(expression, mode="eval")
            return self._eval_node(tree.body, line)
        except VEXAError:
            raise
        except (SyntaxError, ValueError, TypeError,
                ZeroDivisionError, OverflowError) as exc:
            self.fail(line, f"Invalid expression: {exc}")

    def _eval_node(self, node, line):
        if isinstance(node, ast.Constant):
            if type(node.value) in (str, int, float, bool):
                return node.value
            self.fail(line, "Unsupported value")

        if isinstance(node, ast.Name):
            if node.id == "true":
                return True
            if node.id == "false":
                return False
            if node.id in self.variables:
                return self.variables[node.id]
            self.fail(line, f"Unknown variable: {node.id}")

        if isinstance(node, ast.BinOp):
            operation = BINARY_OPERATORS.get(type(node.op))
            if operation is None:
                self.fail(line, "Unsupported operator")

            left = self._eval_node(node.left, line)
            right = self._eval_node(node.right, line)

            try:
                result = operation(left, right)
            except (TypeError, ValueError, ZeroDivisionError,
                    OverflowError) as exc:
                self.fail(line, f"Operation failed: {exc}")

            if type(result) in (int, float) and abs(result) > 10**100:
                self.fail(line, "Numeric result is too large")

            return result

        if isinstance(node, ast.UnaryOp):
            value = self._eval_node(node.operand, line)

            if isinstance(node.op, ast.Not):
                return not value

            if isinstance(node.op, ast.USub):
                if type(value) in (int, float):
                    return -value

            if isinstance(node.op, ast.UAdd):
                if type(value) in (int, float):
                    return value

            self.fail(line, "Unsupported unary operation")

        if isinstance(node, ast.Compare):
            left = self._eval_node(node.left, line)

            for op_node, comparator in zip(
                node.ops, node.comparators
            ):
                operation = COMPARE_OPERATORS.get(type(op_node))
                if operation is None:
                    self.fail(line, "Unsupported comparison")

                right = self._eval_node(comparator, line)

                try:
                    if not operation(left, right):
                        return False
                except TypeError as exc:
                    self.fail(line, f"Comparison failed: {exc}")

                left = right

            return True

        self.fail(line, "Unsupported expression")

    def find_block(self, lines, start, end):
        depth = 0
        else_position = None

        for index in range(start + 1, end):
            command = lines[index].strip()

            if command.startswith("vwhen "):
                depth += 1

            elif command == "vdone":
                if depth == 0:
                    return else_position, index
                depth -= 1

            elif command == "velse" and depth == 0:
                if else_position is not None:
                    self.fail(index + 1, "Duplicate velse")
                else_position = index

        self.fail(start + 1, "Missing vdone")

    def execute_range(self, lines, start, end):
        index = start

        while index < end and not self.stopped:
            raw = lines[index]
            command = raw.strip()
            line = index + 1
            index += 1

            if not command or command.startswith("#"):
                continue

            if command.startswith("vdisr "):
                expression = command[len("vdisr "):].strip()
                value = self.evaluate(expression, line)
                print(value)
                continue

            if command.startswith("vforge "):
                match = re.fullmatch(
                    r"vforge\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)",
                    command,
                )

                if not match:
                    self.fail(
                        line,
                        "Syntax: vforge name = expression",
                    )

                name, expression = match.groups()
                self.variables[name] = self.evaluate(expression, line)
                continue

            if command.startswith("vxin "):
                match = re.fullmatch(
                    r'vxin\s+("(?:[^"\\]|\\.)*")\s*->\s*'
                    r"([A-Za-z_][A-Za-z0-9_]*)",
                    command,
                )

                if not match:
                    self.fail(
                        line,
                        'Syntax: vxin "prompt" -> variable',
                    )

                prompt, name = match.groups()
                prompt_text = self.evaluate(prompt, line)
                self.variables[name] = input(str(prompt_text))
                continue

            if command.startswith("vwhen "):
                expression = command[len("vwhen "):].strip()
                condition = self.evaluate(expression, line)

                else_pos, done_pos = self.find_block(
                    lines, index - 1, end
                )

                if condition:
                    branch_end = (
                        else_pos if else_pos is not None else done_pos
                    )
                    self.execute_range(lines, index, branch_end)

                elif else_pos is not None:
                    self.execute_range(
                        lines, else_pos + 1, done_pos
                    )

                index = done_pos + 1
                continue

            if command == "vhalt":
                self.stopped = True
                return

            if command in ("velse", "vdone"):
                self.fail(line, f"Unexpected command: {command}")

            self.fail(line, f"Unknown command: {command}")

    def run(self, source):
        self.execute_range(source.splitlines(), 0, len(source.splitlines()))


def main():
    if len(sys.argv) != 2:
        print(f"VEXA Interpreter v{VERSION}")
        print("Usage: python vexa.py main.vexa")
        return 2

    path = Path(sys.argv[1])

    if path.suffix != ".vexa":
        print("Error: VEXA source files must end in .vexa")
        return 2

    try:
        source = path.read_text(encoding="utf-8")
        VEXAInterpreter().run(source)
        return 0

    except FileNotFoundError:
        print(f"Error: File not found: {path}")
        return 1

    except VEXAError as exc:
        print(f"VEXA Error: {exc}")
        return 1

    except (OSError, UnicodeError) as exc:
        print(f"File Error: {exc}")
        return 1

    except (EOFError, KeyboardInterrupt):
        print("\nVEXA execution interrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
