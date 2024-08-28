import traceback
from functools import wraps
from enum import Enum, auto
from papys.request_response import Request, Response


class PapysActionException(Exception):
    def __init__(self, message: str, error_code: int = 500):
        super().__init__(message)
        self._message = message
        self._error_code = error_code

    def __str__(self):
        return f"[Error {self._error_code}]: {self._message}"

    def get_error_code(self):
        return self._error_code

    def get_message(self):
        return self._message


class ActionParameter(Enum):
    REQUEST = auto()
    RESPONSE = auto()
    REQUEST_BODY_JSON = auto()
    REQUEST_BODY_RAW = auto()
    REQUEST_BODY_STREAM = auto()
    REQUEST_BODY_STRING = auto()
    USER_INFO = auto()
    LOGGER = auto()


def _get_path_process_or_query_parameter(req: Request, name: str):
    if (pv := req.path_variables.get(name, None)) is not None:
        return pv
    if (pd := req.process_data.get(name, None)) is not None:
        return pd
    return req.query_string_dict.get(name, None)


def papys_action(
    param: dict = {},
    succ_code: int = 200,
    error_code: int = 500,
    return_mimetype: str | None = None,
):
    def decorator(func):
        @wraps(func)
        def wrapper(req: Request, resp: Response):
            try:
                param_values = {}

                for k, v in param.items():
                    match v:
                        case ActionParameter.REQUEST:
                            param_values[k] = req
                        case ActionParameter.RESPONSE:
                            param_values[k] = resp
                        case ActionParameter.REQUEST_BODY_JSON:
                            param_values[k] = req.body_json
                        case ActionParameter.REQUEST_BODY_RAW:
                            param_values[k] = req.body_raw
                        case ActionParameter.REQUEST_BODY_STREAM:
                            param_values[k] = req.body_stream
                        case ActionParameter.REQUEST_BODY_STRING:
                            param_values[k] = req.body_str
                        case ActionParameter.USER_INFO:
                            param_values[k] = req.user_info
                        case ActionParameter.LOGGER:
                            param_values[k] = req.logger
                        case _:
                            param_values[k] = _get_path_process_or_query_parameter(
                                req, v
                            )
                            pass

                result = func(**param_values)

                if isinstance(result, str):
                    resp.json = result

                if isinstance(result, dict):
                    resp.to_convert = result

                if isinstance(result, bytearray):
                    resp.custom_bytearray = result

                if return_mimetype is not None:
                    resp.content_type = return_mimetype

                return succ_code, req, resp

            except PapysActionException as papysErr:
                req.logger.log_error(
                    f"Error with papys_action. Function: ${func.__name__}. PapysActionException: ${papysErr.get_message()}",
                    traceback.format_exc(),
                    1100,
                    req,
                )
                resp.is_error = True
                resp.error = papysErr
                return papysErr.get_error_code(), req, resp

            except Exception as err:
                req.logger.log_error(
                    f"Error with papys_action. Function: ${func.__name__}",
                    traceback.format_exc(),
                    1101,
                    req,
                )
                resp.is_error = True
                resp.error = err
                return error_code, req, resp

        return wrapper

    return decorator

