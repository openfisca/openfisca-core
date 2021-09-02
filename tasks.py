import invoke


@invoke.task
def test(context, pattern):
    context.run(f"pytest -qx --workers auto {pattern}")
