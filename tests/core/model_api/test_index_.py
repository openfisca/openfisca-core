import numpy as np


def test_index_():
    from policyengine_core.model_api import index_

    assert (
        index_(
            into=np.array([1, 2, 3, 4, 5]),
            indices=np.array([2, 2, 2, 1, 1]),
            where=np.array([True, False, True, False, True]),
            fill=7,
        )
        == np.array([3, 7, 3, 7, 2])
    ).all(), "index_ function didn't output as expected."
