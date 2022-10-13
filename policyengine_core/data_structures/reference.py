

class Reference:
    label: str
    """The display text to use for the reference."""

    href: str
    """The URL to link to."""

    type: str = "general"
    """The type of reference. Custom country-specific reference types should override this class."""

    def __init__(self, label: str, href: str):
        self.label = label
        self.href = href