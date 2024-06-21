import traceback
from typing import Tuple
from papys.actions.core import PAction
from papys.request_response import Request, Response


class PostBounceAction(PAction):
    """
    Class providing a simple post mockup.
    This implementation does nothing other than return a body that has been sent by a client 1:1,
    i.e. write it to the response. The class is purely for test purposes.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
        status_codes (dict): You can customize the returned status in case of success and an error. Default: { 'success': 200, 'error': 500 }.
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
            resp.to_convert = req.body_json
            return self._status_codes["success"], req, resp
        except Exception as err:
            req.logger.log_error(
                "PostBounceAction could not processed.", traceback.format_exc(), 140, req
            )
            resp.is_error = True
            resp.error = err
            return self._status_codes["error"], req, resp


class DummyAction(PAction):
    """
    Class providing a dummy action.
    This implementation does exactly nothing.
    It only returns the parameters with status code 200.
    It is only used for testing purposes.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
    """

    def __init__(self, name: str = ""):
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        return 200, req, resp
