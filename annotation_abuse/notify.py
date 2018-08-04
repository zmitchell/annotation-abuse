"""#SPC-notify"""
import ast
from enum import Enum
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
NICE = r"""
    \
     \
        __
       /  \
       |  |
       @  @
       || |/
       || ||
       |\_/|
       \___/
"""
ANGRY = r"""
    \
     \
        __
       /  \
       \  /
       @  @
       || |/
       || ||
       |\_/|
       \___/
"""


class Response(Enum):
    YES = ["y", "Y", "yes", "Yes", "YES"]
    NO = ["n", "N", "no", "No", "NO"]
    INVALID = ""


def notify(cls):
    """Prints a message when assigning to variables annotated with 'this one'.

    partof: #SPC-notify.decorator
    """
    if type(cls) is not type:
        raise TypeError("'notify' may only be applied to classes")
    class_vars = detect_classvars(cls)
    inst_vars = find_instvars(cls)
    marked_vars = inst_vars + class_vars
    new_setattr = make_setattr(cls, marked_vars)
    setattr(cls, "__setattr__", new_setattr.__get__(cls))
    return cls


def detect_classvars(cls):
    """Extracts the names of marked class variables.

    partof: #SPC-notify.classvars
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

    partof: #SPC-notify-inst.modast
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


def find_init_ast(cls):
    """Returns the AST of the class's `__init__` method.

    partof: #SPC-notify-inst.initast
    """
    mod_ast = module_ast(cls)
    cache = build_func_cache(mod_ast)
    init_ast = cache[cls.__init__.__code__.co_firstlineno]
    return init_ast


def find_instvars(cls):
    """Returns a list of marked instance variables.

    partof: #SPC-notify-inst
    """
    if inherits_init(cls):
        return []
    init_node = find_init_ast(cls)
    annotated_assignments = recurse_init(init_node)
    marked_inst_vars = []
    for item in annotated_assignments:
        ann_is_str = type(item.annotation) is ast.Str
        try:
            has_marker = item.annotation.s == MARKER
        except AttributeError:
            continue
        target_is_attr = type(item.target) is ast.Attribute
        try:
            target_is_self = item.target.value.id == "self"
        except AttributeError:
            continue
        if ann_is_str and has_marker and target_is_attr and target_is_self:
            marked_inst_vars.append(item.target.attr)
    return marked_inst_vars


def recurse_init(node):
    """Recurse the AST of `__init__` looking for `ast.AnnAssign` nodes."""
    ann_assigns = []
    if type(node) is ast.AnnAssign:
        ann_assigns.append(node)
        return ann_assigns
    if type(node) in BLOCK_TYPES:
        for child in node.body:
            nested_assigns = recurse_init(child)
            ann_assigns.extend(nested_assigns)
    return ann_assigns


def make_setattr(cls, var_names):
    """Make a `__setattr__` that detects writes to certain attributes.

    partof: #SPC-notify-intercept
    """

    def new_setattr(self, attr_name, new_value):
        if attr_name not in var_names:
            setattr(self, attr_name, new_value)
            return
        # The instance variable will be set for the first time during __init__ but we
        # don't want to prompt the user on instantiation.
        if attr_name not in self.__dict__.keys():
            setattr(self, attr_name, new_value)
            return
        current_value = self.__dict__[attr_name]
        attr = cls.__name__ + "." + attr_name
        show_message(attr, current_value, new_value)
        user_resp = prompt_user()
        if user_resp == Response.YES:
            no_problem_message()
            setattr(self, attr_name, new_value)
        elif user_resp == Response.NO:
            angry_message()

    return new_setattr


def show_message(name, old_value, new_value):
    """Inform the user that a new value is about to be set.

    partof: #SPC-notify-intercept.msg
    """
    update_msg = f"It looks like you're trying to update {name}"
    from_msg = f'from "{old_value}"'
    to_msg = f'to "{new_value}".'
    use_combined = False
    if len(from_msg + to_msg) < 60:
        combined_msg = from_msg + " " + to_msg
        use_combined = True
    help_msg = "Would you like some help with that?"
    if use_combined:
        lines = [update_msg, combined_msg, help_msg]
    else:
        lines = [update_msg, from_msg, to_msg, help_msg]
    text = speech_bubble(lines)
    for line in text:
        print(line)
    print(NICE)


def angry_message():
    lines = ["FINE"]
    text = speech_bubble(lines)
    for line in text:
        print(line)
    print(ANGRY)


def no_problem_message():
    lines = ["No problem!"]
    text = speech_bubble(lines)
    for line in text:
        print(line)
    print(NICE)


def speech_bubble(msg_lines):
    """Wraps the lines of a message in an ASCII speech bubble."""
    msg_width = max([len(x) for x in msg_lines])
    lines = []
    lines.append("   " + (msg_width + 2) * "_" + " ")
    lines.append("  /" + (msg_width + 2) * " " + "\\")
    for line in msg_lines:
        lines.append("  | " + line.center(msg_width) + " |")
    lines.append("  \\" + (msg_width + 2) * "_" + "/")
    return lines


def prompt_user():
    """Get the user's approval to set the value.

    partof: #SPC-notify-intercept.input
    """
    prompt = "Let Clippy update the value? (y/n): "
    keep_going = True
    while keep_going:
        text = input(prompt)
        resp = interpret_resp(text)
        if resp == Response.INVALID:
            print()
            print("...please don't make him angry...seriously...")
            print("Only (y|Y|yes|Yes) and (n|N|no|No) are valid responses")
            print()
        else:
            keep_going = False
    return resp


def interpret_resp(text):
    """Interpret the user's response."""
    resp = text.strip()
    if resp in Response.YES.value:
        return Response.YES
    elif resp in Response.NO.value:
        return Response.NO
    else:
        return Response.INVALID
