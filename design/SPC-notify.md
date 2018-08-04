# SPC-notify
This project shall implement a decorator, `notify`, that shall only be applied to class definitions. Both class variables ([[SPC-notify.detect-classvars]]) and instance variables ([[SPC-notify-inst]]) shall be searched for the marker annotation. The marked variable will be replaced with a descriptor whose `__set__` method prints a message to the terminal.

## [[.decorator]]
The decorator shall only be applied to classes.

## [[.classvars]]: Detect marked class variables
Marked class variables shall be detected by reading `MyClass.__annotations__` if it exists. This attribute will not exist if there are no annotated class variables).

### Unit Tests
Valid inputs:
- [[.tst-marked_classvars]]: Test that the names of marked class variables are extracted.
Invalid inputs:
- [[.tst-arb_ann]]: Test that arbitrary string annotations are ignored.


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

### Unit Tests
Valid inputs:
- [[.tst-impl_init]]: Test that a class-defined `__init__` is correctly identified.
- [[.tst-inherits_init]]: Test that an inherited `__init__` is correctly identified.

## [[.modast]]: Construct an AST for the module
The filename of the module can be found in `MyClass.__init__.__code__.co_filename`. The source code should be read into a string and parsed using `ast.parse()`.

## [[.cache]]: Locate all functions/methods in the module
A cache (dictionary) will be created to hold all of the functions in the module. The dictionary keys will be line numbers, and the values will be the AST nodes of the functions. The line numbers of functions can be obtained from `func.__code__.co_firstlineno`.

The module should be recursively searched to locate nested functions and class definitions. The search can be carried out by iterating over the nodes in the `body` field of the appropriate AST nodes.

### Unit Tests
Valid inputs:
- [[.tst-detects_tests]]: Test that the cache locates all of the test functions in `test_notify.py`

## [[.initast]]: Obtain the AST of the `__init__` method
The AST will be retrieved from the cache using the line number from `MyClass.__init__.__code__.co_firstlineno`.

## [[.find]]: Find annotated instance attributes
Assignments to annotated variables appear in `ast.AnnAssign` nodes. The marked instance variables will appear in `ast.AnnAssign` nodes where the `target` field is of the form `self.var`.

### Unit Tests
Valid inputs:
- [[.tst-find_ann]]: Test that all marked instance variables are found in a class.


# SPC-notify-intercept
The decorator shall intercept writes to the marked variables by overriding the class's `__setattr__` method.

The replacement `__setattr__` should follow this procedure:
- Detect whether the method is trying to set a marked variable.
- If not, call the base class's `__setattr__` immediately and return.
- Generate a message to print to the terminal.
- Print the message.
- Collect the user input.
- Decide whether to set the new value based on user input.
- Set the new value if necessary.

The replacement `__setattr__` should be configured as a closure.

### Unit Tests
- [[.tst-intercepts_inst]]: Test that the new `__setattr__` intercepts writes to marked instance variables.
- [[.tst-intercepts_class]]: Test that the new `__setattr__` intercepts writes to marked class variables.
- [[.tst-unmarked_inst]]: Test that writes to unmarked instance variables behave as expected.
- [[.tst-unmarked_class]]: Test that writes to unmarked class variables behave as expected.

## [[.msg]]
A message should be shown to the user indicating that a new value is about to be set. The message should fit within a width of 80 characters modulo weird unicode things.

## [[.input]]
A prompt should be shown to the user saying something along the lines of:
```
Accept new value? (Y/n)
```
The prompt shall accept "Yes", "yes", "Y", or "y" as affirmative responses, and "No", "no", "N", or "n" as negative responses.

When a response is given that does not fit the set of allowed answers, a message should be printed indicating that the response was not understood, then the original prompt should be shown again.

### Unit Tests
Valid inputs:
- [[.tst-prompt_yes]]: Test that an affirmative input produces a "yes" response.
- [[.tst-prompt_no]]: Test that a negative input produces a "no" response.
Invalid inputs:
- [[.tst-prompt_invalid]]: Test that arbitrary text produces an "invalid" response.