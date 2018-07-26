# REQ-notify
partof:
  - REQ-purpose
###

This project shall implement a decorator that prints a notification to the terminal when a new value is assigned to a designated class or instance attribute.

- The decorator shall allow only a single field to be designed per class.
- The designated field shall be marked by placing the string "this one" in the field's annotation.
- When the field is assigned to, a message shall be printed to the terminal indicating the current value and the value to be assigned.
