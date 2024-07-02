import traceback
from typing import Tuple
import requests
from papys.actions.core import PAction
from papys.request_response import Request, Response, COOKIE_SAME_SITE_LAX


class KcOidcAcfCallbackAction(PAction):
    """
    A class that handle the Keycloak callback call after the user login.
    This class is created from KcOIDCFactory. It's recommended to not
    instance this class yourself.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
        config (dict): The configuration of the process: {
                "base_url": "",
                "client_id": "",
                "client_secret": "",
                "redirect_url": "",
                "app_redirect_url": "",
            }
        status_codes (dict): You can customize the returned status in case of an error. Default: { 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        config: dict = {},
        status_codes={"error": 500},
    ):
        self._status_codes = status_codes
        self._config = config
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            code = req.query_string_dict.get("code", None)
            if code:
                token_response = requests.post(
                    self._config.get("base_url") + "/protocol/openid-connect/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self._config.get("redirect_url"),
                        "client_id": self._config.get("client_id"),
                        "client_secret": self._config.get("client_secret"),
                    },
                )
                token = token_response.json()
                if "access_token" in token:
                    access_token = token["access_token"]
                    refresh_token = token["refresh_token"]

                    resp.add_cookie(
                        "access_token",
                        access_token,
                        resp.create_cookie_attributes(
                            http_only=True,
                            same_site=COOKIE_SAME_SITE_LAX,
                            path="/",
                            secure=True,
                        ),
                    )

                    resp.add_cookie(
                        "refresh_token",
                        refresh_token,
                        resp.create_cookie_attributes(
                            http_only=True,
                            same_site=COOKIE_SAME_SITE_LAX,
                            path="/",
                            secure=True,
                        ),
                    )
                    resp.set_header("Location", self._config.get("app_redirect_url"))
                    return 302, req, resp
                else:
                    req.logger.log_warning(
                        f"Authorization failed, 401. Token: {token}",
                        req=req,
                        log_code=170,
                    )
                    return 401, req, resp
            else:
                req.logger.log_warning("Unauthorized 400", req=req, log_code=171)
                return 400, req, resp

        except Exception as err:
            req.logger.log_error(
                "KcOAuth2CallbackAction could not processed.",
                traceback.format_exc(),
                172,
                req,
            )
            resp.is_error = True
            resp.error = err
            return self._status_codes["error"], req, resp


class KcOidcAcfLogoutAction(PAction):
    """
    A class handle the logout request from a client.
    This class is created from KcOIDCFactory. It's recommended to not
    instance this class yourself.

    Args:
        name (str): Die argument is only for you to describe the action in the source code. It's optional.
        config (dict): The configuration of the action: {
                "base_url": "",
                "client_id": "",
                "client_secret": "",
            }
        status_codes (dict): You can customize the returned status in case of an error. Default: { 'error': 500 }.
    """

    def __init__(
        self,
        name: str = "",
        config: dict = {},
        status_codes={"error": 500},
    ):
        self._status_codes = status_codes
        self._config = config
        super().__init__(name=name)

    def process(self, req: Request, resp: Response) -> Tuple[int, Request, Response]:
        try:
            logout_response = requests.post(
                self._config.get("base_url") + "/protocol/openid-connect/logout",
                headers={
                    "Authorization": f"Bearer {req.parsed_cookie.get('access_token', '')}"
                },
                data={
                    "client_id": self._config.get("client_id"),
                    "client_secret": self._config.get("client_secret"),
                    "refresh_token": req.parsed_cookie.get("refresh_token", ""),
                },
            )

            if logout_response.status_code == 204:
                resp.remove_cookie_from_client("access_token")
                resp.remove_cookie_from_client("refresh_token")

                redirect_url = req.query_string_dict.get("redirect_url", None)
                if redirect_url:
                    resp.set_header("Location", redirect_url)
                    return 302, req, resp
                else:
                    resp.to_convert = {"logout": "successful"}
                    return 200, req, resp
            elif logout_response.status_code == 400:
                resp.to_convert = {"logout": "No active user to log out."}
                req.logger.log_warning(
                    "Logout but no activ user.",                    
                    172,
                    req,
                )
                return 400, req, resp
            else:
                req.logger.log_error(
                    "Logout failed",
                    f"IAM status code: {logout_response.status_code}",
                    173,
                    req,
                )
                return 500, req, resp

        except Exception as err:
            req.logger.log_error(
                "KcOIDCLogoutAction could not processed.",
                traceback.format_exc(),
                174,
                req,
            )
            resp.is_error = True
            resp.error = err
            return self._status_codes["error"], req, resp
