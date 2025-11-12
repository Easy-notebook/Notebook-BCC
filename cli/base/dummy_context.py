"""
Dummy context manager for when rich is not available.
"""


class DummyContext:
    """Dummy context manager for when rich is not available."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
