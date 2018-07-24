def inrange(cls):
    """Generate properties that can be set in specified ranges.

    partof: #SPC-ast.decorator
    """
    if type(cls) is not type:
        raise MacroError("'inrange' may only be applied to class definitions")
    try:
        cls.__annotations__
    except AttributeError:
        raise MacroError("No annotations found")


class MacroError(Exception):
    """Exception raised when a macro encounters an error.
    """

    pass


class InRangeProcessor:

    """
    A class that generates new properties based on class variable annotations.

    partof: #SPC-ast-proc

    """

    pass
