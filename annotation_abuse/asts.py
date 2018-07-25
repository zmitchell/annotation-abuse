import ast
from ast import (
    Compare,
    Num,
    UnaryOp,
    USub,
    Name,
    arg,
    arguments,
    Attribute,
    Return,
    FunctionDef,
    Module,
)


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
        self.init_stmt = None


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

    @staticmethod
    def _extract_endpoints(node):
        """Extract the range's endpoints from the `ast.Compare` node.

        partof: #SPC-asts-proc.extract
        """
        if len(node.comparators) != 2:
            raise MacroError("Invalid number of comparisons")
        left_node = node.left
        right_node = node.comparators[1]
        lower = InRangeProcessor._num_from_node(left_node)
        upper = InRangeProcessor._num_from_node(right_node)
        if lower >= upper:
            raise MacroError("Left endpoint must be less than right endpoint")
        return lower, upper

    @staticmethod
    def _num_from_node(node):
        if type(node) is Num:  # catches numeric literals i.e. '5'
            value = node.n
        elif type(node) is UnaryOp:
            if type(node.op) is USub:  # catches i.e. '-5'
                if type(node.operand) is Num:
                    value = -node.operand.n
                elif type(node.operand) is Name:
                    if node.operand.id in ["inf", "nan", "NaN"]:
                        raise MacroError(
                            f"{node.operand.id} is not a valid range endpoint"
                        )
                    else:
                        raise MacroError("Only literals may be used as range endpoints")
            else:
                value = node.operand.n
        elif type(node) is Name:
            if node.id in ["inf", "nan", "NaN"]:
                raise MacroError(f"{node.id} is not a valid range endpoint")
            else:
                raise MacroError("Only literals may be used as range endpoints")
        return value

    @staticmethod
    def _ast_to_func(node, name):
        """Convert an `ast.FunctionDef` node into a callable object.

        partof: #SPC-asts-proc.ast-func
        """
        ast.fix_missing_locations(node)
        code = compile(node, __file__, "exec")
        context = {}
        exec(code, globals(), context)
        return context[name]

    @staticmethod
    def _getter(item):
        """Construct the AST for the getter function.

        partof: #SPC-asts-proc.getter
        """
        func_name = f"{item.var}_getter"
        self_arg = arg(arg="self", annotation=None)
        func_args = arguments(
            args=[self_arg],
            kwonlyargs=[],
            vararg=None,
            kwarg=None,
            defaults=[],
            kw_defaults=[],
        )
        inst_var = Attribute(
            value=Name(id="self", ctx=ast.Load()), attr=f"_{item.var}", ctx=ast.Load()
        )
        ret_stmt = Return(value=inst_var)
        func_node = FunctionDef(
            name=func_name,
            args=func_args,
            body=ret_stmt,
            decorator_list=[],
            returns=None,
        )
        mod_node = Module(body=[func_node])
        return InRangeProcessor._ast_to_func(mod_node, func_name)

    @staticmethod
    def _setter_body(item):
        """Construct the body of the setter function.
        """
        new_value = Name(id="new", ctx=ast.Load())
        inst_var = Attribute(
            value=Name(id="self", ctx=ast.Load()), attr=f"_{item.var}", ctx=ast.Store()
        )
        comp_node = Compare(
            left=Num(n=item.lower),
            ops=[ast.Lt(), ast.Lt()],
            comparators=[new_value, Num(n=item.upper)],
        )
        assign_stmt = ast.Assign(targets=[inst_var], value=new_value)
        except_msg = f"value outside of range {item.lower} < {item.var} < {item.upper}"
        exc = ast.Call(
            func=Name(id="ValueError", ctx=ast.Load()),
            args=[ast.Str(s=except_msg)],
            keywords=[],
        )
        else_body = ast.Raise(exc=exc, cause=None)
        if_node = ast.If(test=comp_node, body=[assign_stmt], orelse=[else_body])
        return if_node

    @staticmethod
    def _setter(item):
        func_name = f"{item.var}_setter"
        self_arg = arg(arg="self", annotation=None)
        new_arg = arg(arg="new", annotation=None)
        func_args = arguments(
            args=[self_arg, new_arg],
            kwonlyargs=[],
            vararg=None,
            kwarg=None,
            defaults=[],
            kw_defaults=[],
        )
        func_node = FunctionDef(
            name=func_name,
            args=func_args,
            body=[InRangeProcessor._setter_body(item)],
            decorator_list=[],
            returns=None,
        )
        mod_node = Module(body=[func_node])
        return InRangeProcessor._ast_to_func(mod_node, func_name)
