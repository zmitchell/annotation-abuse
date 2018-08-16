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

    partof:
      - #SPC-asts
      - #SPC-asts.decorator
    """
    if type(cls) is not type:
        raise MacroError("'inrange' may only be applied to class definitions")
    try:
        cls.__annotations__
    except AttributeError:
        raise MacroError("No annotations found")
    return produce(cls)


class MacroError(Exception):
    """Exception raised when a macro encounters an error.
    """

    pass


class MacroItem:

    """
    Container for a single class variable processed by the macro.

    partof: #SPC-asts.item

    """

    def __init__(self, var_name, annotation):
        self.var = var_name
        self.annotation = annotation
        self.lower = None
        self.upper = None
        self.getter = None
        self.setter = None
        self.init_stmt = None


def collect_vars(cls):
    """Collect the class variables to process.

    partof: #SPC-asts.collect
    """
    items = []
    for field, ann in cls.__annotations__.items():
        if type(ann) is not str:
            continue
        items.append(MacroItem(field, ann))
    if len(items) == 0:
        raise MacroError(
            "No acceptable annotations found, macro annotations must be strings"
        )
    return items


def parse(item):
    """Parse the annotation, returning the Compare node.

    An annotation of the form '0 < x < 1` will be parsed into an `ast.Module` node,
    whose `body` field contains a single item. The item in `body` is an `ast.Expr`
    node whose `value` is an `ast.Compare` node.

    partof: #SPC-asts.parse
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


def extract_endpoints(node):
    """Extract the range's endpoints from the `ast.Compare` node.

    partof: #SPC-asts.extract
    """
    if len(node.comparators) != 2:
        raise MacroError("Invalid number of comparisons")
    left_node = node.left
    right_node = node.comparators[1]
    lower = num_from_node(left_node)
    upper = num_from_node(right_node)
    if lower >= upper:
        raise MacroError("Left endpoint must be less than right endpoint")
    return lower, upper


def num_from_node(node):
    """Extract a number from one end of the range AST.

    The number '5' is `ast.Num(n=5)`, but '-5' is
    `ast.UnaryOp(op=ast.USub(), operand=ast.Num(n=5)`, which is much more complicated.
    """
    if type(node) is Num:  # catches numeric literals i.e. '5'
        value = node.n
    elif type(node) is UnaryOp:
        if type(node.op) is USub:  # catches i.e. '-5'
            if type(node.operand) is Num:
                value = -node.operand.n
            elif type(node.operand) is Name:
                if node.operand.id in ["inf", "nan", "NaN"]:
                    raise MacroError(f"{node.operand.id} is not a valid range endpoint")
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


def ast_to_func(node, name):
    """Convert an `ast.FunctionDef` node into a callable object.

    partof: #SPC-asts.ast2func
    """
    ast.fix_missing_locations(node)
    code = compile(node, __file__, "exec")
    context = {}
    exec(code, globals(), context)
    return context[name]


def getter(item):
    """Construct the getter function.

    partof: #SPC-asts.getter
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
        name=func_name, args=func_args, body=[ret_stmt], decorator_list=[], returns=None
    )
    mod_node = Module(body=[func_node])
    return ast_to_func(mod_node, func_name)


def setter_body(item):
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


def setter(item):
    """Construct the setter function.

    partof: #SPC-asts.setter
    """
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
        body=[setter_body(item)],
        decorator_list=[],
        returns=None,
    )
    mod_node = Module(body=[func_node])
    return ast_to_func(mod_node, func_name)


def make_init_stmt(item):
    """Make the AST for the initialization statement (`self._var = None`).
    """
    target = Attribute(
        value=Name(id="self", ctx=ast.Load()), attr=f"_{item.var}", ctx=ast.Store()
    )
    assign_stmt = ast.Assign(targets=[target], value=Name(id="None", ctx=ast.Load()))
    return assign_stmt


def populate_macro_items(cls):
    """Parse the annotations and construct the getter/setter functions.
    """
    items = collect_vars(cls)
    new_items = []
    for item in items:
        item_cpy = item
        comp = parse(item_cpy)
        lower, upper = extract_endpoints(comp)
        item_cpy.lower, item_cpy.upper = lower, upper
        item_cpy.init_stmt = make_init_stmt(item_cpy)
        item_cpy.getter = getter(item_cpy)
        item_cpy.setter = setter(item_cpy)
        new_items.append(item_cpy)
    items = new_items
    return items


def empty_init_ast():
    """Constructs an AST for `__init__` with no body.

    #SPC-asts.initast
    """
    self_arg = arg(arg="self", annotation=None)
    func_args = arguments(
        args=[self_arg],
        kwonlyargs=[],
        vararg=None,
        kwarg=None,
        defaults=[],
        kw_defaults=[],
    )
    func_node = FunctionDef(
        name="__init__", args=func_args, body=[], decorator_list=[], returns=None
    )
    return func_node


def make_init(items):
    """Construct the `__init__` function.

    partof: #SPC-asts.statements
    """
    init = empty_init_ast()
    for item in items:
        init.body.append(item.init_stmt)
    mod_node = Module(body=[init])
    return ast_to_func(mod_node, "__init__")


def bind_init(cls, items):
    """Add the `__init__` method to the class.

    partof: #SPC-asts.bind
    """
    init_func = make_init(items)
    setattr(cls, "__init__", init_func.__get__(cls))


def produce(cls):
    """Generate the new class definition.

    partof: #SPC-asts.property
    """
    items = populate_macro_items(cls)
    bind_init(cls, items)
    for item in items:
        setattr(cls, item.var, property(item.getter, item.setter))
    return cls
