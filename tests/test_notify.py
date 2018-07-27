import hypothesis.strategies as st

from hypothesis import given
from annotation_abuse.notify import (
    detect_classvars,
    inherits_init,
    module_ast,
    build_func_cache,
)


def test_accepts_marked_classvars():
    """#SPC-notify.tst-marked-classvars"""

    class DummyClass:
        var1: "this one"
        var2: "this one"

    extracted = detect_classvars(DummyClass)
    assert len(extracted) == 2
    assert extracted[0] == "var1"
    assert extracted[1] == "var2"


@given(annotation=st.text())
def test_ignores_arbitrary_annotations(annotation):
    """#SPC-notify.tst-arb-ann"""

    class DummyClass:
        var: f"{annotation}"

    extracted = detect_classvars(DummyClass)
    assert len(extracted) == 0


def test_detects_class_init():
    """#SPC-notify-inst.tst-impl-init"""

    class DummyClass:
        def __init__(self):
            self.x = 1

    assert not inherits_init(DummyClass)


def test_detects_inherited_init():
    """#SPC-notify-inst.tst-inherits-init"""

    class DummyClass:
        var = 0

    assert inherits_init(DummyClass)


def test_detects_tests():
    """#SPC-notify-inst.tst-detects-tests"""

    class DummyClass:
        def __init__(self, x):
            self.x = x

    test_mod_ast = module_ast(DummyClass)
    cache = build_func_cache(test_mod_ast)
    test_funcs = [
        func_name
        for func_name in test_detects_tests.__globals__
        if func_name.startswith("test_")
    ]
    for func_name in test_funcs:
        test_lineno = test_detects_tests.__globals__[func_name].__code__.co_firstlineno
        assert test_lineno in cache.keys()
