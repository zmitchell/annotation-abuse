from annotation_abuse import asts
from pytest import raises


def test_rejects_funcs():
    """#SPC-asts.tst-reject-funcs"""
    def dummy_func(x):
        return x
    with raises(asts.MacroError):
        asts.inrange(dummy_func)


def test_rejects_methods():
    """#SPC-asts.tst-rejects-methods"""
    with raises(asts.MacroError):
        class DummyClass:
            @asts.inrange
            def dummy_method(self):
                return True


