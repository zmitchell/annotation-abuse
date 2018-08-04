# REQ-asts
partof: REQ-purpose
###

This project started as an exploration into whether it is possible to create Rust-style macros in Python. Procedural macros in Rust are functions that, when applied to a struct, function, etc, are passed the abstract syntax tree (AST) of the respective item. The function operates on the AST, performing some computations i.e. code generation, and returns the AST that should replace the original AST.

This example will provide a macro (class decorator) that generates instance properties from specially annotated class variables.

- The macro shall be called `inrange`.
- The macro shall accept class variable annotations of the form `"lower < class_var < upper"`, where `upper` and `lower` must be literal numeric values.
- The macro shall only accept closed ranges i.e. ranges with both `upper` and `lower` specified.
- The macro shall only accept the `<` operator, for simplicity.
- An exception shall be raised if the annotation does not conform to the specified format.
- The macro shall generate a setter that only accepts values in the range specified by the annotation.
- The macro shall operate on the AST of the class being decorated.
- The macro shall generate functions/methods via constructing ASTs.