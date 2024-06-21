import traceback
from typing import Tuple
from papys.actions.core import PAction
from papys.request_response import Request, Response


class RedirectAction(PAction):
    """
    Class providing a client redirect.
    This implementation sets the http header "Location" to the desired URL
    and the http status code to the selected status code. E.g. 302.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
        url (str): The url for the http header 'Location' for the redirect.
        redirect_status_code (int): The desired http status code for the redirection. Default: 302.
        status_codes (dict): You can customize the returned status in case of an error. Default: { 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        url: str = "/",
        redirect_status_code=302,
        status_codes={"error": 500},
    ):
        self._url = url
        self.redirect_status_code = redirect_status_code
        self._status_codes = status_codes
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            resp.set_header("Location", self._url)
            resp.status_code = self.redirect_status_code
            return self.redirect_status_code, req, resp
        except Exception as err:
            req.logger.log_error(
                "RedirectAction could not processed.", traceback.format_exc(), 122, req
            )
            resp.is_error = True
            resp.error = err
            return self._status_codes["error"], req, resp
