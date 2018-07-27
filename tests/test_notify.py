import hypothesis.strategies as st

from hypothesis import given
from annotation_abuse.notify import (
    detect_classvars,
    inherits_init,
    module_ast,
    build_func_cache,
    find_instvars,
    notify,
    interpret_resp,
    Response,
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


def test_finds_instvars():
    class DummyClass:
        def __init__(self):
            self.var1: "this one" = 1
            self.var2: "this one" = 2

    found = find_instvars(DummyClass)
    assert len(found) == 2
    assert found[0] == "var1"
    assert found[1] == "var2"


def test_intercepts_inst_writes(mocker):
    """#SPC-notify-intercept.tst-intercepts-inst"""
    # Pretend like the user rejected the new value
    mocker.patch("annotation_abuse.notify.prompt_user", lambda: False)

    @notify
    class DummyClass(object):
        def __init__(self):
            self.var: "this one" = 1

    dummy = DummyClass()
    assert dummy.var == 1
    dummy.var = 2
    # Write (hopefully) intercepted and rejected
    assert dummy.var == 1
    # Make sure the behavior responds to the user prompt
    mocker.patch("annotation_abuse.notify.prompt_user", lambda: True)
    dummy.var = 2
    assert dummy.var == 2


def test_intercepts_class_writes(mocker):
    """#SPC-notify-intercept.tst-intercepts-class"""
    # Pretend like the user rejected the new value
    mocker.patch("annotation_abuse.notify.prompt_user", lambda: False)

    @notify
    class DummyClass(object):
        var: "this one" = 1

    dummy = DummyClass()
    assert dummy.var == 1
    dummy.var = 2
    # Write (hopefully) intercepted and rejected
    assert dummy.var == 1
    # Make sure the behavior responds to the user prompt
    mocker.patch("annotation_abuse.notify.prompt_user", lambda: True)
    dummy.var = 2
    assert dummy.var == 2


def test_unmarked_inst_still_write(mocker):
    """#SPC-notify-inst.tst-unmarked-inst"""
    # Pretend like the user rejected the new value
    mocker.patch("annotation_abuse.notify.prompt_user", lambda: False)

    @notify
    class DummyClass(object):
        def __init__(self):
            self.var = 1

    dummy = DummyClass()
    assert dummy.var == 1
    dummy.var = 2
    # Write (hopefully) intercepted and rejected
    assert dummy.var == 2
    # Make sure the behavior responds to the user prompt
    mocker.patch("annotation_abuse.notify.prompt_user", lambda: True)
    dummy.var = 3
    assert dummy.var == 3


def test_unmarked_class_still_write(mocker):
    """#SPC-notify-inst.tst-unmarked-class"""
    # Pretend like the user rejected the new value
    mocker.patch("annotation_abuse.notify.prompt_user", lambda: False)

    @notify
    class DummyClass(object):
        var = 1

    dummy = DummyClass()
    assert dummy.var == 1
    dummy.var = 2
    # Write (hopefully) intercepted and rejected
    assert dummy.var == 2
    # Make sure the behavior responds to the user prompt
    mocker.patch("annotation_abuse.notify.prompt_user", lambda: True)
    dummy.var = 3
    assert dummy.var == 3


def test_prompt_accepts_yes():
    """#SPC-notify-intercept.tst-prompt-yes"""
    for text in Response.YES.value:
        assert interpret_resp(text) == Response.YES


def test_prompt_accepts_no():
    """#SPC-notify-intercept.tst-prompt-no"""
    for text in Response.NO.value:
        assert interpret_resp(text) == Response.NO


@given(text=st.text())
def test_prompt_detects_invalid(text):
    """#SPC-notify-intercept.tst-prompt-invalid"""
    resp = interpret_resp(text)
    assert resp == Response.INVALID
