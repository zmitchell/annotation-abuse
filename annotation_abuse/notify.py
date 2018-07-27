import ast
import sys

MARKER = "this one"
BLOCK_TYPES = [
    ast.If,
    ast.For,
    ast.While,
    ast.Try,
    ast.ExceptHandler,
    ast.With,
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.AsyncFor,
    ast.AsyncWith,
    ast.Module,
]


def notify(cls):
    """Prints a message when assigning to variables annotated with 'this one'.

    partof: #SPC-notify.decorator
    """
    if type(cls) is not type:
        raise TypeError("'notify' may only be applied to classes")
    return cls


def detect_classvars(cls):
    """Extracts the names of marked class variables.

    partof: #SPC-notify.detect-classvars
    """
    annotations = getattr(cls, "__annotations__", None)
    if annotations is None:
        return []
    classvars = []
    for field, annotation in annotations.items():
        if annotation == MARKER:
            classvars.append(field)
    return classvars


def inherits_init(cls):
    """Returns `True` if the class inherits its `__init__` method.

    partof: #SPC-notify-inst.inherits
    """
    classname = cls.__name__
    suffix = f"{classname}.__init__"
    return not cls.__init__.__qualname__.endswith(suffix)


def module_ast(cls):
    """Constructs the AST for the module that the class resides in.

    partof: #SPC-notify-inst.mod-ast
    """
    filename = cls.__init__.__code__.co_filename
    try:
        with open(filename, "r") as mod_file:
            mod_contents = mod_file.read()
    except IOError:
        sys.exit(f"Could not open file {filename}")
    mod_contents.replace("\r\n", "\n").replace("\r", "\n")
    if not mod_contents.endswith("\n"):
        mod_contents += "\n"
    mod_node = ast.parse(mod_contents)
    return mod_node


def build_func_cache(parent_node):
    """Recursively builds a cache of all functions in the module.

    The cache returned is a dictionary whose keys are line numbers, and whose values
    are ASTs belonging to the functions in the module.

    partof: #SPC-notify-inst.cache
    """
    func_nodes = dict()
    if type(parent_node) is ast.FunctionDef:
        func_nodes[parent_node.lineno] = parent_node
    if type(parent_node) in BLOCK_TYPES:
        for child in parent_node.body:
            nested_nodes = build_func_cache(child)
            func_nodes.update(nested_nodes)
    return func_nodes
