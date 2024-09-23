from numpy.typing import NDArray as Array
from typing import NoReturn
from typing_extensions import TypeAlias

import numpy

ArrayBool: TypeAlias = numpy.bool_
ArrayInt: TypeAlias = numpy.int32
ArrayFloat: TypeAlias = numpy.float32

def evaluate(
    __ex: str, *__args: object, **__kwargs: object
) -> NoReturn | Array[ArrayBool | ArrayInt | ArrayFloat]: ...
