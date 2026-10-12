class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos] if self.tokens else None

    def error(self):
        raise SyntaxError("خطأ نحوي في بناء الجملة (Syntax Error)")

    def eat(self, token_type):
        if self.current_token and self.current_token.type == token_type:
            self.pos += 1
            if self.pos < len(self.tokens):
                self.current_token = self.tokens[self.pos]
            else:
                self.current_token = None
        else:
            self.error()

    def factor(self):
        token = self.current_token
        if token.type == 'NUMBER':
            self.eat('NUMBER')
            return ('NUM', token.value)
        elif token.type == 'STRING':
            self.eat('STRING')
            return ('STRING', token.value)
        elif token.type == 'IDENTIFIER':
            var_name = token.value
            self.eat('IDENTIFIER')
            return ('VAR', var_name)
        elif token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            return node
        self.error()

    def term(self):
        node = self.factor()
        while self.current_token and self.current_token.type in ('MUL', 'DIV'):
            token = self.current_token
            if token.type == 'MUL':
                self.eat('MUL')
            elif token.type == 'DIV':
                self.eat('DIV')
            node = ('BIN_OP', node, token.value, self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.current_token and self.current_token.type in ('PLUS', 'MINUS'):
            token = self.current_token
            if token.type == 'PLUS':
                self.eat('PLUS')
            elif token.type == 'MINUS':
                self.eat('MINUS')
            node = ('BIN_OP', node, token.value, self.term())
        return node

    def statement(self):
        token = self.current_token
        if token.type == 'KEYWORD' and token.value == 'var':
            self.eat('KEYWORD')
            var_name = self.current_token.value
            self.eat('IDENTIFIER')
            self.eat('ASSIGN')
            expr_val = self.expr()
            return ('VAR_DECL', var_name, expr_val)
        elif token.type == 'KEYWORD' and token.value == 'print':
            self.eat('KEYWORD')
            self.eat('LPAREN')
            expr_val = self.expr()
            self.eat('RPAREN')
            return ('PRINT', expr_val)
        else:
            return self.expr()

    def parse(self):
        statements = []
        while self.current_token and self.current_token.type != 'EOF':
            statements.append(self.statement())
        return statements
