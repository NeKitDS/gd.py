from functools import wraps
from operator import attrgetter

from gd.async_utils import get_not_running_loop, maybe_coroutine
from gd.code_utils import time_execution_and_print
from gd.errors import LoginRequired
from gd.typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional, Type, TypeVar, Union

if TYPE_CHECKING:
    from gd.abstract_entity import AbstractEntity  # noqa
    from gd.client import Client  # noqa

__all__ = (
    "benchmark",
    "cache_by",
    "cached_property",
    "classproperty",
    "login_check",
    "login_check_object",
    "patch",
    "run_once",
    "sync",
    "synchronize",
)

T = TypeVar("T")


class CachedProperty:
    def __init__(self, method: Optional[Callable[..., Any]] = None) -> None:
        self.method = method

        self.__doc__ = method.__doc__

    @property
    def __name__(self) -> str:
        if self.method is None:
            raise AttributeError("Can not read name of the property.")

        try:
            return self.method.__name__

        except AttributeError:
            return f"unknown_{id(self):x}"

    def __get__(self, instance: Optional[Any], owner: Optional[Type[Any]] = None) -> Any:
        if instance is None:
            return self

        if self.method is None:
            raise AttributeError("Can not read cached property.")

        value = self.method(instance)

        setattr(instance, self.__name__, value)

        return value

    def getter(self, method: Callable[..., Any]) -> "CachedProperty":
        self.method = method

        self.__doc__ = method.__doc__

        return self


def cached_property(method: Optional[Callable[..., Any]] = None) -> CachedProperty:
    """Decorator that converts a method with a single instance argument into a property
    that caches itself after being called.

    When cached property is accessed, it executes underlying method,
    replacing itself in the instance with the call result.

    Example
    -------
    >>> class Class:
    ...     @cached_property
    ...     def value(self) -> int:
    ...         print("called")
    ...         return 42
    ...
    >>> instance = Class()
    >>> instance.value
    called
    42
    >>> instance.value
    42
    """
    return CachedProperty(method)


class ClassProperty:
    def __init__(self, method: Optional[Callable[..., Any]] = None) -> None:
        self.get = method

        self.__doc__ = method.__doc__

    @property
    def __name__(self) -> str:
        if self.get is None:
            raise AttributeError("Can not read name of the property.")

        try:
            return self.get.__name__

        except AttributeError:
            return f"unknown_{id(self):x}"

    def __get__(self, instance: Optional[Any], owner: Optional[Type[Any]] = None) -> Any:
        if owner is None:
            if instance is None:
                raise RuntimeError("Both instance and owner are not present.")

            cls = type(instance)

        else:
            cls = owner

        if self.get is None:
            raise AttributeError("Can not read class property.")

        return self.get(cls)

    def getter(self, method: Callable[..., Any]) -> "ClassProperty":
        self.get = method

        self.__doc__ = method.__doc__

        return self


def classproperty(method: Optional[Callable[..., Any]] = None) -> ClassProperty:
    """Decorator that converts a method with a single class argument into a property
    that can be accessed directly from the class.

    Example
    -------
    >>> class Class:
    ...     @classproperty
    ...     def value(cls) -> int:
    ...         return 42
    ...
    >>> Class.value
    42
    >>> instance = Class()
    >>> instance.value
    42
    """
    return ClassProperty(method)


def benchmark(function: Callable[..., T]) -> Callable[..., T]:
    """Benchmark time spent to call ``function``.
    :func:`~gd.utils.time_execution_and_print` is used internally.
    """

    @wraps(function)
    def inner(*args, **kwargs) -> T:
        return time_execution_and_print(function, *args, **kwargs)

    return inner


def cache_by(*names: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Cache ``function`` result by object's attributes given by ``names``."""

    def decorator(function: Callable[..., T]) -> Callable[..., T]:
        get_attrs = tuple(attrgetter(name) for name in names)

        @wraps(function)
        def wrapper(self, *args, **kwargs) -> T:
            actual = tuple(get_attr(self) for get_attr in get_attrs)

            try:
                cached = function._cached  # type: ignore

            except AttributeError:
                result = function(self, *args, **kwargs)

                function._cached = result  # type: ignore

                return result

            try:
                cached_by = function._cached_by  # type: ignore

            except AttributeError:
                function._cached_by = actual  # type: ignore

            else:
                if actual == cached_by:
                    return cached

            function._cached_by = actual  # type: ignore

            result = function(self, *args, **kwargs)

            function._cached = result  # type: ignore

            return result

        return wrapper

    return decorator


def sync(function: Callable[..., Union[Awaitable[T], T]]) -> Callable[..., T]:
    """Wrap ``function`` to be called synchronously."""

    @wraps(function)
    def syncer(*args, **kwargs) -> T:
        return get_not_running_loop().run_until_complete(maybe_coroutine(function, *args, **kwargs))

    return syncer


def synchronize(cls: Type[T]) -> Type[T]:
    """Implement ``sync_<name>`` functions for class ``cls`` to synchronously call methods."""
    try:
        old_get_attribute = cls.__getattr__  # type: ignore

    except AttributeError:

        def old_get_attribute(instance: T, name: str) -> None:
            raise AttributeError(f"{type(instance).__name__!r} has no attribute {name!r}")

    lookup = "sync_"

    def get_attribute(instance: T, name: str) -> Any:
        if name.startswith(lookup):

            name = name[len(lookup) :]  # skip lookup part in name

            return sync(getattr(instance, name))

        else:
            return old_get_attribute(instance, name)

    cls.__getattr__ = get_attribute  # type: ignore

    return cls


def login_check(function: Callable[..., T]) -> Callable[..., T]:
    """Wrap ``function`` for :class:`~gd.AbstractEntity` or :class:`~gd.Client`
    to check if the client is logged in.
    """

    @wraps(function)
    def wrapper(client_or_entity: Union["AbstractEntity", "Client"], *args, **kwargs) -> T:
        login_check_object(client_or_entity)

        return function(client_or_entity, *args, **kwargs)

    return wrapper


def login_check_object(client_or_entity: Union["AbstractEntity", "Client"]) -> None:
    """Check whether :class:`~gd.AbstractEntity` or :class:`~gd.Client` have logged in client."""
    client: "Client" = getattr(client_or_entity, "client", client_or_entity)

    if not client.is_logged():
        raise LoginRequired("Client is not logged in.")


def run_once(function: Callable[..., T]) -> Callable[..., T]:
    """Execute ``function`` once, cache the result and return it on other calls."""

    @wraps(function)
    def runner(*args, **kwargs) -> T:
        if not hasattr(function, "run_once_result"):
            function.run_once_result = function(*args, **kwargs)  # type: ignore

        return function.run_once_result  # type: ignore

    return runner


def patch(
    some_object: Any, name: Optional[str] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Patch ``name`` method or function of ``some_object`` with ``function``."""

    def decorator(function: Callable[..., T]) -> Callable[..., T]:
        nonlocal name

        if name is None:
            name = function.__name__

        setattr(some_object, name, function)

        return function

    return decorator
