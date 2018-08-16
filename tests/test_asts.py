import hypothesis.strategies as st

from ast import Compare
from math import isinf, isnan
from typing import List
from annotation_abuse.asts import (
    inrange,
    MacroError,
    collect_vars,
    parse,
    extract_endpoints,
)
from hypothesis import given, assume
from pytest import raises


sorted_int_endpoints = st.tuples(st.integers(), st.integers()).map(sorted)
sorted_float_endpoints = st.tuples(st.floats(), st.floats()).map(sorted)


def test_rejects_funcs():
    """#SPC-asts.tst-rejects_funcs"""

    def dummy_func(x):
        return x

    with raises(MacroError):
        inrange(dummy_func)


def test_rejects_methods():
    """#SPC-asts.tst-rejects_methods"""
    with raises(MacroError):

        class DummyClass:
            @inrange
            def dummy_method(self):
                return True


def test_rejects_no_annotations():
    """#SPC-asts.tst-no_annotations"""

    class DummyClass:
        var = 1

    with raises(MacroError):
        inrange(DummyClass)


def test_rejects_no_strings():
    """#SPC-asts.tst-no_strings"""

    class DummyClass:
        var1: int
        var2: List

    with raises(MacroError, match="annotations must be strings"):
        collect_vars(DummyClass)


def test_accepts_mixed_annotations():
    """#SPC-asts.tst-mixed_strings"""

    class DummyClass:
        var1: "arbitrary string"
        var2: int

    items = collect_vars(DummyClass)
    assert len(items) == 1


@given(annotation=st.text())
def test_rejects_malformed_annotation(annotation):
    """#SPC-asts.tst-not_comparison"""

    class DummyClass:
        var: f"{annotation}"

    items = collect_vars(DummyClass)
    with raises(MacroError):
        parse(items[0])


def test_accepts_comparison():
    """#SPC-asts.tst-comparison"""

    class DummyClass:
        var: "0 < var < 1"

    items = collect_vars(DummyClass)
    comp_node = parse(items[0])
    assert type(comp_node) is Compare


@given(endpoints=sorted_int_endpoints)
def test_accepts_valid_int_endpoints(endpoints):
    """#SPC-asts.tst-valid_ints"""
    lower = endpoints[0]
    upper = endpoints[1]
    assume(lower != upper)
    for e in endpoints:
        assume(not isinf(e))
        assume(not isnan(e))

    class DummyClass:
        var: f"{lower} < var < {upper}"

    items = collect_vars(DummyClass)
    comp_node = parse(items[0])
    ext_lower, ext_upper = extract_endpoints(comp_node)
    assert lower == ext_lower
    assert upper == ext_upper


@given(endpoints=sorted_float_endpoints)
def test_accepts_valid_float_endpoints(endpoints):
    """#SPC-asts.tst-valid_floats"""
    lower = endpoints[0]
    upper = endpoints[1]
    assume(lower != upper)
    for e in endpoints:
        assume(not isinf(e))
        assume(not isnan(e))

    class DummyClass:
        var: f"{lower} < var < {upper}"

    items = collect_vars(DummyClass)
    comp_node = parse(items[0])
    ext_lower, ext_upper = extract_endpoints(comp_node)
    assert lower == ext_lower
    assert upper == ext_upper


@given(endpoints=sorted_float_endpoints)
def test_rejects_inf_nan(endpoints):
    """#SPC-asts.tst-rejects_inf_nan"""
    # Make sure that one of the endpoints is `inf` or `nan`
    assume(any(map(lambda x: isnan(x) or isinf(x), endpoints)))
    lower = endpoints[0]
    upper = endpoints[1]

    class DummyClass:
        var: f"{lower} < var < {upper}"

    items = collect_vars(DummyClass)
    comp_node = parse(items[0])
    with raises(MacroError, match="is not a valid range endpoint"):
        extract_endpoints(comp_node)


@given(endpoints=sorted_float_endpoints)
def test_rejects_out_of_order_endpoints(endpoints):
    """#SPC-asts.tst-order"""
    lower = endpoints[1]  # note that this is backwards!
    upper = endpoints[0]
    assume(lower != upper)
    for e in endpoints:
        assume(not isinf(e))
        assume(not isnan(e))

    class DummyClass:
        var: f"{lower} < var < {upper}"

    items = collect_vars(DummyClass)
    comp_node = parse(items[0])
    with raises(MacroError, match="must be less than"):
        extract_endpoints(comp_node)


@given(endpoint=st.integers())
def test_rejects_equal_endpoints(endpoint):
    """#SPC-asts.tst-equal"""
    assume(not isinf(endpoint))

    class DummyClass:
        var: f"{endpoint} < var < {endpoint}"

    items = collect_vars(DummyClass)
    comp_node = parse(items[0])
    with raises(MacroError, match="must be less than"):
        extract_endpoints(comp_node)


@given(val=st.floats(min_value=0.001, max_value=0.999))
def test_accepts_in_range(val):
    """#SPC-asts.tst-in_range"""

    @inrange
    class DummyClass:
        var: "0 < var < 1"

    dummy = DummyClass()
    dummy.var = val


def test_rejects_outside_range():
    """#SPC-asts.tst-outside_range"""

    @inrange
    class DummyClass:
        var: "0 < var < 1"

    dummy = DummyClass()
    with raises(ValueError):
        dummy.var = 2


def test_init_stmts_added():
    """#SPC-asts.tst-init_stmts"""

    @inrange
    class DummyClass:
        var: "0 < var < 2"

    dummy = DummyClass()
    assert dummy._var is None
    dummy.var = 1
    assert dummy._var == 1
