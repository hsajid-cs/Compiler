"""
Compiler Driver
Chains all four phases: Lexer → Parser → Semantic Analysis → TAC Generation
Run: python compiler.py <source_file.c> [--phase lexer|parser|semantic|tac]
"""

import sys
from lexer import Lexer, LexerError
from parser import Parser, ParseError
from semantic import SemanticAnalyzer
from tac_generator import TACGenerator
from ast_nodes import pretty_print


def compile_file(source_code: str, phase: str = "tac", filename: str = "<stdin>"):
    """
    Run the compiler pipeline up to the given phase.
    phase: 'lexer', 'parser', 'semantic', or 'tac'
    """
    print(f"=== Compiling: {filename} ===\n")

    # ── Phase 1: Lexical Analysis ────────────────────────────────────────
    print("-- Phase 1: Lexical Analysis --")
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        print(f"   [OK] Tokenized successfully -- {len(tokens)} tokens\n")
    except LexerError as e:
        print(f"   [FAIL] Lexer Error: {e}\n")
        return False

    if phase == "lexer":
        print("-- Tokens --")
        for tok in tokens:
            print(f"   {tok}")
        return True

    # ── Phase 2: Parsing ─────────────────────────────────────────────────
    print("-- Phase 2: Parsing --")
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        print(f"   [OK] Parsed successfully -- AST built\n")
    except ParseError as e:
        print(f"   [FAIL] Parse Error: {e}\n")
        return False

    if phase == "parser":
        print("-- Abstract Syntax Tree --")
        pretty_print(ast)
        return True

    # ── Phase 3: Semantic Analysis ───────────────────────────────────────
    print("-- Phase 3: Semantic Analysis --")
    analyzer = SemanticAnalyzer()
    errors = analyzer.analyze(ast)

    if errors:
        print(f"   [FAIL] Found {len(errors)} error(s):\n")
        for err in errors:
            print(f"      {err}")
        print()
        return False
    else:
        print(f"   [OK] Semantic analysis passed -- no errors\n")

    if phase == "semantic":
        return True

    # ── Phase 4: Three Address Code Generation ───────────────────────────
    print("-- Phase 4: Three Address Code --")
    gen = TACGenerator()
    instructions = gen.generate(ast)
    print(f"   [OK] Generated {len(instructions)} TAC instructions\n")

    print("-- Three Address Code Output --")
    for instr in instructions:
        print(f"   {instr}")
    print()

    return True


def main():
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python compiler.py <source_file.c> [--phase lexer|parser|semantic|tac]")
        print()
        print("Phases:")
        print("  lexer     -- Tokenize and show all tokens")
        print("  parser    -- Parse and show the AST")
        print("  semantic  -- Run semantic analysis (type/scope checking)")
        print("  tac       -- Generate Three Address Code (default)")
        sys.exit(1)

    filename = sys.argv[1]
    phase = "tac"  # default

    if "--phase" in sys.argv:
        idx = sys.argv.index("--phase")
        if idx + 1 < len(sys.argv):
            phase = sys.argv[idx + 1]
            if phase not in ("lexer", "parser", "semantic", "tac"):
                print(f"Unknown phase '{phase}'. Use: lexer, parser, semantic, or tac")
                sys.exit(1)

    try:
        with open(filename, "r") as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)

    success = compile_file(source_code, phase, filename)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
