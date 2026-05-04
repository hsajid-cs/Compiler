"""
Phase 3: Semantic Analyzer
Walks the AST and checks:
  - Variables are declared before use
  - No duplicate declarations in the same scope
  - Type compatibility in assignments and expressions
  - Function call argument count matches definition
  - Return types match function signatures
  - A main() function exists
All errors are human-friendly with line numbers.
"""

from ast_nodes import *


# ── Semantic Error ───────────────────────────────────────────────────────────

class SemanticError:
    """A single semantic error — we collect them all instead of stopping at the first."""

    def __init__(self, message, line):
        self.message = message
        self.line = line

    def __repr__(self):
        return f"Line {self.line}: {self.message}"


# ── Symbol Table ─────────────────────────────────────────────────────────────

class SymbolTable:
    """
    A scope stack: list of dictionaries.
    Each dictionary maps variable name → {'type': str, 'kind': 'var'|'array'|'func', ...}
    The last element is the current (innermost) scope.
    """

    def __init__(self):
        self.scopes = [{}]  # start with global scope

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, name, info):
        """Declare a symbol in the current scope. Returns False if already declared here."""
        current = self.scopes[-1]
        if name in current:
            return False
        current[name] = info
        return True

    def lookup(self, name):
        """Look up a symbol from innermost to outermost scope. Returns info or None."""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_current_scope(self, name):
        """Look up a symbol only in the current scope."""
        return self.scopes[-1].get(name)


# ── Semantic Analyzer ────────────────────────────────────────────────────────

class SemanticAnalyzer:
    """
    Usage:
        analyzer = SemanticAnalyzer()
        errors = analyzer.analyze(ast)
        if errors:
            for err in errors: print(err)
    """

    # Built-in functions that don't need to be declared
    BUILTINS = {
        "print": {"kind": "func", "ret_type": "void", "params": [("int", "value")]},
        "read":  {"kind": "func", "ret_type": "int",  "params": []},
    }

    def __init__(self):
        self.symbols = SymbolTable()
        self.errors = []
        self.current_function = None  # track which function we're inside

    def _error(self, message, line):
        self.errors.append(SemanticError(message, line))

    # ── Main entry point ─────────────────────────────────────────────────

    def analyze(self, program: Program) -> list:
        """Analyze the entire program. Returns list of SemanticError."""
        self.errors = []

        # First pass: register all function signatures (allows forward calls)
        for func in program.functions:
            param_info = [(p.param_type, p.name) for p in func.params]
            success = self.symbols.declare(func.name, {
                "kind": "func",
                "ret_type": func.ret_type,
                "params": param_info,
            })
            if not success:
                self._error(
                    f"Function '{func.name}' is defined more than once. "
                    f"Each function name must be unique.",
                    func.line,
                )

        # Check for main
        main_info = self.symbols.lookup("main")
        if not main_info or main_info["kind"] != "func":
            self._error(
                "Every C program needs a 'main' function, but I couldn't find one! "
                "Add: int main() { ... }",
                1,
            )

        # Second pass: analyze each function body
        for func in program.functions:
            self._analyze_func(func)

        return self.errors

    # ── Function ─────────────────────────────────────────────────────────

    def _analyze_func(self, func: FuncDef):
        self.current_function = func
        self.symbols.enter_scope()

        # Declare parameters
        for param in func.params:
            success = self.symbols.declare(param.name, {
                "kind": "var",
                "type": param.param_type,
            })
            if not success:
                self._error(
                    f"Parameter '{param.name}' is declared twice in function '{func.name}'. "
                    f"Each parameter must have a unique name.",
                    param.line,
                )

        # Analyze body
        self._analyze_block(func.body)

        self.symbols.exit_scope()
        self.current_function = None

    # ── Block ────────────────────────────────────────────────────────────

    def _analyze_block(self, block: Block):
        self.symbols.enter_scope()
        for stmt in block.statements:
            self._analyze_statement(stmt)
        self.symbols.exit_scope()

    # ── Statements ───────────────────────────────────────────────────────

    def _analyze_statement(self, stmt):
        if isinstance(stmt, VarDecl):
            self._analyze_var_decl(stmt)
        elif isinstance(stmt, ArrayDecl):
            self._analyze_array_decl(stmt)
        elif isinstance(stmt, Assignment):
            self._analyze_assignment(stmt)
        elif isinstance(stmt, ArrayAssignment):
            self._analyze_array_assignment(stmt)
        elif isinstance(stmt, IfStmt):
            self._analyze_if(stmt)
        elif isinstance(stmt, WhileStmt):
            self._analyze_while(stmt)
        elif isinstance(stmt, DoWhileStmt):
            self._analyze_do_while(stmt)
        elif isinstance(stmt, ForStmt):
            self._analyze_for(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._analyze_return(stmt)
        elif isinstance(stmt, ExpressionStmt):
            self._analyze_expr(stmt.expr)
        elif isinstance(stmt, Block):
            self._analyze_block(stmt)
        else:
            self._error(f"Unknown statement type: {type(stmt).__name__}", getattr(stmt, 'line', 0))

    def _analyze_var_decl(self, decl: VarDecl):
        # Check for redeclaration in current scope
        if self.symbols.lookup_current_scope(decl.name):
            self._error(
                f"Variable '{decl.name}' is already declared in this scope. "
                f"Pick a different name or remove the duplicate.",
                decl.line,
            )
        else:
            self.symbols.declare(decl.name, {"kind": "var", "type": decl.var_type})

        # Type-check the initializer
        if decl.init_expr:
            init_type = self._analyze_expr(decl.init_expr)
            if init_type and init_type != decl.var_type:
                if decl.var_type == "int" and init_type == "float":
                    self._error(
                        f"Type mismatch — you're initializing '{decl.name}' (int) with a float value. "
                        f"That would lose the decimal part!",
                        decl.line,
                    )
                elif not (decl.var_type == "float" and init_type == "int"):
                    # int → float is OK (widening), anything else is not
                    self._error(
                        f"Type mismatch — '{decl.name}' is declared as '{decl.var_type}' "
                        f"but you're initializing it with a '{init_type}' value.",
                        decl.line,
                    )

    def _analyze_array_decl(self, decl: ArrayDecl):
        if self.symbols.lookup_current_scope(decl.name):
            self._error(
                f"Array '{decl.name}' is already declared in this scope.",
                decl.line,
            )
        else:
            self.symbols.declare(decl.name, {
                "kind": "array",
                "type": decl.var_type,
                "size": decl.size,
            })
        if decl.size <= 0:
            self._error(
                f"Array '{decl.name}' has size {decl.size}, but array size must be positive.",
                decl.line,
            )

    def _analyze_assignment(self, stmt: Assignment):
        info = self.symbols.lookup(stmt.name)
        if not info:
            self._error(
                f"Hey, '{stmt.name}' hasn't been declared yet. "
                f"Did you forget something like 'int {stmt.name};'?",
                stmt.line,
            )
            self._analyze_expr(stmt.expr)
            return

        if info["kind"] == "func":
            self._error(
                f"'{stmt.name}' is a function, not a variable — you can't assign to it!",
                stmt.line,
            )
            return

        if info["kind"] == "array":
            self._error(
                f"'{stmt.name}' is an array. Use '{stmt.name}[index] = value;' to assign to an element.",
                stmt.line,
            )
            return

        expr_type = self._analyze_expr(stmt.expr)
        var_type = info["type"]
        if expr_type and expr_type != var_type:
            if var_type == "int" and expr_type == "float":
                self._error(
                    f"Type mismatch — you're assigning a 'float' to '{stmt.name}', which is an 'int'. "
                    f"That's not allowed because you'd lose the decimal part.",
                    stmt.line,
                )
            elif not (var_type == "float" and expr_type == "int"):
                self._error(
                    f"Type mismatch — '{stmt.name}' is '{var_type}' but you're assigning a '{expr_type}'.",
                    stmt.line,
                )

    def _analyze_array_assignment(self, stmt: ArrayAssignment):
        info = self.symbols.lookup(stmt.name)
        if not info:
            self._error(f"Array '{stmt.name}' hasn't been declared.", stmt.line)
        elif info["kind"] != "array":
            self._error(
                f"'{stmt.name}' is not an array — you can't use [index] on it.",
                stmt.line,
            )

        idx_type = self._analyze_expr(stmt.index)
        if idx_type and idx_type != "int":
            self._error(
                f"Array index must be an integer, but you used a '{idx_type}'.",
                stmt.line,
            )

        self._analyze_expr(stmt.expr)

    # ── Control flow ─────────────────────────────────────────────────────

    def _analyze_if(self, stmt: IfStmt):
        self._analyze_expr(stmt.condition)
        self._analyze_statement(stmt.then_branch)
        if stmt.else_branch:
            self._analyze_statement(stmt.else_branch)

    def _analyze_while(self, stmt: WhileStmt):
        self._analyze_expr(stmt.condition)
        self._analyze_statement(stmt.body)

    def _analyze_do_while(self, stmt: DoWhileStmt):
        self._analyze_statement(stmt.body)
        self._analyze_expr(stmt.condition)

    def _analyze_for(self, stmt: ForStmt):
        # For has its own mini-scope for the init variable
        self.symbols.enter_scope()
        if stmt.init:
            self._analyze_statement(stmt.init)
        if stmt.condition:
            self._analyze_expr(stmt.condition)
        if stmt.update:
            self._analyze_statement(stmt.update)
        self._analyze_statement(stmt.body)
        self.symbols.exit_scope()

    def _analyze_return(self, stmt: ReturnStmt):
        if self.current_function is None:
            self._error("'return' outside of a function — that's not allowed!", stmt.line)
            return

        func = self.current_function
        if func.ret_type == "void":
            if stmt.expr is not None:
                self._error(
                    f"Function '{func.name}' is 'void' — it shouldn't return a value.",
                    stmt.line,
                )
        else:
            if stmt.expr is None:
                self._error(
                    f"Function '{func.name}' should return a '{func.ret_type}', "
                    f"but this return statement has no value.",
                    stmt.line,
                )
            else:
                ret_type = self._analyze_expr(stmt.expr)
                if ret_type and ret_type != func.ret_type:
                    if not (func.ret_type == "float" and ret_type == "int"):
                        self._error(
                            f"Function '{func.name}' should return '{func.ret_type}', "
                            f"but this returns a '{ret_type}'.",
                            stmt.line,
                        )

    # ── Expression analysis (returns the inferred type or None) ──────────

    def _analyze_expr(self, expr) -> str | None:
        """Analyze an expression and return its inferred type (or None on error)."""

        if isinstance(expr, Literal):
            return expr.lit_type

        if isinstance(expr, Identifier):
            info = self.symbols.lookup(expr.name)
            if not info:
                self._error(
                    f"Hey, '{expr.name}' hasn't been declared yet. "
                    f"Did you forget something like 'int {expr.name};'?",
                    expr.line,
                )
                return None
            if info["kind"] == "func":
                self._error(
                    f"'{expr.name}' is a function — did you mean to call it with '{expr.name}()'?",
                    expr.line,
                )
                return None
            if info["kind"] == "array":
                self._error(
                    f"'{expr.name}' is an array — did you mean '{expr.name}[index]'?",
                    expr.line,
                )
                return None
            return info["type"]

        if isinstance(expr, ArrayAccess):
            info = self.symbols.lookup(expr.name)
            if not info:
                self._error(f"Array '{expr.name}' hasn't been declared.", expr.line)
                return None
            if info["kind"] != "array":
                self._error(f"'{expr.name}' is not an array — you can't index it.", expr.line)
                return None
            idx_type = self._analyze_expr(expr.index)
            if idx_type and idx_type != "int":
                self._error(f"Array index must be an integer, but you used a '{idx_type}'.", expr.line)
            return info["type"]

        if isinstance(expr, BinOp):
            left_type = self._analyze_expr(expr.left)
            right_type = self._analyze_expr(expr.right)

            if left_type is None or right_type is None:
                return None

            # Relational and logical operators always produce int (0 or 1)
            if expr.op in ("<", ">", "<=", ">=", "==", "!=", "&&", "||"):
                return "int"

            # Arithmetic: if either is float, result is float
            if left_type == "float" or right_type == "float":
                return "float"

            # char arithmetic → int (like C)
            return "int" if left_type == "char" or right_type == "char" else left_type

        if isinstance(expr, UnaryOp):
            operand_type = self._analyze_expr(expr.operand)
            if expr.op == "!":
                return "int"
            return operand_type  # negation preserves type

        if isinstance(expr, FuncCall):
            return self._analyze_func_call(expr)

        self._error(f"Unknown expression type: {type(expr).__name__}", getattr(expr, 'line', 0))
        return None

    def _analyze_func_call(self, call: FuncCall) -> str | None:
        """Analyze a function call and return its return type."""
        # Check builtins first
        if call.name in self.BUILTINS:
            builtin = self.BUILTINS[call.name]
            # print accepts any single argument
            if call.name == "print":
                if len(call.args) != 1:
                    self._error(
                        f"'print' takes exactly 1 argument, but you gave it {len(call.args)}.",
                        call.line,
                    )
                else:
                    self._analyze_expr(call.args[0])
            elif call.name == "read":
                if len(call.args) != 0:
                    self._error(
                        f"'read' takes no arguments — it returns the value read from input.",
                        call.line,
                    )
            return builtin["ret_type"]

        info = self.symbols.lookup(call.name)
        if not info:
            self._error(
                f"Function '{call.name}' hasn't been defined. "
                f"Did you spell it correctly?",
                call.line,
            )
            return None

        if info["kind"] != "func":
            self._error(
                f"'{call.name}' is not a function — you can't call it with '()'.",
                call.line,
            )
            return None

        expected = len(info["params"])
        actual = len(call.args)
        if expected != actual:
            self._error(
                f"Function '{call.name}' expects {expected} argument(s), "
                f"but you gave it {actual}. Check the call.",
                call.line,
            )

        # Analyze each argument
        for arg in call.args:
            self._analyze_expr(arg)

        return info["ret_type"]


# ── Standalone test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    from lexer import Lexer, LexerError
    from parser import Parser, ParseError

    if len(sys.argv) < 2:
        test_code = """
int fibonacci(int n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int i = 0;
    while (i < 10) {
        print(fibonacci(i));
        i = i + 1;
    }
    return 0;
}
"""
        print("=== Semantic Analysis Test: Fibonacci ===\n")
    else:
        with open(sys.argv[1], "r") as f:
            test_code = f.read()

    try:
        lexer = Lexer(test_code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        analyzer = SemanticAnalyzer()
        errors = analyzer.analyze(ast)

        if errors:
            print(f"Found {len(errors)} semantic error(s):\n")
            for err in errors:
                print(f"  {err}")
        else:
            print("Semantic analysis passed — no errors found!")

    except (LexerError, ParseError) as e:
        print(f"Error: {e}")
