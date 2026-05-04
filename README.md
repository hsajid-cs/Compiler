# C Subset Compiler

A compiler for a subset of the C programming language, written in Python.  
Implements all four core phases: **Lexer -> Parser -> Semantic Analysis -> Three Address Code**.

## Quick Start

```bash
# Run the full pipeline (all 4 phases)
python compiler.py tests/test_fibonacci.c

# Stop at a specific phase
python compiler.py tests/test_fibonacci.c --phase lexer
python compiler.py tests/test_fibonacci.c --phase parser
python compiler.py tests/test_fibonacci.c --phase semantic
python compiler.py tests/test_fibonacci.c --phase tac
```

## Supported Language Features

| Feature | Examples |
|---|---|
| Types | `int`, `float`, `char` |
| Variables | `int x = 5;` declarations anywhere in a block |
| Arrays | `int arr[10]; arr[0] = 42;` |
| Arithmetic | `+`, `-`, `*`, `/`, `%` |
| Relational | `<`, `>`, `<=`, `>=`, `==`, `!=` |
| Logical | `&&`, `\|\|`, `!` |
| Control flow | `if`/`else`, `while`, `do-while`, `for` |
| Functions | `int add(int a, int b) { return a + b; }` |
| I/O | `print(x)`, `read()` (built-in) |
| Comments | `// single-line` and `/* multi-line */` |

## Project Structure

```
lexer.py          -- Phase 1: Tokenizer (character-by-character scanner)
ast_nodes.py      -- AST node definitions (Python dataclasses)
parser.py         -- Phase 2: Recursive descent + Pratt precedence climbing
semantic.py       -- Phase 3: Type checking, scope management, symbol table
tac_generator.py  -- Phase 4: Three Address Code generation
compiler.py       -- Main driver (chains all phases)
tests/            -- Test programs
```

## Test Programs

| File | What it tests |
|---|---|
| `test_fibonacci.c` | Recursive Fibonacci -- functions, if/else, recursion |
| `test_bubblesort.c` | Bubble Sort -- arrays, nested while loops, swapping |
| `test_gcd.c` | GCD (Euclidean) -- do-while loop, modulo operator |
| `test_factorial.c` | Factorial -- for loop, iterative computation |
| `test_errors.c` | Intentional errors -- human-friendly error messages |
| `test_scoping.c` | Variable scoping -- nested blocks, shadowing |

## Design Choices

1. **Hand-written recursive descent parser** -- no parser generators (yacc, ANTLR). Every grammar rule is a readable Python method.

2. **Pratt-style precedence climbing** for expressions -- uses a binding power table instead of one function per precedence level. More elegant and extensible.

3. **Human-friendly error messages** with line numbers:
   ```
   Line 5: Hey, 'x' hasn't been declared yet. Did you forget something like 'int x;'?
   Line 8: Type mismatch -- you're initializing 'a' (int) with a float value.
   ```

4. **do-while loops** supported (uncommon in student compilers).

5. **C99-style declarations** -- variables can be declared anywhere in a block, not just at the top.

## Compiler Phases

### Phase 1: Lexer
Scans source character-by-character, producing tokens with line/column positions.
Handles single-line (`//`) and multi-line (`/* */`) comments.

### Phase 2: Parser
Builds an Abstract Syntax Tree (AST) using recursive descent.
Expression parsing uses Pratt-style precedence climbing with a binding power table.

### Phase 3: Semantic Analysis
- Symbol table with scope stack (supports nested scopes)
- Type checking (assignments, expressions, return types)
- Function signature verification (argument count)
- Forward function references (two-pass design)

### Phase 4: Three Address Code
Generates flat TAC instructions:
- Temporary variables (`t0`, `t1`, ...)
- Labels and gotos for control flow
- `param` / `call` for function calls
- `array_load` / `array_store` for arrays
