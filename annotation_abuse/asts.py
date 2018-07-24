import ast
from ast import Compare


def inrange(cls):
    """Generate properties that can be set in specified ranges.

    partof: #SPC-asts.decorator
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


class MacroItem:

    """
    Container for a single class variable processed by the macro.

    partof: #SPC-asts-proc.item

    """

    def __init__(self, var_name, annotation):
        self.var = var_name
        self.annotation = annotation
        self.lower = None
        self.upper = None
        self.getter = None
        self.setter = None


class InRangeProcessor:

    """
    A class that generates new properties based on class variable annotations.

    partof: #SPC-asts-proc

    """

    def __init__(self, cls):
        """Store the class that the macro is processing.

        partof: #SPC-asts-proc.proc
        """
        self._cls = cls
        self._items = []
        self._cls_fname = None
        self._mod_ast = None
        self._new_props = []
        self._new_init_stmts = []

    def _collect(self):
        """Collect the class variables to process.

        partof: #SPC-asts-proc.collect
        """
        for field, ann in self._cls.__annotations__.items():
            if type(ann) is not str:
                continue
            self._items.append(MacroItem(field, ann))
        if len(self._items) == 0:
            raise MacroError(
                "No acceptable annotations found, macro annotations must be strings"
            )

    @staticmethod
    def _parse(item):
        """Parse the annotation, returning the Compare node.

        An annotation of the form '0 < x < 1` will be parsed into an `ast.Module` node,
        whose `body` field contains a single item. The item in `body` is an `ast.Expr`
        node whose `value` is an `ast.Compare` node.

        :param MacroItem item: A MacroItem whose annotation should be parsed.
        :raises MacroError if the annotation is malformed
        :rtype ast.Compare

        partof: #SPC-asts-proc.parse
        """
        try:
            mod = ast.parse(item.annotation)
        except (SyntaxError, ValueError):
            raise MacroError(f"Invalid annotation: {item.annotation}")
        if len(mod.body) == 0:
            raise MacroError("Invalid annotation")
        expr_node = mod.body[0]
        comp_node = expr_node.value
        if type(comp_node) is not Compare:
            raise MacroError(f"Invalid annotation: {item.annotation}")
        return comp_node
