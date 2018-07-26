import hypothesis.strategies as st

from hypothesis import given
from annotation_abuse.notify import detect_classvars, inherits_init


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
