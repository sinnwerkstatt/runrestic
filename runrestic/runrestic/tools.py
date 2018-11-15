class ReturnCodes:
    rcs = []

    def __init__(self, exit_on_error=True):
        self.exit_on_error = exit_on_error

    def __repr__(self):
        return 'ReturnCodes: {}'.format(self.rcs)

    def __str__(self):
        return str(self.rcs)

    def __add__(self, other: list):
        if isinstance(other, int):
            other = [other]
        if self.exit_on_error and any(other):
            raise RuntimeError(
                "Caught an error - exiting. If you want runrestic to continue despite errors, set `exit_on_error=false` in your config.")
        self.rcs += other
        return self

    def __iter__(self):
        return self.rcs.__iter__()
