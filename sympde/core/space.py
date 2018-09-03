# coding: utf-8

# TODO: - add VectorUnknown

from numpy import unique

from sympy.core import Basic
from sympy.tensor import Indexed, IndexedBase
from sympy.core import Symbol
from sympy.core import Expr
from sympy.core.containers import Tuple

from .basic import DottedName

# ...
class BasicSobolevSpace(Basic):
    """
    Represents a basic continuous Sobolev space.

    Examples

    """
    _ldim = None
    _shape = None
    _is_vector = False
    _is_block = False
    def __new__(cls, name, ldim=None, shape=None, is_vector=False,
                is_block=False, coordinates=None):
        if is_vector or is_block:
            if shape is None:
                raise ValueError('shape must be provided for a vector/block space')

        obj = Basic.__new__(cls, name)
        obj._ldim = ldim
        if shape is None:
            obj._shape = 1
        else:
            obj._shape = shape

        obj._is_vector = is_vector
        obj._is_block = is_block

        if coordinates is None:
            _coordinates = []
            if ldim:
                _coordinates = [Symbol(name) for name in ['x', 'y', 'z'][:ldim]]
        else:
            if not isinstance(coordinates, (list, tuple, Tuple)):
                raise TypeError('> Expecting list, tuple, Tuple')

            for a in coordinates:
                if not isinstance(a, (str, Symbol)):
                    raise TypeError('> Expecting str or Symbol')

            _coordinates = [Symbol(name) for name in coordinates]

        obj._coordinates = _coordinates

        return obj

    @property
    def name(self):
        return self._args[0]

    @property
    def ldim(self):
        return self._ldim

    @property
    def shape(self):
        return self._shape

    @property
    def is_vector(self):
        return self._is_vector

    @property
    def is_block(self):
        return self._is_block

    @property
    def ldim(self):
        return self._ldim

    @property
    def coordinates(self):
        if self.ldim == 1:
            return self._coordinates[0]
        else:
            return self._coordinates

    def _sympystr(self, printer):
        sstr = printer.doprint
        return sstr(self.name)
# ...

# ... TODO shall we keep the definition of is_block/is_vector as it is now?
class ProductSpace(BasicSobolevSpace):
    """
    Represents a product of continuous Sobolev spaces.

    Examples

    """
    def __new__(cls, *spaces):

        # ...
        if not (isinstance(spaces, (tuple, list, Tuple))):
            raise TypeError('> Expecting a tuple, list or Tuple')

        spaces = Tuple(*spaces)
        # ...

        # ...
        ldim = unique([i.ldim for i in spaces])
        if not( len(ldim) == 1 ):
            raise ValueError('> All spaces must have the same logical dimension ldim')

        ldim = ldim[0]
        # ...

        # ...
        shape = sum([i.shape for i in spaces])
        # ...

        # ...
        name = ''.join(i.name for i in spaces)
        # ...

        # ...
        def _get_name(V):
            if V.ldim == 1:
                return V.coordinates.name
            else:
                return [i.name for i in V.coordinates]

        coordinates = unique([_get_name(i) for i in spaces])
        for i in coordinates:
            if not isinstance(i, str):
                raise TypeError('> Expecting a string')

        coordinates = spaces[0].coordinates
        if isinstance(coordinates, Symbol):
            coordinates = [coordinates]
        # ...

        # ...
        obj = Basic.__new__(cls, spaces)

        obj._ldim = ldim
        obj._shape = shape
        obj._is_vector = False
        obj._is_block = True
        obj._coordinates = coordinates
        obj._name = name
        # ...

        return obj

    @property
    def spaces(self):
        return self._args[0]

    @property
    def name(self):
        return self._name

    @property
    def ldim(self):
        return self._ldim

    @property
    def shape(self):
        return self._shape

    @property
    def is_vector(self):
        return self._is_vector

    @property
    def is_block(self):
        return self._is_block

    @property
    def ldim(self):
        return self._ldim

    @property
    def coordinates(self):
        if self.ldim == 1:
            return self._coordinates[0]
        else:
            return self._coordinates

    def _sympystr(self, printer):
        sstr = printer.doprint
        return sstr(self.name)
# ...


# TODO make it as a singleton
class H1Space(BasicSobolevSpace):
    """
    Represents the H1 continuous Sobolev space.

    Examples

    """
    pass

# TODO make it as a singleton
class HcurlSpace(BasicSobolevSpace):
    """
    Represents the Hcurl continuous Sobolev space.

    Examples

    """
    pass

# TODO make it as a singleton
class HdivSpace(BasicSobolevSpace):
    """
    Represents the Hdiv continuous Sobolev space.

    Examples

    """
    pass

# TODO make it as a singleton
class L2Space(BasicSobolevSpace):
    """
    Represents the L2 continuous Sobolev space.

    Examples

    """
    pass


class TestFunction(Symbol):
    """
    Represents a test function as an element of a fem space.

    Examples

    >>> from sympde.codegen.core import SplineFemSpace
    >>> from sympde.codegen.core import TestFunction
    >>> V = SplineFemSpace('V')
    >>> phi = TestFunction(V, 'phi')
    """
    _space = None
    is_commutative = True
    def __new__(cls, space, name=None):
        obj =  Basic.__new__(cls, name)
        obj._space = space
        return obj

    @property
    def space(self):
        return self._space

    @property
    def name(self):
        return self._args[0]

    def duplicate(self, name):
        return TestFunction(self.space, name)

    def _sympystr(self, printer):
        sstr = printer.doprint
        return sstr(self.name)


# this class is needed, otherwise sympy will convert VectorTestFunction to
# IndexedBase
class IndexedTestTrial(Indexed):
    """Represents a mathematical object with indices.

    """
    is_commutative = True
    is_Indexed = True
    is_symbol = True
    is_Atom = True

    def __new__(cls, base, *args, **kw_args):
        assert(isinstance(base, VectorTestFunction))

        if not args:
            raise IndexException("Indexed needs at least one index.")

        return Expr.__new__(cls, base, *args, **kw_args)

    # free_symbols is redefined otherwise an expression u[0].free_symbols will
    # give the error:  AttributeError: 'int' object has no attribute 'free_symbols'
    @property
    def free_symbols(self):
        base_free_symbols = self.base.free_symbols
        symbolic_indices = [i for i in self.indices if isinstance(i, Basic)]
        if len(symbolic_indices) > 0:
            raise ValueError('symbolic indices not yet available')

        return base_free_symbols

        # TODO uncomment if needed
#        indices_free_symbols = {
#            fs for i in symbolic_indices for fs in i.free_symbols}
#        if base_free_symbols:
#            return {self} | base_free_symbols | indices_free_symbols
#        else:
#            return indices_free_symbols


class VectorTestFunction(Symbol, IndexedBase):
    """
    Represents a vector test function as an element of a fem space.

    Examples

    """
    is_commutative = True
    _space = None
    def __new__(cls, space, name=None):
        if not(space.is_vector) and not(space.is_block):
            raise ValueError('Expecting a vector/block space')

        obj = Basic.__new__(cls, name)
        obj._space = space
        return obj

    @property
    def space(self):
        return self._space

    @property
    def name(self):
        return self._args[0]

    @property
    def shape(self):
        # we return a list to make it compatible with IndexedBase sympy object
        return [self.space.shape]

    def __getitem__(self, *args):

        if self.shape and len(self.shape) != len(args):
            raise IndexException("Rank mismatch.")

        if not(len(args) == 1):
            raise ValueError('expecting exactly one argument')

        assumptions ={}
        obj = IndexedTestTrial(self, *args)
        return obj

    def duplicate(self, name):
        return VectorTestFunction(self.space, name)


class Unknown(TestFunction):
    """
    Represents an unknown function

    """
    def __new__(cls, name, ldim):
        V = BasicSobolevSpace('V', ldim=ldim)
        return TestFunction.__new__(cls, V, name)

    @property
    def ldim(self):
        return self.space.ldim
