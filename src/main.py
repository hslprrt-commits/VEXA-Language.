import sys

def run_code(code):
    print("=== VEXA-Language Runner ===")
    print(f"Executing: {code}")

def main():
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        run_code(code)
    else:
        print("=== VEXA-Language REPL (v0.1) ===")
        while True:
            try:
                code = input("vexa> ")
                if code.strip() == "exit":
                    break
                if code.strip():
                    run_code(code)
            except (KeyboardInterrupt, EOFError):
                break

if __name__ == '__main__':
    main()
