import invoke


@invoke.task
def test(context, pattern):
    context.run("pytest -qx --workers auto")
