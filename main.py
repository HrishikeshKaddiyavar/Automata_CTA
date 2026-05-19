import re

class AlgoToCConverter:
    def __init__(self):
        self.tokens = []
        self.variables = set()
        self.c_code = []
        self.indent = 1
        self.block_stack = []

    # ---------------- LEXICAL ANALYSIS ----------------
    def tokenize(self, code):
        keywords = {"START", "STOP", "READ", "PRINT", "IF", "THEN",
                    "ELSE", "ENDIF", "WHILE", "DO", "ENDWHILE"}
        
        lines = code.strip().split("\n")
        token_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = re.findall(r'[A-Za-z_]\w*|\d+|==|!=|>=|<=|[+\-*/=<>]', line)
            tokens = []

            for part in parts:
                if part in keywords:
                    tokens.append(("KEYWORD", part))
                elif re.match(r'^\d+$', part):
                    tokens.append(("NUMBER", part))
                elif re.match(r'^[A-Za-z_]\w*$', part):
                    tokens.append(("IDENTIFIER", part))
                else:
                    tokens.append(("OPERATOR", part))

            token_lines.append((line, tokens))

        return token_lines

    # ---------------- CODE GENERATION ----------------
    def add_line(self, line):
        self.c_code.append("    " * self.indent + line)

    # ---------------- SYNTAX + SEMANTIC ANALYSIS ----------------
    def parse(self, token_lines):
        for raw_line, tokens in token_lines:

            if raw_line == "START":
                continue

            elif raw_line == "STOP":
                if self.block_stack:
                    raise Exception("Error: Unclosed block(s) detected")
                break

            elif raw_line.startswith("READ"):
                content = raw_line[4:].strip()

                # Case 1: READ "text", var
                if "," in content:
                    parts = [p.strip() for p in content.split(",")]

                    if len(parts) != 2:
                        raise Exception("Invalid READ format")

                    text, var = parts

                    if not re.match(r'^".*"$', text):
                        raise Exception("READ prompt must be in quotes")

                    if not re.match(r'^[A-Za-z_]\w*$', var):
                        raise Exception(f"Invalid variable name: {var}")

                    self.variables.add(var)

                    prompt = text.strip('"')
                    self.add_line(f'printf("{prompt}");')
                    self.add_line(f'scanf("%d", &{var});')

                # Case 2: READ var
                else:
                    var = content.strip()

                    if not re.match(r'^[A-Za-z_]\w*$', var):
                        raise Exception(f"Invalid variable name: {var}")

                    self.variables.add(var)
                    self.add_line(f'scanf("%d", &{var});')

            elif raw_line.startswith("PRINT"):
                content = raw_line[5:].strip()

                # Case 1: PRINT "text"
                if re.match(r'^".*"$', content):
                    text = content.strip('"')
                    self.add_line(f'printf("{text}\\n");')

                # Case 2: PRINT "text", var
                elif "," in content:
                    parts = [p.strip() for p in content.split(",")]
                    fmt = ""
                    args = []

                    for p in parts:
                        if re.match(r'^".*"$', p):
                            fmt += p.strip('"')
                        else:
                            fmt += "%d"
                            args.append(p)
                            self.variables.add(p)

                    args_str = ", " + ", ".join(args) if args else ""
                    self.add_line(f'printf("{fmt}\\n"{args_str});')

                # Case 3: PRINT variable
                else:
                    self.add_line(f'printf("%d\\n", {content});')
                    self.variables.add(content)
            # IF
            elif raw_line.startswith("IF"):
                if "THEN" not in raw_line:
                    raise Exception("Syntax Error: Missing THEN in IF")

                condition = re.search(r'IF (.*) THEN', raw_line)
                if not condition:
                    raise Exception("Invalid IF condition")

                self.add_line(f'if ({condition.group(1)})' + " {")
                self.indent += 1
                self.block_stack.append("IF")

            # ELSE
            elif raw_line == "ELSE":
                if not self.block_stack or self.block_stack[-1] != "IF":
                    raise Exception("ELSE without matching IF")

                self.indent -= 1
                self.add_line("} else {")
                self.indent += 1

            # ENDIF
            elif raw_line == "ENDIF":
                if not self.block_stack or self.block_stack[-1] != "IF":
                    raise Exception("ENDIF without matching IF")

                self.block_stack.pop()
                self.indent -= 1
                self.add_line("}")

            # WHILE
            elif raw_line.startswith("WHILE"):
                if "DO" not in raw_line:
                    raise Exception("Syntax Error: Missing DO in WHILE")

                condition = re.search(r'WHILE (.*) DO', raw_line)
                if not condition:
                    raise Exception("Invalid WHILE condition")

                self.add_line(f'while ({condition.group(1)})' + " {")
                self.indent += 1
                self.block_stack.append("WHILE")

            # ENDWHILE
            elif raw_line == "ENDWHILE":
                if not self.block_stack or self.block_stack[-1] != "WHILE":
                    raise Exception("ENDWHILE without matching WHILE")

                self.block_stack.pop()
                self.indent -= 1
                self.add_line("}")

            # Assignment
            elif "=" in raw_line:
                parts = raw_line.split("=")
                if len(parts) != 2:
                    raise Exception(f"Invalid assignment: {raw_line}")

                var = parts[0].strip()
                expr = parts[1].strip()

                if not re.match(r'^[A-Za-z_]\w*$', var):
                    raise Exception(f"Invalid variable name: {var}")

                self.variables.add(var)
                self.add_line(f"{var} = {expr};")

            else:
                raise Exception(f"Unknown statement: {raw_line}")

    # ---------------- MAIN CONVERSION ----------------
    def convert(self, code):
        token_lines = self.tokenize(code)

        self.c_code.append("#include <stdio.h>\n")
        self.c_code.append("int main() {")

        self.parse(token_lines)

        # Variable declarations
        if self.variables:
            decl = "int " + ", ".join(sorted(self.variables)) + ";"
            self.c_code.insert(2, "    " + decl)

        self.add_line("return 0;")
        self.c_code.append("}")

        return "\n".join(self.c_code)


# ---------------- TEST ----------------
if __name__ == "__main__":
    algo_input = """
    START
    READ "Enter n: ", n
    f = 1
    i = 1
    WHILE i <= n DO
        f = f * i
        i = i + 1
    ENDWHILE
    PRINT "Factorial of ", n, " is ", f
    STOP
    """

    converter = AlgoToCConverter()

    try:
        output = converter.convert(algo_input)
        print("Generated C Code:\n")
        print(output)
    except Exception as e:
        print("Error:", e)
