from __future__ import annotations

from typing import Iterable
from typing_extensions import TypeGuard

from .typing import AbbrParams, AxesParams, ExplParams, ImplParams, Params


def is_abbr_spec(params: Params, items: Iterable[str]) -> TypeGuard[AbbrParams]:
    return any(key in items for key in params.keys()) or params == {}


def is_impl_spec(params: Params, items: Iterable[str]) -> TypeGuard[ImplParams]:
    return set(params).intersection(items)


def is_expl_spec(params: Params, items: Iterable[str]) -> TypeGuard[ExplParams]:
    return any(key in items for key in params.keys())


def is_axes_spec(params: ExplParams | Params) -> TypeGuard[AxesParams]:
    return params.get("axes", None) is not None
