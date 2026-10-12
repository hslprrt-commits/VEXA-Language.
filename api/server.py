from flask import Flask, request, jsonify
import io
import sys
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

app = Flask(__name__)

@app.route('/api/server', methods=['POST'])
def run_code():
    data = request.json or {}
    code = data.get('code', '')
    
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    
    output = ""
    try:
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        interpreter = Interpreter()
        interpreter.interpret(ast)
        output = buffer.getvalue()
    except Exception as e:
        output = f"Error: {str(e)}"
    finally:
        sys.stdout = old_stdout
        
    return jsonify({'output': output})
