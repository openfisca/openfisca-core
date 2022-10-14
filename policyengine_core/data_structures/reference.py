class Reference:
    """A reference to a piece of legislation or other document."""

    label: str
    """The display text to use for the reference."""

    href: str
    """The URL to link to."""

    type: str = "general"
    """The type of reference."""
