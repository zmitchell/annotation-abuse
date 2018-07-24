from typing import List
from annotation_abuse.asts import inrange, InRangeProcessor, MacroError
from pytest import raises


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
