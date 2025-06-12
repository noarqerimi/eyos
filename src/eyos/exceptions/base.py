from typing import Any, Awaitable, Callable, Type, TypeVar, Union

from fastapi import FastAPI, Request, Response

E = TypeVar("E", bound=Exception)
ExceptionHandlerType = Callable[[Request, E], Union[Response, Awaitable[Response]]]


class ExceptionHandlers:
    def __init__(self) -> None:
        self.handlers: dict[Type[Exception], ExceptionHandlerType[Any]] = {}

    def add_exception_handler(
        self, *exceptions: Type[E]
    ) -> Callable[[ExceptionHandlerType[E]], ExceptionHandlerType[E]]:
        def decorator(handler: ExceptionHandlerType[E]) -> ExceptionHandlerType[E]:
            for exception in exceptions:
                self.handlers[exception] = handler
            return handler

        return decorator

    def include_exception_handlers(self, exception_handler: "ExceptionHandlers") -> None:
        self.handlers.update(exception_handler.handlers)

    def __call__(self, app: FastAPI) -> None:
        for exception, handler in self.handlers.items():
            app.add_exception_handler(exception, handler)
