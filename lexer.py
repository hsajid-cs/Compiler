"""
Phase 1: Lexical Analyzer (Tokenizer)
Scans source code character-by-character and produces a stream of tokens.
Each token carries its line and column number for error reporting.
"""

from enum import Enum, auto


# ── Token Types ──────────────────────────────────────────────────────────────

class TokenType(Enum):
    # Keywords
    INT     = auto()
    FLOAT   = auto()
    CHAR    = auto()
    VOID    = auto()
    IF      = auto()
    ELSE    = auto()
    WHILE   = auto()
    DO      = auto()
    FOR     = auto()
    RETURN  = auto()

    # Literals and identifiers
    IDENT     = auto()
    INT_LIT   = auto()
    FLOAT_LIT = auto()
    CHAR_LIT  = auto()

    # Arithmetic operators
    PLUS    = auto()   # +
    MINUS   = auto()   # -
    STAR    = auto()   # *
    SLASH   = auto()   # /
    PERCENT = auto()   # %

    # Relational operators
    LT  = auto()   # <
    GT  = auto()   # >
    LE  = auto()   # <=
    GE  = auto()   # >=
    EQ  = auto()   # ==
    NEQ = auto()   # !=

    # Logical operators
    AND = auto()   # &&
    OR  = auto()   # ||
    NOT = auto()   # !

    # Assignment and delimiters
    ASSIGN  = auto()   # =
    LPAREN  = auto()   # (
    RPAREN  = auto()   # )
    LBRACE  = auto()   # {
    RBRACE  = auto()   # }
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    SEMI    = auto()   # ;
    COMMA   = auto()   # ,

    # Special
    EOF = auto()


# ── Token ────────────────────────────────────────────────────────────────────

class Token:
    """A single token with its type, raw value, and source location."""

    def __init__(self, type: TokenType, value, line: int, column: int):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.column})"


# ── Keyword map ──────────────────────────────────────────────────────────────

KEYWORDS = {
    "int":    TokenType.INT,
    "float":  TokenType.FLOAT,
    "char":   TokenType.CHAR,
    "void":   TokenType.VOID,
    "if":     TokenType.IF,
    "else":   TokenType.ELSE,
    "while":  TokenType.WHILE,
    "do":     TokenType.DO,
    "for":    TokenType.FOR,
    "return": TokenType.RETURN,
}

# Single-character tokens (no ambiguity)
SIMPLE_TOKENS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "%": TokenType.PERCENT,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    ";": TokenType.SEMI,
    ",": TokenType.COMMA,
}


# ── Lexer Error ──────────────────────────────────────────────────────────────

class LexerError(Exception):
    """A friendly error from the lexer, always includes line and column."""

    def __init__(self, message, line, column):
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, Col {column}: {message}")


# ── Lexer ────────────────────────────────────────────────────────────────────

class Lexer:
    """
    Character-by-character scanner.
    Usage:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()   # returns list of Token
    """

    def __init__(self, source: str):
        self.source = source
        self.pos = 0          # current index into source
        self.line = 1         # current line (1-indexed)
        self.column = 1       # current column (1-indexed)
        self.tokens = []

    # ── Helpers ──────────────────────────────────────────────────────────

    def _current(self) -> str | None:
        """Return current character, or None if at end."""
        if self.pos < len(self.source):
            return self.source[self.pos]
        return None

    def _peek(self) -> str | None:
        """Return next character without consuming it."""
        if self.pos + 1 < len(self.source):
            return self.source[self.pos + 1]
        return None

    def _advance(self) -> str:
        """Consume and return the current character, updating line/col."""
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _error(self, message: str):
        raise LexerError(message, self.line, self.column)

    # ── Skip whitespace and comments ─────────────────────────────────────

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self._current()

            # Whitespace
            if ch in " \t\r\n":
                self._advance()
                continue

            # Single-line comment: //
            if ch == "/" and self._peek() == "/":
                self._advance()  # skip first /
                self._advance()  # skip second /
                while self.pos < len(self.source) and self._current() != "\n":
                    self._advance()
                continue

            # Multi-line comment: /* ... */
            if ch == "/" and self._peek() == "*":
                start_line = self.line
                start_col = self.column
                self._advance()  # skip /
                self._advance()  # skip *
                while self.pos < len(self.source):
                    if self._current() == "*" and self._peek() == "/":
                        self._advance()  # skip *
                        self._advance()  # skip /
                        break
                    self._advance()
                else:
                    raise LexerError(
                        "Unterminated comment! You opened a '/*' comment here but never closed it with '*/'.",
                        start_line, start_col
                    )
                continue

            break  # not whitespace, not comment — stop

    # ── Number literals ──────────────────────────────────────────────────

    def _read_number(self) -> Token:
        """Read an integer or float literal."""
        start_col = self.column
        num_str = ""
        is_float = False

        while self.pos < len(self.source) and (self._current().isdigit() or self._current() == "."):
            if self._current() == ".":
                if is_float:
                    self._error("Unexpected second '.' in number literal. Numbers can only have one decimal point.")
                is_float = True
            num_str += self._advance()

        if is_float:
            return Token(TokenType.FLOAT_LIT, float(num_str), self.line, start_col)
        else:
            return Token(TokenType.INT_LIT, int(num_str), self.line, start_col)

    # ── Character literals ───────────────────────────────────────────────

    def _read_char_literal(self) -> Token:
        """Read a character literal like 'a' or '\\n'."""
        start_col = self.column
        self._advance()  # skip opening quote

        if self._current() is None:
            self._error("Unexpected end of file inside a character literal. Did you forget the closing quote?")

        if self._current() == "\\":
            # Escape sequence
            self._advance()  # skip backslash
            escape_map = {"n": "\n", "t": "\t", "\\": "\\", "'": "'", "0": "\0"}
            ch = self._current()
            if ch in escape_map:
                value = escape_map[ch]
                self._advance()
            else:
                self._error(f"Unknown escape sequence '\\{ch}'. Supported: \\n, \\t, \\\\, \\', \\0")
        else:
            value = self._advance()

        if self._current() != "'":
            self._error("Character literal must be exactly one character (or escape sequence). Close it with a single quote.")
        self._advance()  # skip closing quote

        return Token(TokenType.CHAR_LIT, value, self.line, start_col)

    # ── Identifiers and keywords ─────────────────────────────────────────

    def _read_identifier_or_keyword(self) -> Token:
        start_col = self.column
        word = ""

        while self.pos < len(self.source) and (self._current().isalnum() or self._current() == "_"):
            word += self._advance()

        # Check if it's a keyword
        if word in KEYWORDS:
            return Token(KEYWORDS[word], word, self.line, start_col)
        else:
            return Token(TokenType.IDENT, word, self.line, start_col)

    # ── Main tokenize loop ───────────────────────────────────────────────

    def tokenize(self) -> list:
        """Scan the entire source and return a list of tokens (ending with EOF)."""
        self.tokens = []

        while True:
            self._skip_whitespace_and_comments()

            if self.pos >= len(self.source):
                self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
                break

            ch = self._current()
            col = self.column

            # ── Simple single-character tokens ───────────────────────
            if ch in SIMPLE_TOKENS:
                self._advance()
                self.tokens.append(Token(SIMPLE_TOKENS[ch], ch, self.line, col))
                continue

            # ── Two-character and ambiguous operators ────────────────
            if ch == "=":
                self._advance()
                if self._current() == "=":
                    self._advance()
                    self.tokens.append(Token(TokenType.EQ, "==", self.line, col))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, "=", self.line, col))
                continue

            if ch == "!":
                self._advance()
                if self._current() == "=":
                    self._advance()
                    self.tokens.append(Token(TokenType.NEQ, "!=", self.line, col))
                else:
                    self.tokens.append(Token(TokenType.NOT, "!", self.line, col))
                continue

            if ch == "<":
                self._advance()
                if self._current() == "=":
                    self._advance()
                    self.tokens.append(Token(TokenType.LE, "<=", self.line, col))
                else:
                    self.tokens.append(Token(TokenType.LT, "<", self.line, col))
                continue

            if ch == ">":
                self._advance()
                if self._current() == "=":
                    self._advance()
                    self.tokens.append(Token(TokenType.GE, ">=", self.line, col))
                else:
                    self.tokens.append(Token(TokenType.GT, ">", self.line, col))
                continue

            if ch == "&":
                self._advance()
                if self._current() == "&":
                    self._advance()
                    self.tokens.append(Token(TokenType.AND, "&&", self.line, col))
                else:
                    self._error("Did you mean '&&' (logical AND)? A single '&' (bitwise AND) isn't supported in this language.")
                continue

            if ch == "|":
                self._advance()
                if self._current() == "|":
                    self._advance()
                    self.tokens.append(Token(TokenType.OR, "||", self.line, col))
                else:
                    self._error("Did you mean '||' (logical OR)? A single '|' (bitwise OR) isn't supported in this language.")
                continue

            if ch == "/":
                # Not a comment (those were handled in skip), so it's division
                self._advance()
                self.tokens.append(Token(TokenType.SLASH, "/", self.line, col))
                continue

            # ── Numbers ──────────────────────────────────────────────
            if ch.isdigit():
                self.tokens.append(self._read_number())
                continue

            # ── Character literals ───────────────────────────────────
            if ch == "'":
                self.tokens.append(self._read_char_literal())
                continue

            # ── Identifiers / keywords ───────────────────────────────
            if ch.isalpha() or ch == "_":
                self.tokens.append(self._read_identifier_or_keyword())
                continue

            # ── Unknown character ────────────────────────────────────
            self._error(f"Unexpected character '{ch}'. I don't know what to do with this!")

        return self.tokens


# ── Standalone test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        # Quick inline test
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
        print("=== Lexer Test: Fibonacci ===")
        print(f"Source:\n{test_code}")
    else:
        with open(sys.argv[1], "r") as f:
            test_code = f.read()

    lexer = Lexer(test_code)
    try:
        tokens = lexer.tokenize()
        print("=== Tokens ===")
        for tok in tokens:
            print(f"  {tok}")
        print(f"\nTotal: {len(tokens)} tokens (including EOF)")
    except LexerError as e:
        print(f"Lexer Error: {e}")
