# SPC-notify
This project shall implement a decorator, `notify`, that shall only be applied to class definitions. Both class variables ([[SPC-notify.detect-classvars]]) and instance variables ([[SPC-notify-inst]]) shall be searched for the marker annotation. The marked variable will be replaced with a descriptor whose `__set__` method prints a message to the terminal.

## [[.decorator]]
The decorator shall only be applied to classes.

## [[.detect-classvars]]: Detect marked class variables
Marked class variables shall be detected by reading `MyClass.__annotations__` if it exists. This attribute will not exist if there are no annotated class variables).

# SPC-notify-inst
Marked instance variables shall be detected by searching the AST of the class's `__init__` method (if it exists). The marked variables will be detected using the following procedure:
- Obtain the filename of the module that class resides in.
- Read the module into a string.
- Parse the string into an AST.
- Recursively search the AST until you find the `__init__` method.
- Recursively search the nodes in the `body` of the `__init__` node, looking for nodes of type `ast.AnnAssign`.
- Record the attribute name if the attribute is being assigned to is of the form `self.attr`.

Searching for marked instance variables shall be skipped if the class inherits `__init__` from a superclass.

## [[.inherits]]: Determine if `__init__` is inherited
The `__qualname__` of `MyClass.__init__` will end with `MyClass.__init__` if it is defined as part of the class.

## [[.mod-ast]]: Construct an AST for the module
The filename of the module can be found in `MyClass.__init__.__code__.co_filename`. The source code should be read into a string and parsed using `ast.parse()`.

## [[.cache]]: Locate all functions/methods in the module
A cache (dictionary) will be created to hold all of the functions in the module. The dictionary keys will be line numbers, and the values will be the AST nodes of the functions. The line numbers of functions can be obtained from `func.__code__.co_firstlineno`.

The module should be recursively searched to locate nested functions and class definitions. The search can be carried out by iterating over the nodes in the `body` field of the appropriate AST nodes.

## [[.find-init]]: Obtain the AST of the `__init__` method
The AST will be retrieved from the cache using the line number from `MyClass.__init__.__code__.co_firstlineno`.

## [[.find-ann]]: Find annotated instance attributes
Assignments to annotated variables appear in `ast.AnnAssign` nodes. The marked instance variables will appear in `ast.AnnAssign` nodes where the `target` field is of the form `self.var`.

# SPC-notify-desc
foo
