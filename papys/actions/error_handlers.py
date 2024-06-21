import json
import traceback
from typing import Tuple
from papys.actions.core import PAction
from papys.request_response import Request, Response


class ErrorAction(PAction):
    """
    Class providing a basic handling of errors in the DAG.
    The implementation checks whether Request.is_error is True.
    If so, it creates a response body from Response.error_message.
    If not, a response body is created with the message that the action was called but there is no error.
    So make sure that if this error handler is called in the DAG via a status code,
    that a previous handler has also set Response.is_error to True.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
        status_codes (dict): You can customize the returned status in case of success and error. Default: { 'success': 200, 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        status_codes={"success": 200, "error": 500},
    ):
        self._status_codes = status_codes
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            if resp.is_error:
                resp.json = json.dumps(
                    {"errorCode": resp.status_code, "errorMessage": str(resp.error)}
                )
                resp.status_code = self._status_codes["error"]
                return self._status_codes["error"], req, resp
            else:
                resp.json = json.dumps(
                    {
                        "errorCode": -1,
                        "errorMessage": "ErrorAction called but no error found. Validate your DAG.",
                    }
                )
                resp.status_code = self._status_codes["success"]
                return self._status_codes["success"], req, resp

        except Exception as err:
            req.logger.log_error("ErrorAction could not processed.", traceback.format_exc(), 125, req)
            resp.is_error = True
            resp.error = err
            return self._status_codes["error"], req, resp
