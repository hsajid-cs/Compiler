"""
Phase 4: Three Address Code (TAC) Generator
Walks the AST and produces a flat list of three-address instructions.

TAC format:
    t1 = a + b            (binary op)
    t2 = -a               (unary op)
    t3 = a                (copy)
    if t1 goto L1         (conditional jump)
    goto L2               (unconditional jump)
    L1:                   (label)
    param x               (push function argument)
    t4 = call func, 2     (function call with 2 args)
    return t1             (return from function)
    arr[t1] = t2          (array store)
    t3 = arr[t1]          (array load)
"""

from ast_nodes import *


# ── TAC Instruction ──────────────────────────────────────────────────────────

class TACInstruction:
    """A single three-address code instruction."""

    def __init__(self, op, result=None, arg1=None, arg2=None):
        self.op = op          # operation type string
        self.result = result  # destination (temp or var name)
        self.arg1 = arg1      # first operand
        self.arg2 = arg2      # second operand (or None)

    def __repr__(self):
        if self.op == "label":
            return f"{self.arg1}:"
        elif self.op == "goto":
            return f"    goto {self.arg1}"
        elif self.op == "if_goto":
            return f"    if {self.arg1} goto {self.arg2}"
        elif self.op == "if_false_goto":
            return f"    ifFalse {self.arg1} goto {self.arg2}"
        elif self.op == "param":
            return f"    param {self.arg1}"
        elif self.op == "call":
            if self.result:
                return f"    {self.result} = call {self.arg1}, {self.arg2}"
            else:
                return f"    call {self.arg1}, {self.arg2}"
        elif self.op == "return":
            if self.arg1 is not None:
                return f"    return {self.arg1}"
            else:
                return f"    return"
        elif self.op == "assign":
            return f"    {self.result} = {self.arg1}"
        elif self.op == "binop":
            return f"    {self.result} = {self.arg1} {self.arg2}"
        elif self.op == "unary":
            return f"    {self.result} = {self.arg1}"
        elif self.op == "array_store":
            return f"    {self.result}[{self.arg1}] = {self.arg2}"
        elif self.op == "array_load":
            return f"    {self.result} = {self.arg1}[{self.arg2}]"
        elif self.op == "func_begin":
            return f"\n{self.arg1}:"
        elif self.op == "func_end":
            return f"    end {self.arg1}"
        elif self.op == "decl":
            return f"    declare {self.arg1}"
        elif self.op == "array_decl":
            return f"    declare {self.arg1}[{self.arg2}]"
        elif self.op == "print":
            return f"    print {self.arg1}"
        elif self.op == "read":
            return f"    {self.result} = read"
        else:
            return f"    {self.op} {self.result} {self.arg1} {self.arg2}"


# ── TAC Generator ───────────────────────────────────────────────────────────

class TACGenerator:
    """
    Usage:
        gen = TACGenerator()
        instructions = gen.generate(ast)
        for instr in instructions:
            print(instr)
    """

    def __init__(self):
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0

    def _new_temp(self) -> str:
        """Generate a fresh temporary variable name."""
        name = f"t{self.temp_counter}"
        self.temp_counter += 1
        return name

    def _new_label(self) -> str:
        """Generate a fresh label name."""
        name = f"L{self.label_counter}"
        self.label_counter += 1
        return name

    def _emit(self, op, result=None, arg1=None, arg2=None):
        """Append a TAC instruction."""
        self.instructions.append(TACInstruction(op, result, arg1, arg2))

    # ── Main entry ───────────────────────────────────────────────────────

    def generate(self, program: Program) -> list:
        """Generate TAC for the entire program."""
        self.instructions = []
        for func in program.functions:
            self._gen_func(func)
        return self.instructions

    # ── Function ─────────────────────────────────────────────────────────

    def _gen_func(self, func: FuncDef):
        self._emit("func_begin", arg1=func.name)

        # Declare parameters
        for param in func.params:
            self._emit("decl", arg1=f"{param.param_type} {param.name}")

        self._gen_block(func.body)
        self._emit("func_end", arg1=func.name)

    # ── Block ────────────────────────────────────────────────────────────

    def _gen_block(self, block: Block):
        for stmt in block.statements:
            self._gen_statement(stmt)

    # ── Statements ───────────────────────────────────────────────────────

    def _gen_statement(self, stmt):
        if isinstance(stmt, VarDecl):
            self._gen_var_decl(stmt)
        elif isinstance(stmt, ArrayDecl):
            self._gen_array_decl(stmt)
        elif isinstance(stmt, Assignment):
            self._gen_assignment(stmt)
        elif isinstance(stmt, ArrayAssignment):
            self._gen_array_assignment(stmt)
        elif isinstance(stmt, IfStmt):
            self._gen_if(stmt)
        elif isinstance(stmt, WhileStmt):
            self._gen_while(stmt)
        elif isinstance(stmt, DoWhileStmt):
            self._gen_do_while(stmt)
        elif isinstance(stmt, ForStmt):
            self._gen_for(stmt)
        elif isinstance(stmt, ReturnStmt):
            self._gen_return(stmt)
        elif isinstance(stmt, ExpressionStmt):
            self._gen_expr_stmt(stmt)
        elif isinstance(stmt, Block):
            self._gen_block(stmt)

    def _gen_var_decl(self, decl: VarDecl):
        if decl.init_expr:
            temp = self._gen_expr(decl.init_expr)
            self._emit("assign", result=decl.name, arg1=temp)
        else:
            self._emit("decl", arg1=f"{decl.var_type} {decl.name}")

    def _gen_array_decl(self, decl: ArrayDecl):
        self._emit("array_decl", arg1=decl.name, arg2=decl.size)

    def _gen_assignment(self, stmt: Assignment):
        temp = self._gen_expr(stmt.expr)
        self._emit("assign", result=stmt.name, arg1=temp)

    def _gen_array_assignment(self, stmt: ArrayAssignment):
        idx_temp = self._gen_expr(stmt.index)
        val_temp = self._gen_expr(stmt.expr)
        self._emit("array_store", result=stmt.name, arg1=idx_temp, arg2=val_temp)

    # ── Control flow ─────────────────────────────────────────────────────

    def _gen_if(self, stmt: IfStmt):
        cond_temp = self._gen_expr(stmt.condition)

        if stmt.else_branch:
            else_label = self._new_label()
            end_label = self._new_label()

            self._emit("if_false_goto", arg1=cond_temp, arg2=else_label)
            self._gen_statement(stmt.then_branch)
            self._emit("goto", arg1=end_label)
            self._emit("label", arg1=else_label)
            self._gen_statement(stmt.else_branch)
            self._emit("label", arg1=end_label)
        else:
            end_label = self._new_label()
            self._emit("if_false_goto", arg1=cond_temp, arg2=end_label)
            self._gen_statement(stmt.then_branch)
            self._emit("label", arg1=end_label)

    def _gen_while(self, stmt: WhileStmt):
        start_label = self._new_label()
        end_label = self._new_label()

        self._emit("label", arg1=start_label)
        cond_temp = self._gen_expr(stmt.condition)
        self._emit("if_false_goto", arg1=cond_temp, arg2=end_label)
        self._gen_statement(stmt.body)
        self._emit("goto", arg1=start_label)
        self._emit("label", arg1=end_label)

    def _gen_do_while(self, stmt: DoWhileStmt):
        start_label = self._new_label()

        self._emit("label", arg1=start_label)
        self._gen_statement(stmt.body)
        cond_temp = self._gen_expr(stmt.condition)
        self._emit("if_goto", arg1=cond_temp, arg2=start_label)

    def _gen_for(self, stmt: ForStmt):
        # for (init; cond; update) body
        # → init; L_start: if !cond goto L_end; body; update; goto L_start; L_end:
        if stmt.init:
            self._gen_statement(stmt.init)

        start_label = self._new_label()
        end_label = self._new_label()

        self._emit("label", arg1=start_label)
        if stmt.condition:
            cond_temp = self._gen_expr(stmt.condition)
            self._emit("if_false_goto", arg1=cond_temp, arg2=end_label)

        self._gen_statement(stmt.body)

        if stmt.update:
            self._gen_statement(stmt.update)

        self._emit("goto", arg1=start_label)
        self._emit("label", arg1=end_label)

    def _gen_return(self, stmt: ReturnStmt):
        if stmt.expr:
            temp = self._gen_expr(stmt.expr)
            self._emit("return", arg1=temp)
        else:
            self._emit("return")

    def _gen_expr_stmt(self, stmt: ExpressionStmt):
        self._gen_expr(stmt.expr)

    # ── Expression generation (returns the temp/var holding the result) ──

    def _gen_expr(self, expr) -> str:
        """Generate TAC for an expression. Returns the name of the temp/var holding the result."""

        if isinstance(expr, Literal):
            return str(expr.value)

        if isinstance(expr, Identifier):
            return expr.name

        if isinstance(expr, ArrayAccess):
            idx_temp = self._gen_expr(expr.index)
            result = self._new_temp()
            self._emit("array_load", result=result, arg1=expr.name, arg2=idx_temp)
            return result

        if isinstance(expr, BinOp):
            left = self._gen_expr(expr.left)
            right = self._gen_expr(expr.right)
            result = self._new_temp()
            self._emit("binop", result=result, arg1=left, arg2=f"{expr.op} {right}")
            return result

        if isinstance(expr, UnaryOp):
            operand = self._gen_expr(expr.operand)
            result = self._new_temp()
            self._emit("unary", result=result, arg1=f"{expr.op}{operand}")
            return result

        if isinstance(expr, FuncCall):
            return self._gen_func_call(expr)

        return "???"

    def _gen_func_call(self, call: FuncCall) -> str:
        """Generate TAC for a function call."""
        # Handle built-in print specially
        if call.name == "print":
            arg_temp = self._gen_expr(call.args[0])
            self._emit("print", arg1=arg_temp)
            return arg_temp

        # Handle built-in read specially
        if call.name == "read":
            result = self._new_temp()
            self._emit("read", result=result)
            return result

        # General function call
        arg_temps = []
        for arg in call.args:
            arg_temps.append(self._gen_expr(arg))

        for a in arg_temps:
            self._emit("param", arg1=a)

        result = self._new_temp()
        self._emit("call", result=result, arg1=call.name, arg2=len(call.args))
        return result


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
        print("=== TAC Generation Test: Fibonacci ===\n")
    else:
        with open(sys.argv[1], "r") as f:
            test_code = f.read()

    try:
        lexer = Lexer(test_code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()

        gen = TACGenerator()
        instructions = gen.generate(ast)

        print("=== Three Address Code ===")
        for instr in instructions:
            print(instr)

    except (LexerError, ParseError) as e:
        print(f"Error: {e}")
