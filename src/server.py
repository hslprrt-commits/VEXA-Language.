from flask import Flask, request, jsonify, send_from_directory
import io
import sys
from lexer import Lexer
from parser import Parser
from interpreter import Interpreter

app = Flask(__name__, static_url_path='', static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/run', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '')
    
    # التقاط المخرجات (print statements)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
