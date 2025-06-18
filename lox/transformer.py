"""
Implementa o transformador da árvore sintática que converte entre as representações

    lark.Tree -> lox.ast.Node.

A resolução de vários exercícios requer a modificação ou implementação de vários
métodos desta classe.
"""

from typing import Callable
from lark import Transformer, v_args

from . import runtime as op
from .ast import *


def op_handler(op: Callable):
    """
    Fábrica de métodos que lidam com operações binárias na árvore sintática.

    Recebe a função que implementa a operação em tempo de execução.
    """

    def method(self, left, right):
        return BinOp(left, right, op)

    return method


def unary_handler(func: Callable):
    def method(self, value):
        return UnaryOp(func, value)

    return method


@v_args(inline=True)
class LoxTransformer(Transformer):
    # Programa
    def program(self, *stmts):
        return Program(list(stmts))

    # Operações matemáticas básicas
    mul = op_handler(op.mul)
    div = op_handler(op.truediv)
    sub = op_handler(op.sub)
    add = op_handler(op.add)

    # Comparações
    gt = op_handler(op.gt)
    lt = op_handler(op.lt)
    ge = op_handler(op.ge)
    le = op_handler(op.le)
    eq = op_handler(op.eq)
    ne = op_handler(op.ne)

    # Operadores unários
    neg = unary_handler(op.neg)
    not_ = unary_handler(op.not_)

    def and_(self, left, right):
        return And(left, right)

    def or_(self, left, right):
        return Or(left, right)

    # Outras expressões
    def call(self, base, *suffixes):
        expr = base
        for part in suffixes:
            if isinstance(part, list):
                expr = Call(expr, part)
            elif isinstance(part, Var):
                expr = Getattr(expr, part.name)
            else:
                expr = Getattr(expr, str(part))
        return expr
        
    def params(self, *args):
        params = list(args)
        return params

    def call_args(self, params: list):
        return params

    def getattr(self, name: Var):
        return name

    def var_decl(self, name: Var, value=None):
        if value is None:
            value = Literal(None)
        return VarDef(name.name, value)

    def block(self, *decls):
        return Block(list(decls))

    def if_cmd(self, cond, then_branch, else_branch=None):
        return If(cond, then_branch, else_branch)

    def while_cmd(self, cond, body):
        return While(cond, body)

    def for_init(self, *args):
        return args[0] if args else None

    def for_cond(self, expr=None):
        return expr if expr is not None else Literal(True)

    def for_incr(self, expr=None):
        return expr

    def for_cmd(self, init, cond, incr, body):
        if incr is not None:
            body = Block([body, incr])
        loop = While(cond, body)
        decls = []
        if init is not None:
            decls.append(init)
        decls.append(loop)
        return Block(decls)

    # Comandos
    def print_cmd(self, expr):
        return Print(expr)

    def VAR(self, token):
        name = str(token)
        return Var(name)

    def NUMBER(self, token):
        num = float(token)
        return Literal(num)
    
    def STRING(self, token):
        text = str(token)[1:-1]
        return Literal(text)
    
    def NIL(self, _):
        return Literal(None)

    def BOOL(self, token):
        return Literal(token == "true")


    def assign(self, target, value):
        if isinstance(target, Var):
            return Assign(target.name, value)
        if isinstance(target, Getattr):
            return Setattr(target.obj, target.name, value)
        raise ValueError("Invalid assignment target")
