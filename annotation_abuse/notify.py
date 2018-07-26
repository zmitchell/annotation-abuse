MARKER = "this one"


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
