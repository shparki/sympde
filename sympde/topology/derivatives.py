# coding: utf-8

# TODO add action of diff operators on sympy known functions

import numpy as np
from itertools import groupby
from collections import OrderedDict

#from sympy.core.sympify import sympify
from sympy.simplify.simplify import simplify
from sympy import Derivative
from sympy.core.function import AppliedUndef
from sympy.core.function import UndefinedFunction
from sympy import Symbol
from sympy import Lambda
from sympy import Function
from sympy import bspline_basis
from sympy import lambdify
from sympy import cos
from sympy import sin
from sympy import Rational
from sympy import diff
from sympy import Matrix, ImmutableDenseMatrix
from sympy import latex
from sympy import I as sympy_I
from sympy.core import Basic
from sympy.core.singleton import S
from sympy.simplify.simplify import nsimplify
from sympy.utilities.lambdify import implemented_function
from sympy.matrices.dense import MutableDenseMatrix
from sympy import Mul, Add, Pow
from sympy import postorder_traversal
from sympy import preorder_traversal

from sympy.core.expr import Expr
from sympy.core.containers import Tuple
from sympy import Integer, Float

from sympy import Add, Mul
from sympy import preorder_traversal, Expr
from sympy import simplify
from sympy import S
from sympy.core.compatibility import is_sequence
from sympy import Basic
from sympy import Indexed, IndexedBase

from sympde.core.basic import CalculusFunction
from sympde.core.basic import _coeffs_registery
from sympde.core.basic import Field, Constant
from sympde.core.basic import BasicMapping
from sympde.core.algebra import LinearOperator
from .space import TestFunction, VectorTestFunction, IndexedTestTrial
from .space import Unknown
from .space import VectorField, IndexedVectorField

# ...
class DifferentialOperator(LinearOperator):
    """
    This class is a linear operator that applies the Leibniz formula

    Examples
    ========

    """
    coordinate = None

    @classmethod
    def eval(cls, *_args):
        """."""

        expr = _args[0]

        # TODO use coordinates for IndexedTestTrial?
        if isinstance(expr, (IndexedTestTrial, IndexedVectorField, DifferentialOperator)):
            return cls(expr, evaluate=False)

        elif isinstance(expr, (Field, TestFunction)):

            coord = cls.coordinate
            coordinates = expr.space.coordinates
            # 1d case
            if not isinstance(coordinates, (list, tuple, Tuple)):
                coordinates = [coordinates]

            names = [c.name for c in coordinates]
            if coord in names:
                return cls(expr, evaluate=False)

            else:
                return S.Zero

        elif isinstance(expr, (VectorTestFunction, VectorField)):
            n = expr.shape[0]
            args = [cls(expr[i], evaluate=False) for i in range(0, n)]
            args = Tuple(*args)
            return Matrix([args])

        elif isinstance(expr, Indexed) and isinstance(expr.base, BasicMapping):

            coord = cls.coordinate
            coordinates = expr.base.coordinates
            # 1d case
            if not isinstance(coordinates, (list, tuple, Tuple)):
                coordinates = [coordinates]

            names = [c.name for c in coordinates]
            if coord in names:
                return cls(expr, evaluate=False)

            else:
                return S.Zero

        elif isinstance(expr, (list, tuple, Tuple)):
            args = [cls(i, evaluate=True) for i in expr]
            args = Tuple(*args)
            return Matrix([args])

        elif isinstance(expr, Add):
            args = expr.args
            args = [cls.eval(a) for a in expr.args]
            return Add(*args)

        elif isinstance(expr, Mul):
            coeffs  = [a for a in expr.args if isinstance(a, _coeffs_registery)]
            vectors = [a for a in expr.args if not(a in coeffs)]

            c = S.One
            if coeffs:
                c = Mul(*coeffs)

            V = S.One
            if vectors:
                if len(vectors) == 1:
                    # do we need to use Mul?
                    V = cls(Mul(vectors[0]), evaluate=True)

                elif len(vectors) == 2:
                    a = vectors[0]
                    b = vectors[1]

                    fa = cls(a, evaluate=True)
                    fb = cls(b, evaluate=True)

                    V = a * fb + fa * b

                else:
                    a = vectors[0]
                    b = Mul(*vectors[1:])

                    fa = cls(a, evaluate=True)
                    fb = cls(b, evaluate=True)

                    V = a * fb + fa * b

            return Mul(c, V)

        elif isinstance(expr, Derivative):
            x = Symbol(cls.coordinate)
            f = expr.args[0]
            args = list(expr.args[1:])
            args += [x]
            return Derivative(f, *args)

        elif isinstance(expr, UndefinedFunction):
            x = Symbol(cls.coordinate)
            return Derivative(expr, x)

        elif isinstance(expr, AppliedUndef):
            x = Symbol(cls.coordinate)
            return Derivative(expr, x)

        elif isinstance(expr, Expr):
            x = Symbol(cls.coordinate)
            return diff(expr, x)

        else:
            msg = '{expr} of type {type}'.format(expr=expr, type=type(expr))
            raise NotImplementedError(msg)
# ...


# ...
class dx(DifferentialOperator):
    coordinate = 'x'
    grad_index = 0 # index in grad
    pass

class dy(DifferentialOperator):
    coordinate = 'y'
    grad_index = 1 # index in grad
    pass

class dz(DifferentialOperator):
    coordinate = 'z'
    grad_index = 2 # index in grad
    pass

_partial_derivatives = (dx, dy, dz)
# ...

# ...
def find_partial_derivatives(expr):
    """
    returns all partial derivative expressions
    """
    if isinstance(expr, (Add, Mul)):
        return find_partial_derivatives(expr.args)

    elif isinstance(expr, Pow):
        return find_partial_derivatives(expr.base)

    elif isinstance(expr, (list, tuple, Tuple)):
        args = []
        for a in expr:
            args += find_partial_derivatives(a)
        return args

    elif isinstance(expr, _partial_derivatives):
        return [expr]

    return []
# ...

# ...
def get_number_derivatives(expr):
    """
    returns the number of partial derivatives in expr.
    this is still an experimental version, and it assumes that expr is of the
    form d(a) where a is a single atom.
    """
    n = 0
    if isinstance(expr, _partial_derivatives):
        assert(len(expr.args) == 1)

        n += 1 + get_number_derivatives(expr.args[0])
    return n
# ...

# ...
def sort_partial_derivatives(expr):
    """returns the partial derivatives of an expression, sorted.
    """
    ls = []

    args = find_partial_derivatives(expr)

#    # ... Note
#    #     group by is given the wrong answer for expr =mu * u + dx(u) + dx(dx(u))
#    for key, group in groupby(args, lambda x: get_number_derivatives(x)):
#        g = [a for a in group]
#        for a in group:
#            ls.append(a)
#    # ...

    # ...
    d = {}
    for a in args:
        n = get_number_derivatives(a)
        if n in d.keys():
            d[n] += [a]
        else:
            d[n] = [a]
    # ...

    # ...
    if not d:
        return []
    # ...

    # ... sort keys from high to low
    keys = np.asarray(list(d.keys()))
    keys.sort()
    keys = keys[::-1]
    # ...

    # ... construct a list of partial derivatives from high to low order
    ls = []
    for k in keys:
        ls += d[k]
    # ...

    return ls
# ...

# ...
def get_index_derivatives(expr):
    """
    """
    coord = ['x','y','z']

    d = OrderedDict()
    for c in coord:
        d[c] = 0

    ops = [a for a in preorder_traversal(expr) if isinstance(a, _partial_derivatives)]
    for i in ops:
        op = type(i)

        if isinstance(i, dx):
            d['x'] += 1

        elif isinstance(i, dy):
            d['y'] += 1

        elif isinstance(i, dz):
            d['z'] += 1

    return d
# ...

# ...
def get_atom_derivatives(expr):
    """
    """

    if isinstance(expr, _partial_derivatives):
        assert(len(expr.args) == 1)

        return get_atom_derivatives(expr.args[0])

    else:
        return expr
# ...

# ...
def print_expression(expr, logical=False, mapping_name=True):
    # dict to map physical to logical coordinates
    # TODO improve using a Coordinates object, as a singleton
    d_coords = {'x': 'x1',
                'y': 'x2',
                'z': 'x3'}

    # ...
    mapping = tuple(expr.atoms(BasicMapping))
    if mapping:
        mapping = mapping[0]
        dim = mapping.rdim
        domain = mapping.domain

        # ...
        coords = mapping.coordinates
        if not isinstance(coords, (tuple, list, Tuple)):
            coords = [coords]

        else:
            coords = [i for i in coords]

        coords = [str(x.name) for x in coords]
        # ...

        # ...
        lcoords = ['x1', 'x2', 'x3'][:dim]
        # ...

        name = str(mapping.name)
        for i in range(0, dim):
            old = mapping[i]
            new = '{M}{i}'.format(M=name, i=i)
            new = Unknown(new, domain)
            expr = expr.subs(old, new)
    # ...

    # ...
    atom = get_atom_derivatives(expr)
    indices = get_index_derivatives_atom(expr, atom)
    # ...

    # ... change code to a string like '_x'
    if indices:
        index = indices[0]
        code = ''
        for k,n in list(index.items()):
            if not logical:
                code += k*n

            else:
                code += d_coords[k]*n

        if isinstance(atom, (IndexedTestTrial, IndexedVectorField)):
            name =  '{base}_{i}'.format(base=atom.base.name, i=atom.indices[0])
        else:
            name = atom.name

        name = '{name}_{code}'.format(name=name, code=code)

    else:
        if isinstance(atom, (IndexedTestTrial, IndexedVectorField)):
            name =  '{base}_{i}'.format(base=atom.base.name, i=atom.indices[0])
        else:
            name = str(atom)
    # ...

    # ...
    if mapping:
        M = str(mapping.name)
        for i in range(0, dim):
            name = name.replace(coords[i], lcoords[i])
            if mapping_name:
                name = name.replace(M+str(i), M+coords[i])

            else:
                name = name.replace(M+str(i), coords[i])
    # ...

    return name
# ...

# ...
class DotBasic(CalculusFunction):
    """

    Examples
    ========

    """

    nargs = None
    name = 'Dot'

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

class Dot_1d(DotBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        if not( len(_args) == 2):
            raise ValueError('Expecting two arguments')

        u = _args[0]
        v = _args[1]

        return u * v

class Dot_2d(DotBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        if not( len(_args) == 2):
            raise ValueError('Expecting two arguments')

        u = _args[0]
        v = _args[1]

        if isinstance(u, (Matrix, ImmutableDenseMatrix)):
            if isinstance(v, (Matrix, ImmutableDenseMatrix)):
                raise NotImplementedError('TODO')

            else:
                return Tuple(u[0,0]*v[0] + u[0,1]*v[1], u[1,0]*v[0] + u[1,1]*v[1])

        else:
            if isinstance(v, (Matrix, ImmutableDenseMatrix)):
                raise NotImplementedError('TODO')

            else:
                return u[0]*v[0] + u[1]*v[1]

class Dot_3d(DotBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        if not( len(_args) == 2):
            raise ValueError('Expecting two arguments')

        u = _args[0]
        v = _args[1]

        if isinstance(u, (Matrix, ImmutableDenseMatrix)):
            if isinstance(v, (Matrix, ImmutableDenseMatrix)):
                raise NotImplementedError('TODO')

            else:
                return Tuple(u[0,0]*v[0] + u[0,1]*v[1] + u[0,2]*v[2],
                             u[1,0]*v[0] + u[1,1]*v[1] + u[1,2]*v[2],
                             u[2,0]*v[0] + u[2,1]*v[1] + u[2,2]*v[2])

        else:
            if isinstance(v, (Matrix, ImmutableDenseMatrix)):
                raise NotImplementedError('TODO')

            else:
                return u[0]*v[0] + u[1]*v[1] + u[2]*v[2]
# ...

# ...
class CrossBasic(CalculusFunction):
    """

    Examples
    ========

    """

    nargs = None
    name = 'Cross'

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

class Cross_2d(CrossBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]
        v = _args[1]

        return u[0]*v[1] - u[1]*v[0]

class Cross_3d(CrossBasic):
    """

    Examples
    ========

    """

    def __getitem__(self, indices, **kw_args):
        if is_sequence(indices):
            # Special case needed because M[*my_tuple] is a syntax error.
            return Indexed(self, *indices, **kw_args)
        else:
            return Indexed(self, indices, **kw_args)

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]
        v = _args[1]

        return Tuple(u[1]*v[2] - u[2]*v[1],
                     u[2]*v[0] - u[0]*v[2],
                     u[0]*v[1] - u[1]*v[0])
# ...


# ...
class GradBasic(CalculusFunction):
    """

    Examples
    ========

    """

    nargs = None
    name = 'Grad'

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

    def __getitem__(self, indices, **kw_args):
        if is_sequence(indices):
            # Special case needed because M[*my_tuple] is a syntax error.
            return Indexed(self, *indices, **kw_args)
        else:
            return Indexed(self, indices, **kw_args)

class Grad_1d(GradBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]

        return dx(u)

class Grad_2d(GradBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]

        if isinstance(u, Tuple):
            n = len(u)
            lines = []
            for i in range(0, n):
                line = [dx(u)[0,i], dy(u)[0,i]]
                lines.append(line)

            v = Matrix(lines)

        else:
            v = Tuple(dx(u), dy(u))

        return v

class Grad_3d(GradBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]

        if isinstance(u, Tuple):
            n = len(u)
            lines = []
            for i in range(0, n):
                line = [dx(u)[0,i], dy(u)[0,i], dz(u)[0,i]]
                lines.append(line)

            v = Matrix(lines)

        else:
            v = Tuple(dx(u), dy(u), dz(u))

        return v
# ...


# ...
class CurlBasic(CalculusFunction):
    """

    Examples
    ========

    """

    nargs = None
    name = 'Curl'

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

    def __getitem__(self, indices, **kw_args):
        if is_sequence(indices):
            # Special case needed because M[*my_tuple] is a syntax error.
            return Indexed(self, *indices, **kw_args)
        else:
            return Indexed(self, indices, **kw_args)

class Curl_2d(CurlBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]

        return Tuple( dy(u),
                     -dx(u))

class Curl_3d(CurlBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]

        return Tuple(dy(u[2]) - dz(u[1]),
                     dz(u[0]) - dx(u[2]),
                     dx(u[1]) - dy(u[0]))
# ...

# ...
class Rot_2d(CalculusFunction):
    """

    Examples
    ========

    """

    nargs = None
    name = 'Grad'

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

    def __getitem__(self, indices, **kw_args):
        if is_sequence(indices):
            # Special case needed because M[*my_tuple] is a syntax error.
            return Indexed(self, *indices, **kw_args)
        else:
            return Indexed(self, indices, **kw_args)

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]

        return dy(u[0]) - dx(u[1])
# ...

# ...
class DivBasic(CalculusFunction):
    """

    Examples
    ========

    """

    nargs = None
    name = 'Div'

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

    def __getitem__(self, indices, **kw_args):
        if is_sequence(indices):
            # Special case needed because M[*my_tuple] is a syntax error.
            return Indexed(self, *indices, **kw_args)
        else:
            return Indexed(self, indices, **kw_args)

class Div_1d(DivBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]

        return dx(u)

class Div_2d(DivBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]

        return dx(u[0]) + dy(u[1])

class Div_3d(DivBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]

        return dx(u[0]) + dy(u[1]) + dz(u[2])
# ...

# ...
class LaplaceBasic(CalculusFunction):
    """

    Examples
    ========

    """

    nargs = None
    name = 'Laplace'

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

    def __getitem__(self, indices, **kw_args):
        if is_sequence(indices):
            # Special case needed because M[*my_tuple] is a syntax error.
            return Indexed(self, *indices, **kw_args)
        else:
            return Indexed(self, indices, **kw_args)

class Laplace_1d(LaplaceBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]
        if isinstance(u, (VectorTestFunction, VectorField)):
            raise NotImplementedError('TODO')

        return dx(dx(u))

class Laplace_2d(LaplaceBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]
        if isinstance(u, (VectorTestFunction, VectorField)):
            raise NotImplementedError('TODO')

        return dx(dx(u)) + dy(dy(u))

class Laplace_3d(LaplaceBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]
        if isinstance(u, (VectorTestFunction, VectorField)):
            raise NotImplementedError('TODO')

        return dx(dx(u)) + dy(dy(u)) + dz(dz(u))
# ...

# ...
class HessianBasic(CalculusFunction):
    """

    Examples
    ========

    """

    nargs = None
    name = 'Hessian'

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

    def __getitem__(self, indices, **kw_args):
        if is_sequence(indices):
            # Special case needed because M[*my_tuple] is a syntax error.
            return Indexed(self, *indices, **kw_args)
        else:
            return Indexed(self, indices, **kw_args)

class Hessian_1d(HessianBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]
        if isinstance(u, (VectorTestFunction, VectorField)):
            raise NotImplementedError('TODO')

        return dx(dx(u))

class Hessian_2d(HessianBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]
        if isinstance(u, (VectorTestFunction, VectorField)):
            raise NotImplementedError('TODO')

        return Matrix([[dx(dx(u)), dx(dy(u))],
                       [dx(dy(u)), dy(dy(u))]])

class Hessian_3d(HessianBasic):
    """

    Examples
    ========

    """

    @classmethod
    def eval(cls, *_args):
        """."""

        if not _args:
            return

        u = _args[0]
        if isinstance(u, (VectorTestFunction, VectorField)):
            raise NotImplementedError('TODO')

        return Matrix([[dx(dx(u)), dx(dy(u)), dx(dz(u))],
                       [dx(dy(u)), dy(dy(u)), dy(dz(u))],
                       [dx(dz(u)), dy(dz(u)), dz(dz(u))]])
# ...

# ...
class BracketBasic(CalculusFunction):
    pass

class Bracket_2d(BracketBasic):
    """

    Examples
    ========

    """

    nargs = None
    name = 'Bracket'

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

        u = _args[0]
        v = _args[1]

        return dx(u)*dy(v) - dy(u)*dx(v)
# ...

# ... TODO to be removed, not used anymore
def partial_derivative_as_symbol(expr, name=None, dim=None):
    """Returns a Symbol from a partial derivative expression."""
    if not isinstance(expr, _partial_derivatives):
        raise TypeError('Expecting a partial derivative expression')

    index = get_index_derivatives(expr)
    var = get_atom_derivatives(expr)

    if not isinstance(var, (Symbol, Indexed)):
        print(type(var))
        raise TypeError('Expecting a Symbol, Indexed')

    code = ''
    for k,n in list(index.items()):
        code += k*n

    if var.is_Indexed:
        if name is None:
            name = var.base

        indices = ''.join('{}'.format(i) for i in var.indices)
        name = '{name}_{code}'.format(name=name, code=code)
        shape = None
        if dim:
            shape = [dim]
        return IndexedBase(name, shape=shape)[indices]

    else:
        if name is None:
            name = var.name

        name = '{name}_{code}'.format(name=name, code=code)
        return Symbol(name)
# ...

# ...
def partial_derivative_as_str(expr):
    """Returns a string from a partial derivative expression."""
    if not isinstance(expr, _partial_derivatives):
        raise TypeError('Expecting a partial derivative expression')

    index = get_index_derivatives(expr)
    var = get_atom_derivatives(expr)

    if not isinstance(var, (Symbol, Indexed)):
        print(type(var))
        raise TypeError('Expecting a Symbol, Indexed')

    code = ''
    for k,n in list(index.items()):
        code += k*n

    return code
# ...

# ...
def get_index_derivatives_atom(expr, atom, verbose=False):
    """This function return a dictionary of partial derivative indices for
    a given atom.
    it must be called after atomizing the expression.
    """
    ops = sort_partial_derivatives(expr)
    if verbose:
        print('> ops = ', ops)

    indices = []
    for i in ops:
        a = get_atom_derivatives(i)
        if a == atom:
            index = get_index_derivatives(i)
            indices.append(index)

    return indices
# ...

def get_max_partial_derivatives(expr, F=None):
    if F is None:
        Fs = (list(expr.atoms(TestFunction)) +
              list(expr.atoms(VectorTestFunction)) +
              list(expr.atoms(IndexedTestTrial)) +
              list(expr.atoms(VectorField)) +
              list(expr.atoms(IndexedVectorField)) +
              list(expr.atoms(Field)))

        indices = []
        for F in Fs:
            indices += get_index_derivatives_atom(expr, F)
    else:
        indices = get_index_derivatives_atom(expr, F)

    d = {'x':0, 'y':0, 'z':0}
    for dd in indices:
        for k,v in dd.items():
            if v > d[k]: d[k] = v
    return d