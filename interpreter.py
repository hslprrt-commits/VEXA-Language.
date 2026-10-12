class Interpreter:
    def __init__(self):
        self.env = {}

    def visit(self, node):
        if not node:
            return None
        node_type = node[0]
        if node_type == 'NUM':
            return node[1]
        elif node_type == 'STRING':
            return node[1]
        elif node_type == 'VAR':
            var_name = node[1]
            if var_name in self.env:
                return self.env[var_name]
            raise NameError(f"متغير غير معرف: '{var_name}'")
        elif node_type == 'VAR_DECL':
            var_name = node[1]
            val = self.visit(node[2])
            self.env[var_name] = val
            return val
        elif node_type == 'PRINT':
            val = self.visit(node[1])
            print(val)
            return val
        elif node_type == 'BIN_OP':
            left = self.visit(node[1])
            op = node[2]
            right = self.visit(node[3])
            if op == '+':
                return left + right
            elif op == '-':
                return left - right
            elif op == '*':
                return left * right
            elif op == '/':
                return left / right
        raise Exception(f"نوع عقدة غير معروف: {node_type}")

    def interpret(self, statements):
        result = None
        for stmt in statements:
            result = self.visit(stmt)
        return result
