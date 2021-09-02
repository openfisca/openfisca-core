import os

import invoke


@invoke.task
def test(context, pattern):
    workers = os.cpu_count() // 2
    context.run(f"pytest -qx --workers {workers} {pattern}")
