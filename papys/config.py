class PConfig:
    """
    Class to configure the Papys application.

    Args:
        log_level (int): 1: Errors only. 2: Errors and warnings. 3: All incl. information. Default is 2.
        post_convert_201 (bool): True: If status is 200 and http method is post, then http status is set to 201. Default is True.
        return_error500_body (bool): True: In case of status 500 a return body from Response.error_message field is created. Default is False.
        accept_default_lang (str): If the http accept lang header is missing this one is set. Default is 'US-en'.

    """

    def __init__(
        self,
        log_level: int = 2,
        post_convert_201: bool = True,
        return_error500_body: bool = False,
        accept_default_lang: str = "en-US",
    ):
        self._log_level = log_level
        self._post_convert_201 = post_convert_201
        self._return_error500_body = return_error500_body
        self._accept_default_lang = accept_default_lang

    @property
    def log_level(self) -> int:
        return self._log_level

    @log_level.setter
    def log_level(self, value: int):
        self._log_level = value

    @property
    def post_convert_201(self) -> bool:
        return self._post_convert_201

    @post_convert_201.setter
    def post_convert_201(self, value: bool):
        self._post_convert_201 = value

    @property
    def return_error500_body(self) -> bool:
        return self._return_error500_body

    @return_error500_body.setter
    def return_error500_body(self, value: bool):
        self._return_error500_body = value

    @property
    def accept_default_lang(self) -> str:
        return self._accept_default_lang

    @accept_default_lang.setter
    def accept_default_lang(self, value: str):
        self._accept_default_lang = value
