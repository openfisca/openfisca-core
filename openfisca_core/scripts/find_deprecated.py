import ast
import pkg_resources
import pathlib
import textwrap
import subprocess

CURRENT_VERSION = pkg_resources.get_distribution("openfisca_core").version


class FindDeprecated(ast.NodeVisitor):

    def __init__(self):
        result = subprocess.run(
            ["git", "ls-files", "*.py"],
            stdout = subprocess.PIPE,
            )

        self.files = result.stdout.decode("utf-8").split()
        self.nodes = [self.node(file) for file in self.files]

    def __call__(self):
        for count, node in enumerate(self.nodes):
            self.count = count
            self.visit(node)

    def visit_FunctionDef(self, node):
        for decorator in node.decorator_list:
            if "deprecated" in ast.dump(decorator):
                file = self.files[self.count]
                path = pathlib.Path(file).resolve()
                module = f"{path.parts[-2]}.{path.stem}"
                lineno = node.lineno + 1
                since, expires = decorator.keywords

                # breakpoint()

                message = [
                    f"[{module}.{node.name}:{lineno}]",
                    f"Deprecated since: {since.value.s}.",
                    f"Expiration status: {expires.value.s}",
                    f"(current: {CURRENT_VERSION}).",
                    ]

                print(" ".join(message))

    def node(self, file):
        try:
            with open(file, "rb") as f:
                source = textwrap.dedent(f.read().decode("utf-8"))
                node = ast.parse(source, file, "exec")
                return node

        except IsADirectoryError:
            pass


find = FindDeprecated()
find()
