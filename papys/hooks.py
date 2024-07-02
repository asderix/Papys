import traceback
from typing import Tuple, Any
from papys.request_response import Request, Response, COOKIE_SAME_SITE_STRICT


class PHook:
    """
    Base class for a hook. This class has to be implemented by a subclass..
    """

    def __init__(self):
        self._sub_hook = None

    @property
    def sub_hook(self):
        return self._sub_hook

    def process_hook(
        self, req: Request, resp: Response
    ) -> Tuple[bool, int, Request, Response]:
        raise NotImplementedError("This method must be overridden by a subclass!")

    # >>
    def __rshift__(self, other):
        self._sub_hook = other
        return self


class FunctionHook(PHook):
    """
    PHook implementation for a function execution.

    Args:
        hf (function): The function which should be executed. func(Request, Response) -> Tuple[bool, int, Request, Response].
        status_codes (dict): {'error': 500} is default. You can provide an other code to return in case of an exception.
    """

    def __init__(self, hf=None, status_codes: dict = {"error": 500}):
        self.hook_function = hf
        self._status_codes = status_codes
        super().__init__()

    def process_hook(
        self, req: Request, resp: Response
    ) -> Tuple[bool, int, Request, Response]:
        if self.hook_function is not None:
            try:
                result = self.hook_function(req, resp)
                return result
            except Exception as err:
                req.logger.log_error(
                    "FunctionHook function could not processed.",
                    traceback.format_exc(),
                    130,
                    req,
                )
                return False, self._status_codes["error"], req, resp
        return False, self._status_codes["error"], req, resp


class ParaMapHook(PHook):
    """
    PHook implementation for a parameter variable mapping.
    This hook inserts new entries to Request.path_variables based on the mapping dict.
    Example of a mapping dict:
    {
        "variable_new": "{doc_id}",
        "symbol_new": "simbol",
    }
    Value in brackets refer to an exiting path variable in Request.path_variables.

    Args:
        map (dict): The mapping logic.
        status_codes (dict): {'success': 200, 'error': 500} is default. You can provide an other code to return in case of success or an exception.
    """

    def __init__(
        self,
        map: dict | None = None,
        status_codes: dict = {"success": 200, "error": 500},
    ):
        self.map = map
        self._status_codes = status_codes
        super().__init__()

    def process_hook(
        self, req: Request, resp: Response
    ) -> Tuple[bool, int, Request, Response]:
        if self.map is not None:
            try:
                for key, value in self.map.items():
                    if value.startswith("{") and value.endswith("}"):
                        variable_name = value[1:-1]
                        req.path_variables[key] = req.path_variables.get(
                            variable_name, "not_found"
                        )
                    else:
                        req.path_variables[key] = value

                result = True, self._status_codes["success"], req, resp
                return result
            except Exception as err:
                req.logger.log_error(
                    "ParaMapHook could not processed.", traceback.format_exc(), 131, req
                )
                resp.is_error = True
                resp.error = err
                return False, self._status_codes["error"], req, resp
        return False, self._status_codes["error"], req, resp
