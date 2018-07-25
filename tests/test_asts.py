import hypothesis.strategies as st

from ast import Compare
from math import isinf, isnan
from typing import List
from annotation_abuse.asts import inrange, InRangeProcessor, MacroError
from hypothesis import given, assume
from pytest import raises


sorted_int_endpoints = st.tuples(st.integers(), st.integers()).map(sorted)
sorted_float_endpoints = st.tuples(st.floats(), st.floats()).map(sorted)


def test_rejects_funcs():
    """#SPC-asts.tst-reject-funcs"""

    def dummy_func(x):
        return x

    with raises(MacroError):
        inrange(dummy_func)


def test_rejects_methods():
    """#SPC-asts.tst-rejects-methods"""
    with raises(MacroError):

        class DummyClass:
            @inrange
            def dummy_method(self):
                return True


def test_rejects_no_annotations():
    """#SPC-asts.tst-no-annotations"""

    class DummyClass:
        var = 1

    with raises(MacroError):
        inrange(DummyClass)


def test_rejects_no_strings():
    """#SPC-asts-proc.tst-no-strings"""

    class DummyClass:
        var1: int
        var2: List

    proc = InRangeProcessor(DummyClass)
    with raises(MacroError, match="annotations must be strings"):
        proc._collect()


def test_accepts_mixed_annotations():
    """#SPC-asts-proc.tst-mixed-strings"""

    class DummyClass:
        var1: "arbitrary string"
        var2: int

    proc = InRangeProcessor(DummyClass)
    proc._collect()
    assert len(proc._items) == 1


@given(annotation=st.text())
def test_rejects_malformed_annotation(annotation):
    """#SPC-asts-proc.tst-not-comparison"""

    class DummyClass:
        var: f"{annotation}"

    proc = InRangeProcessor(DummyClass)
    proc._collect()
    with raises(MacroError):
        proc._parse(proc._items[0])


def test_accepts_comparison():
    """#SPC-asts-proc.tst-comparison"""

    class DummyClass:
        var: "0 < var < 1"

    proc = InRangeProcessor(DummyClass)
    proc._collect()
    comp_node = proc._parse(proc._items[0])
    assert type(comp_node) is Compare


@given(endpoints=sorted_int_endpoints)
def test_accepts_valid_int_endpoints(endpoints):
    """#SPC-asts-proc.tst-valid-ints"""
    lower = endpoints[0]
    upper = endpoints[1]
    assume(lower != upper)
    for e in endpoints:
        assume(not isinf(e))
        assume(not isnan(e))

    class DummyClass:
        var: f"{lower} < var < {upper}"

    proc = InRangeProcessor(DummyClass)
    proc._collect()
    comp_node = proc._parse(proc._items[0])
    ext_lower, ext_upper = proc._extract_endpoints(comp_node)
    assert lower == ext_lower
    assert upper == ext_upper


@given(endpoints=sorted_float_endpoints)
def test_accepts_valid_float_endpoints(endpoints):
    """#SPC-asts-proc.tst-valid-floats"""
    lower = endpoints[0]
    upper = endpoints[1]
    assume(lower != upper)
    for e in endpoints:
        assume(not isinf(e))
        assume(not isnan(e))

    class DummyClass:
        var: f"{lower} < var < {upper}"

    proc = InRangeProcessor(DummyClass)
    proc._collect()
    comp_node = proc._parse(proc._items[0])
    ext_lower, ext_upper = proc._extract_endpoints(comp_node)
    assert lower == ext_lower
    assert upper == ext_upper


@given(endpoints=sorted_float_endpoints)
def test_rejects_inf_nan(endpoints):
    """#SPC-asts-proc.tst-rejects-inf-nan"""
    # Make sure that one of the endpoints is `inf` or `nan`
    assume(any(map(lambda x: isnan(x) or isinf(x), endpoints)))
    lower = endpoints[0]
    upper = endpoints[1]

    class DummyClass:
        var: f"{lower} < var < {upper}"

    proc = InRangeProcessor(DummyClass)
    proc._collect()
    comp_node = proc._parse(proc._items[0])
    with raises(MacroError, match="is not a valid range endpoint"):
        proc._extract_endpoints(comp_node)


@given(endpoints=sorted_float_endpoints)
def test_rejects_out_of_order_endpoints(endpoints):
    """#SPC-asts-proc.tst-order"""
    lower = endpoints[1]  # note that this is backwards!
    upper = endpoints[0]
    assume(lower != upper)
    for e in endpoints:
        assume(not isinf(e))
        assume(not isnan(e))

    class DummyClass:
        var: f"{lower} < var < {upper}"

    proc = InRangeProcessor(DummyClass)
    proc._collect()
    comp_node = proc._parse(proc._items[0])
    with raises(MacroError, match="must be less than"):
        proc._extract_endpoints(comp_node)


@given(endpoint=st.integers())
def test_rejects_equal_endpoints(endpoint):
    """#SPC-asts-proc.tst-equal"""
    assume(not isinf(endpoint))

    class DummyClass:
        var: f"{endpoint} < var < {endpoint}"

    proc = InRangeProcessor(DummyClass)
    proc._collect()
    comp_node = proc._parse(proc._items[0])
    with raises(MacroError, match="must be less than"):
        proc._extract_endpoints(comp_node)
