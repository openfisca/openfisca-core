"""Algebraic data types for OpenFisca.

An algebraic data type is a structured type that’s formed by composing other
types. [...] Product types allow you to have more than one value in a single
structure, at the same time. [...] Sum types are types where your value must
be one of a fixed set of options.

.. _See:
    https://jrsinclair.com/articles/2019/algebraic-data-types-what-i-wish-someone-had-explained-about-functional-programming/

"""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar, cast, final
from typing_extensions import Never

import dataclasses

#: Type variable representing an error.
E = TypeVar("E")

#: Type variable representing a value.
A = TypeVar("A")


@dataclasses.dataclass(frozen=True)
class Either(Generic[E, A]):
    """The Either monad.

    The Either monad specifies the Either data type as well as several
    functions that operate on top of it. The Either data type represents the
    result of a computation that may fail.

    """

    #: The value or state passed on.
    _value: E | A

    @property
    @final
    def is_failure(self) -> bool:
        """bool: Whether this instance represents a failure."""
        return isinstance(self, Failure)

    @property
    @final
    def is_success(self) -> bool:
        """bool: Whether this instance represents a success."""
        return isinstance(self, Success)

    @final
    def unwrap(self) -> E | A:
        """Return the value of this instance.

        Examples:
            >>> Either.fail("error").unwrap()
            'error'

            >>> Either.succeed(1).unwrap()
            1

        Returns:
            E | A: The value of this instance.

        """

        return self._value

    @final
    def then(
        self, f: Callable[[A], Failure[E] | Success[A]]
    ) -> Failure[E] | Success[A]:
        """Apply a flatMap to input stream.

        Examples:
            >>> Either.fail("error").then(lambda x: Either.succeed(x)).unwrap()
            'error'

            >>> Either.succeed(1).then(lambda x: Either.succeed(x + 1)).unwrap()
            2

        Args:
            f: A function that takes a value and returns a new Either instance.

        Returns:
            _Failure[E] | _Success[A]: The result of applying f.

        """

        if self.is_success:
            return f(cast(A, self.unwrap()))
        return Either.fail(cast(E, self.unwrap()))

    @staticmethod
    @final
    def fail(value: E) -> Failure[E]:
        """_Failure[E]: Create a failing result."""
        return Failure(value)

    @staticmethod
    @final
    def succeed(value: A) -> Success[A]:
        """_Success[A]: Create a successful result."""
        return Success(value)


@final
class Failure(Either[E, Never]):
    """A failing result in an Either ADT."""


@final
class Success(Either[Never, A]):
    """A successful result in an Either ADT."""
