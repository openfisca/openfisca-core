import numpy
from numpy.typing import NDArray

def evaluate(
    __ex: str,
    /,
    *__args: object,
    **__kwargs: object,
) -> NDArray[numpy.bool_] | NDArray[numpy.int32] | NDArray[numpy.float32]: ...
