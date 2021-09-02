import os

import invoke


@invoke.task
def test(context, group, pattern):
    jobs = os.cpu_count() // 4
    args = f"PYTEST_ADDOPTS='-qx --workers {jobs} --splits {jobs * 2} --group {group}'"
    context.run(f"{args} openfisca test {pattern}")
