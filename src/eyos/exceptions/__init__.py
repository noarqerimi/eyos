from eyos.exceptions import validations
from eyos.exceptions.base import ExceptionHandlers

exception_handlers = ExceptionHandlers()
exception_handlers.include_exception_handlers(validations.exception_handler)
