"""
Phase 2: Parser (Recursive Descent + Pratt-style Precedence Climbing)
Transforms a token stream into an Abstract Syntax Tree.
Uses binding powers for operator precedence instead of one function per level.
"""

from lexer import Lexer, Token, TokenType, LexerError
from ast_nodes import *


# ── Parser Error ─────────────────────────────────────────────────────────────

class ParseError(Exception):
    """A friendly error from the parser."""

    def __init__(self, message, line):
        self.line = line
        super().__init__(f"Line {line}: {message}")


# ── Binding Power Table (Pratt-style) ───────────────────────────────────────
# Higher number = tighter binding.
# Each entry: token_type → (left_bp, right_bp)
# Left-associative: right_bp = left_bp + 1
# Right-associative: right_bp = left_bp

BINDING_POWER = {
    TokenType.OR:      (10, 11),
    TokenType.AND:     (20, 21),
    TokenType.EQ:      (30, 31),
    TokenType.NEQ:     (30, 31),
    TokenType.LT:      (40, 41),
    TokenType.GT:      (40, 41),
    TokenType.LE:      (40, 41),
    TokenType.GE:      (40, 41),
    TokenType.PLUS:    (50, 51),
    TokenType.MINUS:   (50, 51),
    TokenType.STAR:    (60, 61),
    TokenType.SLASH:   (60, 61),
    TokenType.PERCENT: (60, 61),
}

# Map token types to their string operators for AST nodes
OP_SYMBOLS = {
    TokenType.PLUS: "+", TokenType.MINUS: "-", TokenType.STAR: "*",
    TokenType.SLASH: "/", TokenType.PERCENT: "%",
    TokenType.LT: "<", TokenType.GT: ">", TokenType.LE: "<=",
    TokenType.GE: ">=", TokenType.EQ: "==", TokenType.NEQ: "!=",
    TokenType.AND: "&&", TokenType.OR: "||",
}


# ── Parser ───────────────────────────────────────────────────────────────────

class Parser:
    """
    Recursive descent parser with Pratt-style expression parsing.
    Usage:
        parser = Parser(tokens)
        ast = parser.parse()
    """

    def __init__(self, tokens: list):
        self.tokens = tokens
        self.pos = 0

    # ── Token helpers ────────────────────────────────────────────────────

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self) -> Token:
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return self.tokens[-1]  # EOF

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _expect(self, token_type: TokenType, hint: str = "") -> Token:
        """Consume a token of the expected type, or raise a friendly error."""
        tok = self._current()
        if tok.type != token_type:
            expected = token_type.name
            got = tok.type.name
            msg = f"Expected {expected} but found {got} ('{tok.value}')."
            if hint:
                msg += f" {hint}"
            raise ParseError(msg, tok.line)
        return self._advance()

    def _match(self, *types) -> Token | None:
        """If the current token matches one of the types, consume and return it."""
        if self._current().type in types:
            return self._advance()
        return None

    def _at(self, *types) -> bool:
        """Check if the current token is one of the given types (without consuming)."""
        return self._current().type in types

    def _is_type_keyword(self) -> bool:
        return self._current().type in (TokenType.INT, TokenType.FLOAT, TokenType.CHAR, TokenType.VOID)

    # ── Program ──────────────────────────────────────────────────────────

    def parse(self) -> Program:
        """Parse the entire program: a sequence of function definitions."""
        program = Program()
        while not self._at(TokenType.EOF):
            program.functions.append(self._parse_function_def())
        return program

    # ── Function definition ──────────────────────────────────────────────

    def _parse_function_def(self) -> FuncDef:
        """Parse: type name(params) { body }"""
        type_tok = self._advance()
        line = type_tok.line

        if type_tok.type not in (TokenType.INT, TokenType.FLOAT, TokenType.CHAR, TokenType.VOID):
            raise ParseError(
                f"Expected a type (int, float, char, void) at the start of a function definition, "
                f"but found '{type_tok.value}'.",
                type_tok.line,
            )

        name_tok = self._expect(TokenType.IDENT, "This should be the function name.")
        self._expect(TokenType.LPAREN, "Function parameters should start with '('.")

        # Parse parameter list
        params = []
        if not self._at(TokenType.RPAREN):
            params = self._parse_params()

        self._expect(TokenType.RPAREN, "Did you forget to close the parameter list with ')'?")

        body = self._parse_block()

        return FuncDef(
            ret_type=type_tok.value,
            name=name_tok.value,
            params=params,
            body=body,
            line=line,
        )

    def _parse_params(self) -> list:
        """Parse: type name, type name, ..."""
        params = []
        while True:
            type_tok = self._advance()
            if type_tok.type not in (TokenType.INT, TokenType.FLOAT, TokenType.CHAR):
                raise ParseError(
                    f"Expected a parameter type (int, float, char) but found '{type_tok.value}'.",
                    type_tok.line,
                )
            name_tok = self._expect(TokenType.IDENT, "Each parameter needs a name after its type.")
            params.append(Param(param_type=type_tok.value, name=name_tok.value, line=type_tok.line))

            if not self._match(TokenType.COMMA):
                break
        return params

    # ── Block ────────────────────────────────────────────────────────────

    def _parse_block(self) -> Block:
        """Parse: { statement* }"""
        lbrace = self._expect(TokenType.LBRACE, "Expected '{' to start a block.")
        block = Block(line=lbrace.line)

        while not self._at(TokenType.RBRACE) and not self._at(TokenType.EOF):
            block.statements.append(self._parse_statement())

        self._expect(TokenType.RBRACE, "Expected '}' to close the block. Did you forget a closing brace?")
        return block

    # ── Statement ────────────────────────────────────────────────────────

    def _parse_statement(self):
        """Dispatch to the right statement parser based on current token."""
        tok = self._current()

        # Block
        if tok.type == TokenType.LBRACE:
            return self._parse_block()

        # Variable / array declaration
        if tok.type in (TokenType.INT, TokenType.FLOAT, TokenType.CHAR):
            return self._parse_declaration()

        # If
        if tok.type == TokenType.IF:
            return self._parse_if()

        # While
        if tok.type == TokenType.WHILE:
            return self._parse_while()

        # Do-while
        if tok.type == TokenType.DO:
            return self._parse_do_while()

        # For
        if tok.type == TokenType.FOR:
            return self._parse_for()

        # Return
        if tok.type == TokenType.RETURN:
            return self._parse_return()

        # Assignment or expression statement (function call, etc.)
        if tok.type == TokenType.IDENT:
            return self._parse_assignment_or_expr_stmt()

        raise ParseError(
            f"Unexpected token '{tok.value}'. I was expecting a statement "
            f"(variable declaration, if, while, return, etc.).",
            tok.line,
        )

    # ── Declaration ──────────────────────────────────────────────────────

    def _parse_declaration(self):
        """Parse: type name [= expr] ; or type name[size] ;"""
        type_tok = self._advance()
        name_tok = self._expect(TokenType.IDENT, "Expected a variable name after the type.")
        line = type_tok.line

        # Array declaration: int arr[10];
        if self._match(TokenType.LBRACKET):
            size_tok = self._expect(TokenType.INT_LIT, "Array size must be an integer literal.")
            self._expect(TokenType.RBRACKET, "Expected ']' after array size.")
            self._expect(TokenType.SEMI, "Don't forget the ';' after an array declaration!")
            return ArrayDecl(var_type=type_tok.value, name=name_tok.value, size=size_tok.value, line=line)

        # Variable declaration with optional initializer
        init_expr = None
        if self._match(TokenType.ASSIGN):
            init_expr = self._parse_expression()

        self._expect(TokenType.SEMI, "Don't forget the ';' after a variable declaration!")
        return VarDecl(var_type=type_tok.value, name=name_tok.value, init_expr=init_expr, line=line)

    # ── Assignment or expression statement ───────────────────────────────

    def _parse_assignment_or_expr_stmt(self):
        """
        Starts with IDENT. Could be:
          - x = expr ;          (assignment)
          - arr[idx] = expr ;   (array assignment)
          - func(args) ;        (expression statement / function call)
        """
        name_tok = self._advance()  # consume the IDENT
        line = name_tok.line

        # Array assignment: arr[idx] = expr;
        if self._match(TokenType.LBRACKET):
            index = self._parse_expression()
            self._expect(TokenType.RBRACKET, "Expected ']' after array index.")
            self._expect(TokenType.ASSIGN, "Expected '=' for array element assignment.")
            expr = self._parse_expression()
            self._expect(TokenType.SEMI, "Don't forget the ';' after assignment!")
            return ArrayAssignment(name=name_tok.value, index=index, expr=expr, line=line)

        # Simple assignment: x = expr;
        if self._match(TokenType.ASSIGN):
            expr = self._parse_expression()
            self._expect(TokenType.SEMI, "Don't forget the ';' after assignment!")
            return Assignment(name=name_tok.value, expr=expr, line=line)

        # Otherwise it's an expression statement — backtrack and parse as expression
        # We already consumed the IDENT, so we need to "un-consume" it.
        self.pos -= 1  # backtrack
        expr = self._parse_expression()
        self._expect(TokenType.SEMI, "Don't forget the ';' after a statement!")
        return ExpressionStmt(expr=expr, line=line)

    # ── Control flow ─────────────────────────────────────────────────────

    def _parse_if(self) -> IfStmt:
        """Parse: if (expr) statement [else statement]"""
        tok = self._advance()  # consume 'if'
        self._expect(TokenType.LPAREN, "An 'if' needs a '(' before the condition.")
        cond = self._parse_expression()
        self._expect(TokenType.RPAREN, "An 'if' needs a ')' after the condition.")

        then_branch = self._parse_statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self._parse_statement()

        return IfStmt(condition=cond, then_branch=then_branch, else_branch=else_branch, line=tok.line)

    def _parse_while(self) -> WhileStmt:
        """Parse: while (expr) statement"""
        tok = self._advance()  # consume 'while'
        self._expect(TokenType.LPAREN, "A 'while' needs a '(' before the condition.")
        cond = self._parse_expression()
        self._expect(TokenType.RPAREN, "A 'while' needs a ')' after the condition.")
        body = self._parse_statement()
        return WhileStmt(condition=cond, body=body, line=tok.line)

    def _parse_do_while(self) -> DoWhileStmt:
        """Parse: do statement while (expr) ;"""
        tok = self._advance()  # consume 'do'
        body = self._parse_statement()
        self._expect(TokenType.WHILE, "A 'do' block must be followed by 'while'.")
        self._expect(TokenType.LPAREN, "Expected '(' after 'while' in do-while.")
        cond = self._parse_expression()
        self._expect(TokenType.RPAREN, "Expected ')' after condition in do-while.")
        self._expect(TokenType.SEMI, "A do-while statement ends with ';'.")
        return DoWhileStmt(body=body, condition=cond, line=tok.line)

    def _parse_for(self) -> ForStmt:
        """Parse: for (init; cond; update) statement"""
        tok = self._advance()  # consume 'for'
        self._expect(TokenType.LPAREN, "A 'for' needs a '(' after the keyword.")

        # Init: declaration, assignment, or empty
        init = None
        if self._at(TokenType.INT, TokenType.FLOAT, TokenType.CHAR):
            init = self._parse_declaration()  # already consumes ';'
        elif self._at(TokenType.IDENT):
            name_tok = self._advance()
            self._expect(TokenType.ASSIGN, "Expected '=' in for-loop initializer.")
            expr = self._parse_expression()
            self._expect(TokenType.SEMI, "Expected ';' after for-loop initializer.")
            init = Assignment(name=name_tok.value, expr=expr, line=name_tok.line)
        else:
            self._expect(TokenType.SEMI, "Expected ';' for empty for-loop initializer.")

        # Condition (optional)
        cond = None
        if not self._at(TokenType.SEMI):
            cond = self._parse_expression()
        self._expect(TokenType.SEMI, "Expected ';' after for-loop condition.")

        # Update (optional)
        update = None
        if not self._at(TokenType.RPAREN):
            name_tok = self._expect(TokenType.IDENT, "Expected variable name in for-loop update.")
            self._expect(TokenType.ASSIGN, "Expected '=' in for-loop update.")
            expr = self._parse_expression()
            update = Assignment(name=name_tok.value, expr=expr, line=name_tok.line)

        self._expect(TokenType.RPAREN, "Expected ')' to close the for-loop header.")
        body = self._parse_statement()

        return ForStmt(init=init, condition=cond, update=update, body=body, line=tok.line)

    def _parse_return(self) -> ReturnStmt:
        """Parse: return [expr] ;"""
        tok = self._advance()  # consume 'return'
        expr = None
        if not self._at(TokenType.SEMI):
            expr = self._parse_expression()
        self._expect(TokenType.SEMI, "Don't forget the ';' after return!")
        return ReturnStmt(expr=expr, line=tok.line)

    # ── Expression parsing (Pratt / precedence climbing) ─────────────────

    def _parse_expression(self, min_bp=0):
        """
        Pratt-style precedence climbing.
        min_bp: minimum binding power — operators with lower binding power won't be consumed.
        """
        left = self._parse_prefix()

        while True:
            tok = self._current()
            if tok.type not in BINDING_POWER:
                break

            left_bp, right_bp = BINDING_POWER[tok.type]
            if left_bp < min_bp:
                break

            op_tok = self._advance()
            right = self._parse_expression(right_bp)
            left = BinOp(op=OP_SYMBOLS[op_tok.type], left=left, right=right, line=op_tok.line)

        return left

    def _parse_prefix(self):
        """Parse a prefix expression: literal, ident, func call, unary op, or grouped expr."""
        tok = self._current()

        # Unary minus
        if tok.type == TokenType.MINUS:
            op_tok = self._advance()
            operand = self._parse_prefix()
            return UnaryOp(op="-", operand=operand, line=op_tok.line)

        # Logical NOT
        if tok.type == TokenType.NOT:
            op_tok = self._advance()
            operand = self._parse_prefix()
            return UnaryOp(op="!", operand=operand, line=op_tok.line)

        # Grouped expression: (expr)
        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN, "Missing closing ')' in grouped expression.")
            return expr

        # Integer literal
        if tok.type == TokenType.INT_LIT:
            self._advance()
            return Literal(value=tok.value, lit_type="int", line=tok.line)

        # Float literal
        if tok.type == TokenType.FLOAT_LIT:
            self._advance()
            return Literal(value=tok.value, lit_type="float", line=tok.line)

        # Character literal
        if tok.type == TokenType.CHAR_LIT:
            self._advance()
            return Literal(value=tok.value, lit_type="char", line=tok.line)

        # Identifier, function call, or array access
        if tok.type == TokenType.IDENT:
            self._advance()

            # Function call: name(args)
            if self._at(TokenType.LPAREN):
                self._advance()  # consume '('
                args = []
                if not self._at(TokenType.RPAREN):
                    args.append(self._parse_expression())
                    while self._match(TokenType.COMMA):
                        args.append(self._parse_expression())
                self._expect(TokenType.RPAREN, f"Expected ')' to close function call to '{tok.value}'.")
                return FuncCall(name=tok.value, args=args, line=tok.line)

            # Array access: name[index]
            if self._at(TokenType.LBRACKET):
                self._advance()  # consume '['
                index = self._parse_expression()
                self._expect(TokenType.RBRACKET, f"Expected ']' after array index for '{tok.value}'.")
                return ArrayAccess(name=tok.value, index=index, line=tok.line)

            return Identifier(name=tok.value, line=tok.line)

        raise ParseError(
            f"Unexpected token '{tok.value}' ({tok.type.name}). I was expecting a value "
            f"(number, variable, function call, or '(' expression ')').",
            tok.line,
        )


# ── Standalone test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

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
        print("=== Parser Test: Fibonacci ===\n")
    else:
        with open(sys.argv[1], "r") as f:
            test_code = f.read()

    try:
        lexer = Lexer(test_code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        pretty_print(ast)
    except (LexerError, ParseError) as e:
        print(f"Error: {e}")
