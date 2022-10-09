import textwrap


class Role:
    """
    The type of the relation between an entity instance and a group entity instance.
    """

    def __init__(self, description, entity):
        self.entity = entity
        self.key = description["key"]
        self.label = description.get("label")
        self.plural = description.get("plural")
        self.doc = textwrap.dedent(description.get("doc", ""))
        self.max = description.get("max")
        self.subroles = None

    def __repr__(self) -> str:
        return "Role({})".format(self.key)
