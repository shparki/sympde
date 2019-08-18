# coding: utf-8

from itertools import groupby

from sympy.core import Basic
from sympy.core import Symbol
from sympy.core import Function
from sympy.simplify.simplify import simplify
from sympy import collect
from sympy.series.order import Order
from sympy.core import Expr, Add, Mul, Pow
from sympy import S
from sympy import Dummy
from sympy.core.numbers import Zero as sy_Zero
from sympy.core.containers import Tuple
from sympy import Indexed, IndexedBase, Matrix, ImmutableDenseMatrix
from sympy import Integer, Float
from sympy.core.expr import AtomicExpr
from sympy.physics.quantum import TensorProduct
from sympy.series.series import series
from sympy.core.compatibility import is_sequence

from sympde.core.basic import _coeffs_registery
from sympde.core.basic import CalculusFunction
from sympde.core.basic import Constant
from sympde.core.algebra import (Dot_1d,
                 Dot_2d, Inner_2d, Cross_2d,
                 Dot_3d, Inner_3d, Cross_3d)
from sympde.core.utils import random_string

from sympde.calculus import Dot, Inner, Cross
from sympde.calculus import Grad, Rot, Curl, Div, Hessian
from sympde.calculus import Bracket
from sympde.calculus import Laplace
from sympde.calculus.core import _generic_ops

from sympde.topology import BasicDomain, Domain, MappedDomain, Union, Interval
from sympde.topology import BoundaryVector, NormalVector, TangentVector, Boundary, Connectivity
from sympde.topology.derivatives import _partial_derivatives
from sympde.topology.derivatives import partial_derivative_as_symbol
from sympde.topology.derivatives import sort_partial_derivatives
from sympde.topology.derivatives import get_atom_derivatives
from sympde.topology.derivatives import dx, dy, dz
from sympde.topology.derivatives import (Grad_1d, Div_1d,
                                         Grad_2d, Curl_2d, Rot_2d, Div_2d,
                                         Grad_3d, Curl_3d, Div_3d)
from sympde.topology.derivatives import Bracket_2d
from sympde.topology.derivatives import Laplace_1d, Laplace_2d, Laplace_3d
from sympde.topology.derivatives import Hessian_1d, Hessian_2d, Hessian_3d
from sympde.topology.space import BasicFunctionSpace
from sympde.topology.space import ScalarFunctionSpace
from sympde.topology.space import ProductSpace
from sympde.topology.space import ScalarTestFunction
from sympde.topology.space import VectorTestFunction
from sympde.topology.space import IndexedTestTrial
from sympde.topology.space import Unknown, VectorUnknown
from sympde.topology.space import Trace, trace_0, trace_1
from sympde.topology.space import ScalarField, VectorField, IndexedVectorField
from sympde.topology.measure import CanonicalMeasure
from sympde.topology.measure import CartesianMeasure
from sympde.topology.measure import Measure

from .errors import UnconsistentLinearExpressionError
from .basic import BasicForm
from .basic  import BasicExpr
from .basic  import is_linear_form, _sanitize_arguments

def expand(expr):
    from sympy import expand
    expr = expand(expr)
    _, args = expr.as_coeff_add()
    args = list(args)
    for i in range(len(args)):
        c,m = args[i].as_coeff_mul()
        for o in m:
            c = c*o
        args[i] = c
    return Add(*args)
#==============================================================================
def _get_domain(expr):
    # expr is an integral of BasicExpr or Add of Integral of BasicExpr
    if isinstance(expr, (DomainIntegral,BoundaryIntegral)):
        return expr.domain
    elif isinstance(expr, (Add,Mul)):
        domains = set()
        for a in expr.args:
            a = _get_domain(a)
            if isinstance(a, Union):
                domains = domains.union(a.args)
            elif isinstance(a, BasicDomain):
                domains = domains.union([a])
        if len(domains) == 1:
            return list(domains)[0]
        return Union(*domains)

#==============================================================================
class LinearExpr(BasicExpr):
    is_linear = True

    def __new__(cls, arguments, expr, check=False):

        # ...
        if expr.atoms(DomainIntegral, BoundaryIntegral):
            raise TypeError('')
        # ...

        # ...
        if check and not is_linear_form(expr, arguments):
            msg = '> Expression is not linear'
            raise UnconsistentLinearExpressionError(msg)
        # ...

        args = _sanitize_arguments(arguments, is_linear=True)
        return Basic.__new__(cls, args, expr)

    @property
    def variables(self):
        return self._args[0]

    @property
    def expr(self):
        return self._args[1]

    def __call__(self, *args):
        args = _sanitize_arguments(args, is_linear=True)
        args = Tuple(*args)
        expr, _ =  self.expr._xreplace(dict(list(zip(self.variables, args))))
        return expr

    def _eval_nseries(self, x, n, logx):
        return self.expr._eval_nseries(x, n, logx)

#==============================================================================
class BilinearExpr(BasicExpr):
    is_bilinear = True

    def __new__(cls, arguments, expr, check=False):

        # ...
        if expr.atoms(DomainIntegral, BoundaryIntegral):
            raise TypeError('')
        # ...

        # ...
        if not isinstance(arguments, (tuple, list, Tuple)):
            raise TypeError('(trial, test) must be a tuple, list or Tuple')

        if not(len(arguments) == 2):
            raise ValueError('Expecting a couple (trial, test)')
        # ...

        # ...
        if check and not is_bilinear_form(expr, arguments):
            msg = '> Expression is not bilinear'
            raise UnconsistentLinearExpressionError(msg)
        # ...

        args = _sanitize_arguments(arguments, is_bilinear=True)
        return Basic.__new__(cls, args, expr)

    @property
    def variables(self):
        return self._args[0]

    @property
    def expr(self):
        return self._args[1]

    def __call__(self, *args):
        args = _sanitize_arguments(args, is_bilinear=True)
        left,right = args
        if not is_sequence(left):
            left = [left]

        if not is_sequence(right):
            right = [right]

        args = Tuple(*left, *right)

        variables = Tuple(*self.variables[0], *self.variables[1])
        return self.expr.xreplace(dict(list(zip(self.variables, args))))


#==============================================================================
class Integral(CalculusFunction):

    def __new__(cls, expr, domain, **options):
        # (Try to) sympify args first

        assert isinstance(domain, BasicDomain)
        return Integral.eval(expr, domain)

    @staticmethod
    def eval(expr, domain):
        """."""

        if not isinstance(expr, (BasicExpr, Expr)):
            raise TypeError('')

        if isinstance(expr, sy_Zero):
            return sy_Zero
            
        if isinstance(expr, BasicExpr):
            expr = expr.expr
            
        if isinstance(expr, Add):
            args = [Integral.eval(a, domain) for a in expr.args]
            return Add(*args)
            
        if isinstance(domain, Union):
            expr = [Integral.eval(expr, d) for d in domain.args]
            return Add(*expr)
                
        if isinstance(domain, (Boundary, Connectivity)):
            return BoundaryIntegral(expr, domain)

        else:
            return DomainIntegral(expr, domain)
            
            

#==============================================================================

class DomainIntegral(AtomicExpr):
    _op_priority = 20
    @property
    def expr(self):
        return self._args[0]
    @property
    def domain(self):
        return self._args[1]       

    def __mul__(self, o):
        return DomainIntegral(self.expr*o, self.domain)
        
    def __rmul__(self, o):
        return DomainIntegral(self.expr*o, self.domain)

    def __eq__(self, a):
        if isinstance(a, DomainIntegral):
            eq = self.domain == a.domain
            eq = eq and self.expr == a.expr
            return eq
        return False
        
    def __hash__(self):
        return hash(self.expr) + hash(self.domain)
#==============================================================================
class BoundaryIntegral(AtomicExpr):
    _op_priority = 20
    
    def __new__(cls, expr, domain):
    
        atoms_1 = list(expr.atoms(Dot,Trace))
        
        for i in range(len(atoms_1)):
            a = atoms_1[i]
            if isinstance(a, Dot):
                if not isinstance(a.args[0], NormalVector):
                    if not isinstance(a.args[1], NormalVector):
                        atoms_1.remove(a)
                
        subs_1  = {a:Dummy() for a in atoms_1}
        expr, _ = expr._xreplace(subs_1)

        atoms_2 = expr.atoms(ScalarTestFunction, VectorTestFunction)
        subs_2  = {a:trace_0(a, domain) for a in atoms_2}
        expr, _ = expr._xreplace(subs_2)
        
        subs_3 = {}
        
        for key,val in subs_1.items():
            
            if isinstance(key, Dot):
                args = key.args
                if isinstance(args[0], NormalVector):
                    v = args[1]
                elif isinstance(args[1], NormalVector):
                    v = args[0]
                subs_3[val] = trace_1(v, domain)
            else:
                subs_3[val] = key
         
        expr, _ = expr._xreplace(subs_3)
        
        
        return Basic.__new__(cls, expr, domain)
        

    @property
    def expr(self):
        return self._args[0]
    @property
    def domain(self):
        return self._args[1]
        
    def __mul__(self, o):
        return BoundaryIntegral(self.expr*o, self.domain)
        
    def __rmul__(self, o):
        return BoundaryIntegral(self.expr*o, self.domain)
        
    def __eq__(self, a):
        if isinstance(a, BoundaryIntegral):
            eq = self.domain == a.domain
            eq = eq and self.expr == a.expr
            return eq
        return False
        
    def __hash__(self):
        return hash(self.expr) + hash(self.domain)
        
#==============================================================================
class Functional(BasicForm):
    is_functional = True

    def __new__(cls, expr, domain, eval=True):

        if eval:
            expr = Integral(expr, domain)
        obj = Basic.__new__(cls, expr, domain)

        # compute dim from fields if available
        ls = list(expr.atoms((ScalarField, VectorField)))
        if ls:
            F = ls[0]
            space = F.space

        else:
            tag = random_string( 3 )
            space_name = 'space_{}'.format(tag)
            space = ScalarFunctionSpace(space_name, domain)
            # TODO vector case

        obj._ldim = domain.dim
        obj._space = space

        return obj

    @property
    def expr(self):
        return self._args[0]

    @property
    def domain(self):
        return self._args[1]

    @property
    def coordinates(self):
        return self.domain.coordinates

    @property
    def space(self):
        return self._space

    # TODO do we need it?
#    def _eval_nseries(self, x, n, logx):
#        return self.expr._eval_nseries(x, n, logx)


#==============================================================================
class LinearForm(BasicForm):
    is_linear = True

    def __new__(cls, arguments, expr):

        # ...
        integrals = expr.atoms(DomainIntegral, BoundaryIntegral)
        if not integrals:
            raise ValueError('Expecting integral Expression')
        # ...

        if expr == 0:
            return sy_Zero
        
        expr = expand(expr)
            

        domain = _get_domain(expr)
        args = _sanitize_arguments(arguments, is_linear=True)
        obj = Basic.__new__(cls, args, expr)

        # ...
        obj._domain = domain
        # ...
        return obj

    @property
    def variables(self):
        return self._args[0]

    @property
    def expr(self):
        return self._args[1]

    @property
    def body(self):
        if self._body is None:
            expr = self.expr
            integrals = expr.atoms(DomainIntegral)
            if integrals:
                for integral in integrals:
                    expr = expr.subs(integral, integral.expr)

            self._body = expr

        return self._body

    @property
    def test_functions(self):
        return self.variables

    @property
    def test_spaces(self):
        return [u.space for u in self.test_functions]

    @property
    def coordinates(self):
        return self.test_spaces[0].coordinates

    @property
    def ldim(self):
        return self.test_spaces[0].ldim

    def __call__(self, *args, **kwargs):

        # ... use free variables if given and available
        expr = self._update_free_variables(**kwargs)
        # ...

        # ...
        args = Tuple(*args)
        variables = self.variables

        subs    = dict(zip(variables, args))
        expr, _ = expr._xreplace(subs)
        # ...
        return expr


#==============================================================================
class BilinearForm(BasicForm):
    is_bilinear = True
    _is_symmetric = None

    def __new__(cls, arguments, expr):

        # ...
        integrals = expr.atoms(DomainIntegral,BoundaryIntegral)
        if not integrals:
            raise ValueError('Expecting integral Expression')
            
        domain = _get_domain(expr)

        # ...
        if expr == 0:
            return sy_Zero
            
        expr = expand(expr)
        
        args = _sanitize_arguments(arguments, is_bilinear=True)
        obj = Basic.__new__(cls, args, expr)
        # ...
        
        obj._domain = domain
        # ...
        return obj

    @property
    def variables(self):
        return self._args[0]

    @property
    def expr(self):
        return self._args[1]

    @property
    def body(self):
        if self._body is None:
            expr = self.expr
            integrals = expr.atoms(DomainIntegral)
            if integrals:
                for integral in integrals:
                    expr = expr.subs(integral, integral._args[0])

            self._body = expr

        return self._body

    @property
    def test_functions(self):
        return self.variables[1]

    @property
    def trial_functions(self):
        return self.variables[0]

    @property
    def test_spaces(self):
        return [u.space for u in self.test_functions]

    @property
    def trial_spaces(self):
        return [u.space for u in self.trial_functions]

    @property
    def coordinates(self):
        return self.test_spaces[0].coordinates

    @property
    def ldim(self):
        return self.test_spaces[0].ldim

    @property
    def is_symmetric(self):
        if self._is_symmetric is None:
            left, right = self.variables
            a1 = self(left, right)
            a2 = self(right, left)
            a1 = expand(a1)
            a2 = expand(a2)
#            print(a1)
#            print(a2)
            value = a1 == a2

            self._is_symmetric = value

        return self._is_symmetric

    def __call__(self, *args, **kwargs):

        # ... use free variables if given and available
        expr = self._update_free_variables(**kwargs)
        # ...

        # ...
        assert(len(args) == 2)
        
        new_args = []
        
        for arg in args:
            
            if is_sequence(arg):
                new_args += list(arg)
            else:
                new_args.append(arg) 
            
        args = Tuple(*new_args)

        variables = Tuple(*self.variables[0], *self.variables[1])
        subs      = dict(zip(variables, args))
        expr, _   = expr._xreplace(subs)
        # ...

        return expr

#==============================================================================
class Norm(Functional):
    is_norm = True

    def __new__(cls, expr, domain, kind='l2', eval=True):
#        # ...
#        tests = expr.atoms((ScalarTestFunction, VectorTestFunction))
#        if tests:
#            msg = '> Expecting an Expression without test functions'
#            raise UnconsistentArgumentsError(msg)
#
#        if not isinstance(expr, (Expr, Matrix, ImmutableDenseMatrix)):
#            msg = '> Expecting Expr, Matrix, ImmutableDenseMatrix'
#            raise UnconsistentArgumentsError(msg)
#        # ...

        # ...
        if not(kind in ['l2', 'h1', 'h2']):
            raise ValueError('> Only L2, H1, H2 norms are available')
        # ...

        # ...
        is_vector = isinstance(expr, (Matrix, Tuple, list, tuple))
        if is_vector:
            expr = Matrix(expr)
        # ...

        # ...
        exponent = None
        if kind == 'l2' and eval:
            exponent = 2

            if not is_vector:
                expr = expr*expr

            else:
                if not( expr.shape[1] == 1 ):
                    raise ValueError('Wrong expression for Matrix. must be a row')

                v = Tuple(*expr[:,0])
                expr = Dot(v, v)

        elif kind == 'h1'and eval :
            exponent = 2

            if not is_vector:
                expr = Dot(Grad(expr), Grad(expr))

            else:
                if not( expr.shape[1] == 1 ):
                    raise ValueError('Wrong expression for Matrix. must be a row')

                v = Tuple(*expr[:,0])
                expr = Inner(Grad(v), Grad(v))
                
        elif kind == 'h2'and eval :
            exponent = 2

            if not is_vector:
                expr = Dot(Hessian(expr), Hessian(expr))
                
            else:
                raise NotImplementedError('TODO')
        # ...

        obj = Functional.__new__(cls, expr, domain, eval=eval)
        obj._exponent = exponent

        return obj

    @property
    def exponent(self):
        return self._exponent


#==============================================================================
def linearize(form, fields, trials=None):
    """linearize a LinearForm around the fields."""
    # ...
    #TODO add LinearForm
    if not isinstance(form, (LinearForm, LinearExpr)):
        raise TypeError('> Expecting a LinearForm')

    if not isinstance(fields, (list, tuple, Tuple)):
        fields = [fields]
        
    fields = [f.space.field(str(f.name)) for f in fields]
    form   = form.annotate()

    for f in fields:
        
        if not isinstance(f, (ScalarField, VectorField)):
            raise TypeError('{} is not ScalarField/VectorField'.format(f))

    if not(trials is None):
        if not isinstance(trials, (list, tuple, Tuple)):
            trials = [trials]

        assert( all([isinstance(i, (str, ScalarTestFunction, VectorTestFunction)) for i in trials]) )
        assert( len(fields) == len(trials) )

        newtrials = []
        for i in trials:
            if isinstance(i, (ScalarTestFunction, VectorTestFunction)):
                newtrials += [i.name]

            else:
                newtrials += [i]

        trials = newtrials
    # ...

    if isinstance(form, LinearForm):
        is_form = True
        expr = form.body
        domain = form.domain

    else:
        is_form = False
        expr = form.expr

    test_functions = form.variables
    fields         = Tuple(*fields)

    # ...
    trial_functions = []
    newargs         = []
    eps  = Constant('eps_' + random_string( 4 ))
    for i,x in enumerate(fields):
        tag  = random_string( 4 )

        if trials is None:
            name = x.name + '_' + tag
        else:
            name = trials[i]

        if isinstance(x, ScalarField):
            trial  = ScalarTestFunction(x.space, name=name)

        elif isinstance(x, VectorField):
            trial  = VectorTestFunction(x.space, name=name)

        else:
            raise TypeError('Only ScalarTestFunction , VectorTestFunction  are available')

        newargs         += [x + eps*trial]
        trial_functions += [trial]
    # ...

    # ...
    newexpr = expr
    for k,v in zip(fields, newargs):
        newexpr = newexpr.subs(k,v)
    # ...

    newexpr = expand(newexpr)

    e = newexpr.series(eps, 0, 2)
    d = collect(e, eps, evaluate=False)
    expr = d[eps]

#    print('> linearize = ', expr)
#    import sys; sys.exit(0)

    test_trial = (trial_functions, test_functions)

    if is_form:
        return BilinearForm(test_trial, integral(domain, expr))

    else:
        return BilinearExpr(test_trial, expr)
        
def integral(domain, expr):
    """."""
    return Integral(expr, domain)
