from sympy.core import Symbol
from sympy import Tuple
from sympy.printing.pycode import PythonCodePrinter as SympyPythonCodePrinter

from sympde.core.expr import BilinearForm, LinearForm, FunctionForm
from sympde.core.generic import Dot, Inner, Cross
from sympde.core.generic import Grad, Rot, Curl, Div
from sympde.core.geometry import Line, Square, Cube
from sympde.core.derivatives import _partial_derivatives


class PythonCodePrinter(SympyPythonCodePrinter):

    # ...........................
    # TODO move this to pyccel
    # ...........................
    def _print_FunctionDef(self, expr):
        name = self._print(expr.name)
        body = '\n'.join(self._print(i) for i in expr.body)
        body = self._indent_codestring(body)
        args = ', '.join(self._print(i) for i in expr.arguments)

        #imports = '\n'.join(self._print(i) for i in expr.imports)
        code = ('def {0}({1}):\n'
                '{2}\n').format(name, args, body)
        return code

    def _print_Return(self, expr):
        return 'return {}'.format(self._print(expr.expr))

    def _print_Comment(self, expr):
        txt = self._print(expr.text)
        return '# {0} '.format(txt)

    def _print_EmptyLine(self, expr):
        return ''

    def _print_NewLine(self, expr):
        return '\n'

    def _print_DottedName(self, expr):
        return '.'.join(self._print(n) for n in expr.name)

    def _print_FunctionCall(self, expr):
        func = self._print(expr.func)
        args = ','.join(self._print(i) for i in expr.arguments)
        return'{func}({args})'.format(func=func, args=args)

    def _print_Len(self, expr):
        return 'len({})'.format(self._print(expr.arg))

    def _print_Import(self, expr):
        target = ', '.join([self._print(i) for i in expr.target])
        if expr.source is None:
            return 'import {target}'.format(target=target)
        else:
            source = self._print(expr.source)
            return 'from {source} import {target}'.format(source=source, target=target)

    def _print_For(self, expr):
        iter   = self._print(expr.iterable)
        target = self._print(expr.target)
        body   = '\n'.join(self._print(i) for i in expr.body)
        body   = self._indent_codestring(body)
        code   = ('for {0} in {1}:\n'
                '{2}\n').format(target,iter,body)

        return code

    def _print_Assign(self, expr):
        lhs = self._print(expr.lhs)
        rhs = self._print(expr.rhs)
        return'{0} = {1}'.format(lhs,rhs)

    def _print_AugAssign(self, expr):
        lhs = self._print(expr.lhs)
        rhs = self._print(expr.rhs)
        op  = self._print(expr.op._symbol)
        return'{0} {1}= {2}'.format(lhs,op,rhs)

    def _print_Range(self, expr):
        start = self._print(expr.start)
        stop  = self._print(expr.stop)
        step  = self._print(expr.step)
        return 'range({}, {}, {})'.format(start,stop,step)

    def _print_IndexedBase(self, expr):
        return self._print(expr.label)

    def _print_Indexed(self, expr):
        inds = [i for i in expr.indices]
        #indices of indexedElement of len==1 shouldn't be a Tuple
        for i, ind in enumerate(inds):
            if isinstance(ind, Tuple) and len(ind) == 1:
                inds[i] = ind[0]

        inds = [self._print(i) for i in inds]

        return "%s[%s]" % (self._print(expr.base.label), ", ".join(inds))

    def _print_Zeros(self, expr):
        return 'zeros('+ self._print(expr.shape)+')'

    def _print_Slice(self, expr):
        return str(expr)

    def _print_Nil(self, expr):
        return 'None'

    def _print_Pass(self, expr):
        return 'pass'

    def _print_Is(self, expr):
        lhs = self._print(expr.lhs)
        rhs = self._print(expr.rhs)
        return'{0} is {1}'.format(lhs,rhs)

    def _print_If(self, expr):
        lines = []
        for i, (c, e) in enumerate(expr.args):
            if i == 0:
                lines.append("if (%s):" % self._print(c))

            elif i == len(expr.args) - 1 and c == True:
                lines.append("else:")

            else:
                lines.append("elif (%s):" % self._print(c))

            if isinstance(e, (list, tuple, Tuple)):
                for ee in e:
                    body = self._indent_codestring(self._print(ee))
                    lines.append(body)
            else:
                lines.append(self._print(e))
        return "\n".join(lines)
    # ...........................




    def _print_dx(self, expr):
        arg = self._print(expr.args[0])
        return arg + '_x'

    def _print_dy(self, expr):
        arg = self._print(expr.args[0])
        return arg + '_y'

    def _print_dz(self, expr):
        arg = self._print(expr.args[0])
        return arg + '_z'


def pycode(expr, **settings):
    """ Converts an expr to a string of Python code
    Parameters
    ==========
    expr : Expr
        A SymPy expression.
    fully_qualified_modules : bool
        Whether or not to write out full module names of functions
        (``math.sin`` vs. ``sin``). default: ``True``.
    Examples
    ========
    >>> from sympy import tan, Symbol
    >>> from sympy.printing.pycode import pycode
    >>> pycode(tan(Symbol('x')) + 1)
    'math.tan(x) + 1'
    """
    return PythonCodePrinter(settings).doprint(expr)
