# REQ-closures
partof:
  - REQ-purpose
###

This example shows a simpler, more Pythonic way to accomplish the goals of [[REQ-ast]].

This example will provide a macro (class decorator) that generates instance properties from specially annotated class variables.

- The macro shall be called `inrange`.
- The macro shall accept class variable annotations of the form `"lower < class_var < upper"`, where `upper` and `lower` must be literal numeric values.
- The macro shall only accept closed ranges i.e. ranges with both `upper` and `lower` specified.
- The macro shall only accept the `<` operator, for simplicity.
- The macro shall generate a setter that only accepts values in the range specified by the annotation.
- The macro shall implement getters and setters with closures.
