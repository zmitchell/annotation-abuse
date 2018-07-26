import hypothesis.strategies as st

from hypothesis import given
from annotation_abuse.notify import detect_classvars


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
