# coding: utf-8

import os

from sympde.parser import Parser

base_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(base_dir, 'data')

def test_1():
    # creates an instance of Vale parser
    pde = Parser()

    # parse the Vale code
    filename = os.path.join(data_dir, 'pde.vl')
    ast = pde.parse_from_file(filename)

test_1()