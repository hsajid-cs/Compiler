"""
AST Node Definitions
Simple Python dataclasses representing every node in our abstract syntax tree.
Each node carries a `line` number for error reporting in later phases.
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Top-level ────────────────────────────────────────────────────────────────

@dataclass
class Program:
    """Root of the AST — a program is a list of function definitions."""
    functions: list = field(default_factory=list)


# ── Functions ────────────────────────────────────────────────────────────────

@dataclass
class Param:
    """A single function parameter: type + name."""
    param_type: str    # "int", "float", "char"
    name: str
    line: int = 0

@dataclass
class FuncDef:
    """A function definition: return type, name, parameters, body block."""
    ret_type: str      # "int", "float", "char", "void"
    name: str
    params: list       # list of Param
    body: 'Block' = None
    line: int = 0


# ── Statements ───────────────────────────────────────────────────────────────

@dataclass
class Block:
    """A brace-enclosed block: { stmt1; stmt2; ... }"""
    statements: list = field(default_factory=list)
    line: int = 0

@dataclass
class VarDecl:
    """Variable declaration: int x; or int x = expr;"""
    var_type: str
    name: str
    init_expr: Optional['Expression'] = None
    line: int = 0

@dataclass
class ArrayDecl:
    """Array declaration: int arr[10];"""
    var_type: str
    name: str
    size: int = 0
    line: int = 0

@dataclass
class Assignment:
    """Simple assignment: x = expr;"""
    name: str
    expr: 'Expression' = None
    line: int = 0

@dataclass
class ArrayAssignment:
    """Array element assignment: arr[index] = expr;"""
    name: str
    index: 'Expression' = None
    expr: 'Expression' = None
    line: int = 0

@dataclass
class IfStmt:
    """if (cond) then_branch [else else_branch]"""
    condition: 'Expression' = None
    then_branch: 'Statement' = None
    else_branch: Optional['Statement'] = None
    line: int = 0

@dataclass
class WhileStmt:
    """while (cond) body"""
    condition: 'Expression' = None
    body: 'Statement' = None
    line: int = 0

@dataclass
class DoWhileStmt:
    """do body while (cond);"""
    body: 'Statement' = None
    condition: 'Expression' = None
    line: int = 0

@dataclass
class ForStmt:
    """for (init; cond; update) body"""
    init: Optional['Statement'] = None       # VarDecl or Assignment or None
    condition: Optional['Expression'] = None
    update: Optional['Assignment'] = None
    body: 'Statement' = None
    line: int = 0

@dataclass
class ReturnStmt:
    """return [expr];"""
    expr: Optional['Expression'] = None
    line: int = 0

@dataclass
class ExpressionStmt:
    """A standalone expression used as a statement (e.g., func call)."""
    expr: 'Expression' = None
    line: int = 0


# ── Expressions ──────────────────────────────────────────────────────────────

@dataclass
class BinOp:
    """Binary operation: left op right"""
    op: str            # "+", "-", "*", "/", "%", "<", ">", "<=", ">=", "==", "!=", "&&", "||"
    left: 'Expression' = None
    right: 'Expression' = None
    line: int = 0

@dataclass
class UnaryOp:
    """Unary operation: op operand (e.g., -x, !flag)"""
    op: str            # "-", "!"
    operand: 'Expression' = None
    line: int = 0

@dataclass
class Literal:
    """A literal value: integer, float, or character."""
    value: object      # int, float, or str (single char)
    lit_type: str      # "int", "float", "char"
    line: int = 0

@dataclass
class Identifier:
    """A variable reference by name."""
    name: str = ""
    line: int = 0

@dataclass
class ArrayAccess:
    """Array element access: arr[index]"""
    name: str = ""
    index: 'Expression' = None
    line: int = 0

@dataclass
class FuncCall:
    """Function call: name(arg1, arg2, ...)"""
    name: str = ""
    args: list = field(default_factory=list)
    line: int = 0


# ── Pretty printer ──────────────────────────────────────────────────────────

def pretty_print(node, indent=0):
    """Recursively print the AST in a human-readable tree format."""
    prefix = "  " * indent

    if isinstance(node, Program):
        print(f"{prefix}Program")
        for func in node.functions:
            pretty_print(func, indent + 1)

    elif isinstance(node, FuncDef):
        params_str = ", ".join(f"{p.param_type} {p.name}" for p in node.params)
        print(f"{prefix}FuncDef: {node.ret_type} {node.name}({params_str})  [line {node.line}]")
        pretty_print(node.body, indent + 1)

    elif isinstance(node, Block):
        print(f"{prefix}Block")
        for stmt in node.statements:
            pretty_print(stmt, indent + 1)

    elif isinstance(node, VarDecl):
        init = " = ..." if node.init_expr else ""
        print(f"{prefix}VarDecl: {node.var_type} {node.name}{init}  [line {node.line}]")
        if node.init_expr:
            pretty_print(node.init_expr, indent + 1)

    elif isinstance(node, ArrayDecl):
        print(f"{prefix}ArrayDecl: {node.var_type} {node.name}[{node.size}]  [line {node.line}]")

    elif isinstance(node, Assignment):
        print(f"{prefix}Assignment: {node.name} =  [line {node.line}]")
        pretty_print(node.expr, indent + 1)

    elif isinstance(node, ArrayAssignment):
        print(f"{prefix}ArrayAssignment: {node.name}[...] =  [line {node.line}]")
        pretty_print(node.index, indent + 1)
        pretty_print(node.expr, indent + 1)

    elif isinstance(node, IfStmt):
        print(f"{prefix}If  [line {node.line}]")
        print(f"{prefix}  Condition:")
        pretty_print(node.condition, indent + 2)
        print(f"{prefix}  Then:")
        pretty_print(node.then_branch, indent + 2)
        if node.else_branch:
            print(f"{prefix}  Else:")
            pretty_print(node.else_branch, indent + 2)

    elif isinstance(node, WhileStmt):
        print(f"{prefix}While  [line {node.line}]")
        print(f"{prefix}  Condition:")
        pretty_print(node.condition, indent + 2)
        print(f"{prefix}  Body:")
        pretty_print(node.body, indent + 2)

    elif isinstance(node, DoWhileStmt):
        print(f"{prefix}DoWhile  [line {node.line}]")
        print(f"{prefix}  Body:")
        pretty_print(node.body, indent + 2)
        print(f"{prefix}  Condition:")
        pretty_print(node.condition, indent + 2)

    elif isinstance(node, ForStmt):
        print(f"{prefix}For  [line {node.line}]")
        if node.init:
            print(f"{prefix}  Init:")
            pretty_print(node.init, indent + 2)
        if node.condition:
            print(f"{prefix}  Condition:")
            pretty_print(node.condition, indent + 2)
        if node.update:
            print(f"{prefix}  Update:")
            pretty_print(node.update, indent + 2)
        print(f"{prefix}  Body:")
        pretty_print(node.body, indent + 2)

    elif isinstance(node, ReturnStmt):
        print(f"{prefix}Return  [line {node.line}]")
        if node.expr:
            pretty_print(node.expr, indent + 1)

    elif isinstance(node, ExpressionStmt):
        print(f"{prefix}ExprStmt  [line {node.line}]")
        pretty_print(node.expr, indent + 1)

    elif isinstance(node, BinOp):
        print(f"{prefix}BinOp: {node.op}  [line {node.line}]")
        pretty_print(node.left, indent + 1)
        pretty_print(node.right, indent + 1)

    elif isinstance(node, UnaryOp):
        print(f"{prefix}UnaryOp: {node.op}  [line {node.line}]")
        pretty_print(node.operand, indent + 1)

    elif isinstance(node, Literal):
        print(f"{prefix}Literal: {node.value!r} ({node.lit_type})  [line {node.line}]")

    elif isinstance(node, Identifier):
        print(f"{prefix}Ident: {node.name}  [line {node.line}]")

    elif isinstance(node, ArrayAccess):
        print(f"{prefix}ArrayAccess: {node.name}[...]  [line {node.line}]")
        pretty_print(node.index, indent + 1)

    elif isinstance(node, FuncCall):
        print(f"{prefix}FuncCall: {node.name}()  [line {node.line}]")
        for arg in node.args:
            pretty_print(arg, indent + 1)

    else:
        print(f"{prefix}??? {type(node).__name__}: {node}")
