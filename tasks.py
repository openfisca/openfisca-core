import os

import invoke


@invoke.task
def test(context, pattern):
    jobs = os.cpu_count() // 2
    args = f"PYTEST_ADDOPTS='-qx --workers {jobs}'"
    context.run(f"{args} openfisca test {pattern}")
