# coding: utf-8
# TODO: - Unknown is not used here (mlhipy) remove it?

from numpy import unique

from sympy.core import Basic
from sympy.tensor import Indexed, IndexedBase
from sympy.core import Symbol
from sympy.core import Expr
from sympy.core.containers import Tuple
from sympy import Function
from sympy import Integer, Float
from sympy.core.singleton import Singleton
from sympy.core.compatibility import with_metaclass
from sympy.core import Add, Mul
from sympy.core.singleton import S

from sympde.core.basic import _coeffs_registery
from sympde.core import LinearOperator

from .form import DifferentialForm


# ...
class ExteriorDerivative(LinearOperator):

    nargs = None

    def __new__(cls, *args, **options):
        # (Try to) sympify args first

        if options.pop('evaluate', True):
            r = cls.eval(*args)
        else:
            r = None

        if r is None:
            return Basic.__new__(cls, *args, **options)
        else:
            return r

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        if not( len(_args) == 1):
            raise ValueError('Expecting one argument')

        expr = _args[0]

        if isinstance(expr, ExteriorDerivative):
            return 0

        # TODO improve
        elif isinstance(expr, (int, complex)):
            return 0

        elif isinstance(expr, _coeffs_registery):
            return 0

        elif isinstance(expr, Add):
            args = expr.args
            args = [cls.eval(a) for a in expr.args]
            return Add(*args)

        elif isinstance(expr, Mul):
            coeffs  = [a for a in expr.args if isinstance(a, _coeffs_registery)]
            vectors = [a for a in expr.args if not(a in coeffs)]

            a = S.One
            if coeffs:
                a = Mul(*coeffs)

            b = S.One
            if vectors:
                b = cls(Mul(*vectors), evaluate=False)

            return Mul(a, b)


        return cls(expr, evaluate=False)

    def _sympystr(self, printer):
        sstr = printer.doprint
        return '{d}({arg})'.format(d=sstr('d'), arg=sstr(self.args[0]))
# ...

# ...
class ExteriorProduct(LinearOperator):

    nargs = None

    def __new__(cls, *args, **options):
        # (Try to) sympify args first

        if options.pop('evaluate', True):
            r = cls.eval(*args)
        else:
            r = None

        if r is None:
            return Basic.__new__(cls, *args, **options)
        else:
            return r

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        if not( len(_args) == 2):
            raise ValueError('Expecting two arguments')

        left = _args[0]
        right = _args[1]
        # TODO add properties in the spirit of ExteriorDerivative

        return cls(left, right, evaluate=False)

    @property
    def math_symbol(self):
        math_str = '/\\'
        return math_str

    def _sympystr(self, printer):
        sstr = printer.doprint
        left = self.args[0]
        right = self.args[1]
        return '{left} {math} {right}'.format( math=sstr(self.math_symbol),
                                                left=sstr(left),
                                                right=sstr(right) )
# ...

# ...
class InteriorProduct(LinearOperator):

    nargs = None

    def __new__(cls, *args, **options):
        # (Try to) sympify args first

        if options.pop('evaluate', True):
            r = cls.eval(*args)
        else:
            r = None

        if r is None:
            return Basic.__new__(cls, *args, **options)
        else:
            return r

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        if not( len(_args) == 2):
            raise ValueError('Expecting two arguments')

        left = _args[0]
        right = _args[1]
        # TODO add properties?

        return cls(left, right, evaluate=False)

    @property
    def math_symbol(self):
        math_str = '_|'
        return math_str

    def _sympystr(self, printer):
        sstr = printer.doprint
        return '{left} {math} {right}'.format( math=sstr(self.math_symbol),
                                                left=sstr(self.args[0]),
                                                right=sstr(self.args[1]) )
# ...

# ...
class PullBack(LinearOperator):

    nargs = None
    _name = None

    def __new__(cls, *args, **options):
        # (Try to) sympify args first

        name = options.pop('name', None)

        if options.pop('evaluate', True):
            r = cls.eval(*args)
        else:
            r = None

        if r is None:
            obj = Basic.__new__(cls, *args, **options)
            obj._name = name
            return obj
        else:
            r._name = name
            return r

    @property
    def name(self):
        return self._name

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        if not( len(_args) == 1):
            raise ValueError('Expecting one argument')

        expr = _args[0]
        # TODO add properties?
        if isinstance(expr, ExteriorProduct):
            left = expr.args[0]
            right = expr.args[1]
            return ExteriorProduct(cls(left, evaluate=False),
                                   cls(right, evaluate=False))

        return cls(expr, evaluate=False)

#    def __call__(self, *args):
#        return PullBack(*args, name=self.name)

    def _sympystr(self, printer):
        sstr = printer.doprint
        name = self.name
        if not name:
            name = 'PullBack'
        arg = self.args[0]
        return '{name}({arg})'.format( name=sstr(name), arg=sstr(arg) )
# ...

# ...
def infere_index(expr):
    if isinstance(expr, DifferentialForm):
        return expr.index

    elif isinstance(expr, ExteriorDerivative):
        arg = expr.args[0]
        i = infere_index(arg)

        return get_index_form(i.index - 1)

    elif isinstance(expr, ExteriorProduct):
        left = expr.args[0]
        right = expr.args[1]
        i = infere_index(left)
        j = infere_index(right)

        return get_index_form(i.index + j.index)

    elif isinstance(expr, Add):
        indices = set([infere_index(i) for i in expr.args])
        indices = list(indices)
        if not( len(indices) == 1 ):
            raise ValueError('> Incompatible types. Found {}'.format(indices))

        return indices[0]

    return None
# ...

# ... user friendly names
d = ExteriorDerivative
wedge = ExteriorProduct
ip = InteriorProduct
# ...
