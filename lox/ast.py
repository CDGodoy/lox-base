from abc import ABC
from dataclasses import dataclass
from typing import Callable

from .runtime import truthy

from .ctx import Ctx

# Declaramos nossa classe base num módulo separado para esconder um pouco de
# Python relativamente avançado de quem não se interessar pelo assunto.
#
# A classe Node implementa um método `pretty` que imprime as árvores de forma
# legível. Também possui funcionalidades para navegar na árvore usando cursores
# e métodos de visitação.
from .node import Node


#
# TIPOS BÁSICOS
#

# Tipos de valores que podem aparecer durante a execução do programa
Value = bool | str | float | None


class Expr(Node, ABC):
    """
    Classe base para expressões.

    Expressões são nós que podem ser avaliados para produzir um valor.
    Também podem ser atribuídos a variáveis, passados como argumentos para
    funções, etc.
    """


class Stmt(Node, ABC):
    """
    Classe base para comandos.

    Comandos são associdos a construtos sintáticos que alteram o fluxo de
    execução do código ou declaram elementos como classes, funções, etc.
    """


@dataclass
class Program(Node):
    """
    Representa um programa.

    Um programa é uma lista de comandos.
    """

    stmts: list[Stmt]

    def eval(self, ctx: Ctx):
        for stmt in self.stmts:
            stmt.eval(ctx)


#
# EXPRESSÕES
#
@dataclass
class BinOp(Expr):
    """
    Uma operação infixa com dois operandos.

    Ex.: x + y, 2 * x, 3.14 > 3 and 3.14 < 4
    """

    left: Expr
    right: Expr
    op: Callable[[Value, Value], Value]

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)
        right_value = self.right.eval(ctx)
        return self.op(left_value, right_value)


@dataclass
class Var(Expr):
    """
    Uma variável no código

    Ex.: x, y, z
    """

    name: str

    def eval(self, ctx: Ctx):
        try:
            return ctx[self.name]
        except KeyError:
            raise NameError(f"variável {self.name} não existe!")


@dataclass
class Literal(Expr):
    """
    Representa valores literais no código, ex.: strings, booleanos,
    números, etc.

    Ex.: "Hello, world!", 42, 3.14, true, nil
    """

    value: Value

    def eval(self, ctx: Ctx):
        return self.value


@dataclass
class And(Expr):
    left: Expr
    right: Expr

    def eval(self, ctx: Ctx):
        left_val = self.left.eval(ctx)
        if not truthy(left_val):
            return left_val
        return self.right.eval(ctx)


@dataclass
class Or(Expr):
    left: Expr
    right: Expr

    def eval(self, ctx: Ctx):
        left_val = self.left.eval(ctx)
        if truthy(left_val):
            return left_val
        return self.right.eval(ctx)


@dataclass
class UnaryOp(Expr):
    """Uma operação prefixa."""

    op: Callable[[Value], Value]
    value: Expr

    def eval(self, ctx: Ctx):
        v = self.value.eval(ctx)
        return self.op(v)


@dataclass
class Call(Expr):
    """Uma chamada de função."""

    func: Expr
    params: list[Expr]

    def eval(self, ctx: Ctx):
        callee = self.func.eval(ctx)
        args = [p.eval(ctx) for p in self.params]
        if callable(callee):
            return callee(*args)
        raise TypeError(f"{callee} não é uma função!")


@dataclass
class This(Expr):
    """
    Acesso ao `this`.

    Ex.: this
    """


@dataclass
class Super(Expr):
    """
    Acesso a method ou atributo da superclasse.

    Ex.: super.x
    """


@dataclass
class Assign(Expr):
    """Atribuição de variável."""

    name: str
    value: Expr

    def eval(self, ctx: Ctx):
        val = self.value.eval(ctx)
        ctx.assign(self.name, val)
        return val


@dataclass
class Getattr(Expr):
    """Acesso a atributo de um objeto."""

    obj: Expr
    name: str

    def eval(self, ctx: Ctx):
        value = self.obj.eval(ctx)
        return getattr(value, self.name)


@dataclass
class Setattr(Expr):
    """Atribuição de atributo de um objeto."""

    obj: Expr
    name: str
    value: Expr

    def eval(self, ctx: Ctx):
        obj = self.obj.eval(ctx)
        val = self.value.eval(ctx)
        setattr(obj, self.name, val)
        return val


#
# COMANDOS
#
@dataclass
class Print(Stmt):
    """
    Representa uma instrução de impressão.

    Ex.: print "Hello, world!";
    """
    expr: Expr
    
    def eval(self, ctx: Ctx):
        value = self.expr.eval(ctx)
        print(value)


@dataclass
class Return(Stmt):
    """
    Representa uma instrução de retorno.

    Ex.: return x;
    """


@dataclass
class VarDef(Stmt):
    name: str
    value: Expr

    def eval(self, ctx: Ctx):
        val = self.value.eval(ctx)
        ctx.var_def(self.name, val)


@dataclass
class If(Stmt):
    cond: Expr
    then_branch: Stmt
    else_branch: Stmt | None = None

    def eval(self, ctx: Ctx):
        if truthy(self.cond.eval(ctx)):
            self.then_branch.eval(ctx)
        elif self.else_branch is not None:
            self.else_branch.eval(ctx)


@dataclass
class While(Stmt):
    cond: Expr
    body: Stmt

    def eval(self, ctx: Ctx):
        while truthy(self.cond.eval(ctx)):
            self.body.eval(ctx)


@dataclass
class Block(Node):
    decls: list[Stmt]

    def eval(self, ctx: Ctx):
        inner = ctx.push({})
        try:
            for d in self.decls:
                d.eval(inner)
        finally:
            inner.pop()


@dataclass
class Function(Stmt):
    """
    Representa uma função.

    Ex.: fun f(x, y) { ... }
    """


@dataclass
class Class(Stmt):
    """
    Representa uma classe.

    Ex.: class B < A { ... }
    """
