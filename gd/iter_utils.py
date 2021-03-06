from typing import Any, Callable, Iterable, Tuple, TypeVar, Union, cast, overload

__all__ = ("extract_iterable_from_tuple", "is_iterable")

T = TypeVar("T")


def is_iterable(maybe_iterable: Union[Iterable[T], T], use_iter: bool = True) -> bool:
    if use_iter:
        try:
            iter(maybe_iterable)  # type: ignore
            return True

        except TypeError:  # "T" object is not iterable
            return False

    return isinstance(maybe_iterable, Iterable)


@overload  # noqa
def extract_iterable_from_tuple(  # noqa
    tuple_to_extract: Tuple[Iterable[T]], check: Callable[[Any], bool]
) -> Iterable[T]:
    ...


@overload  # noqa
def extract_iterable_from_tuple(  # noqa
    tuple_to_extract: Tuple[T, ...], check: Callable[[Any], bool]
) -> Iterable[T]:
    ...


def extract_iterable_from_tuple(  # noqa
    tuple_to_extract: Union[Tuple[Iterable[T]], Tuple[T, ...]],
    check: Callable[[Any], bool] = is_iterable,
) -> Iterable[T]:
    if len(tuple_to_extract) == 1:
        maybe_return = tuple_to_extract[0]

        if check(maybe_return):
            return cast(Iterable[T], maybe_return)

    return cast(Iterable[T], tuple_to_extract)
