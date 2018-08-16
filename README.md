# Abusing Type Annotations

Rust-like "macros" in Python via egregious abuse of type annotations.

## About

This project started out as an exploration into whether Rust-like macros could be brought to Python. Spoiler: They can be (but it's not pretty). Rust has more than one kind of macro, but "procedural" macros operate on the abstract syntax tree of your code (an abstract syntax tree is a data structure that represents your parsed code). This allows you to generate code or derive functionality provided by a library with very little effort on your part. It's pretty great.

The code in this repository is just a proof of concept, so you probably shouldn't use it for anything mission critical. If you want to read about what's going on here, how it works, etc, you can read the blog post:

- [Bringing macros to Python by abusing type annotations](https://tinkering.xyz/abusing-type-annotations/)

### Example 1 - Generating Instance Properties
I fully committed to the Rust way of doing things for this example, and worked on ASTs the whole way through. This example provides a decorator, `@inrange`, that generates properties based on the annotations of class variables.

The `@inrange` macro would take this class definition
```python
@inrange
class MyClass:
    var: "0 < var < 1"
```
and turn it into
```python
class MyClass:
    var: "0 < var < 1"

    def __init__(self):
        self._var = None

    @property
    def var(self):
        return self._var

    @var.setter
    def var(self, new_value):
        if (0 < new_value) and (new_value < 1):
            self._var = new_value
```

In this example the getter, setter, and `__init__` are all constructed as ASTs, then compiled to functions, then bound to the class. I do not recommend this.

### Example 2 - Notify on Write
The second example prints a notification to the terminal when writing to a variable that you've marked with a certain annotation. For example:
```python
@notify
class MyClass:
    def __init__(self, x):
        self.x: "this one" = x
        self.y = True
```
This would print a message to the terminal whenever you try to assign a new value to `foo.x` (where `foo` is an instance of `MyClass`).

This example is much less AST wrangling than the first example, but the AST is still used to determine which fields are marked with the `"this one"` annotation. To intercept writes to the the variables, the class's `__setattr__` method is overridden with one that will print messages before setting the new value.

## License

Licensed under either of

 * Apache License, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE) or http://www.apache.org/licenses/LICENSE-2.0)
 * MIT license ([LICENSE-MIT](LICENSE-MIT) or http://opensource.org/licenses/MIT)

at your option.

### Contribution

Unless you explicitly state otherwise, any contribution intentionally
submitted for inclusion in the work by you, as defined in the Apache-2.0
license, shall be dual licensed as above, without any additional terms or
conditions.
