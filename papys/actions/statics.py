import json
import traceback
from typing import Tuple
from papys.actions.core import PAction
from papys.request_response import Request, Response


class StaticJsonAction(PAction):
    """
    Class providing a simple JSON response.
    You can use this class to transfer a JSON object, which is then written to the response.
    You can use it for test purposes, but also productively if you want to deliver a short static content for an endpoint.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
        json (dict) : The JSON to deliver as response content.
        status_codes (dict): You can customize the returned status in case of success and an error. Default: { 'success': 200, 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        json: dict = {},
        status_codes={"success": 200, "error": 500},
    ):
        self._json = json
        self._status_codes = status_codes
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            resp.to_convert = self._json
            resp.json = json.dumps(self._json)
            resp.status_code = self._status_codes["success"]
            return self._status_codes["success"], req, resp
        except Exception as err:
            req.logger.log_error(
                "StaticJsonAction could not processed.", traceback.format_exc(), 121, req
            )
            resp.is_error = True
            resp.error = err
            return self._status_codes["error"], req, resp


# TODO
# class StaticFileAction(PAction)
# return the File from path. Basedirectory is set in the global config.