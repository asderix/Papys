import traceback
import requests
from typing import Tuple
from collections.abc import Iterable
from papys.http_methods import GET, POST, PUT, DELETE
from papys.hooks import PHook
from papys.request_response import (
    Request,
    Response,
    COOKIE_SAME_SITE_STRICT,
)

AUTH_ALLOW = "allow"
AUTH_DENY = "deny"


class KcOidcAcfRouteGuardHook(PHook):
    """
    PHook implementation to secure a route with Keycloak OICD.
    This hook will be generated by the KcOIDCFactory class.
    It's recommended to not instance this class yourself.

    Args:
        config (dict): The OICD configuration for checking the authoritiy.
        status_codes (dict): {'success': 200, 'unauthorized': 401, 'error': 500} is default. You can provide other codes to return in case of success or an exception.
    """

    def __init__(
        self,
        config=None,
        status_codes: dict = {"success": 200, "unauthorized": 401, "error": 500},
    ):
        self._config = config
        self._status_codes = status_codes
        super().__init__()

    def process_hook(
        self, req: Request, resp: Response
    ) -> Tuple[bool, int, Request, Response]:
        try:
            access_token = req.parsed_cookie.get("access_token", None)
            if access_token:
                user_info_response = requests.get(
                    self._config.get("base_url") + "/protocol/openid-connect/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                if user_info_response.status_code == 200:
                    req.user_info = user_info_response.json()
                    return True, self._status_codes["success"], req, resp
                else:
                    payload = {
                        "grant_type": "refresh_token",
                        "client_id": self._config.get("client_id"),
                        "client_secret": self._config.get("client_secret"),
                        "refresh_token": req.parsed_cookie.get("refresh_token", None),
                    }

                    response = requests.post(
                        self._config.get("base_url") + "/protocol/openid-connect/token",
                        data=payload,
                    )
                    response_data = response.json()

                    if response.status_code == 200:
                        resp.add_cookie(
                            "access_token",
                            response_data["access_token"],
                            resp.create_cookie_attributes(
                                http_only=True,
                                same_site=COOKIE_SAME_SITE_STRICT,
                                secure=True,
                            ),
                        )

                        resp.add_cookie(
                            "refresh_token",
                            response_data["refresh_token"],
                            resp.create_cookie_attributes(
                                http_only=True,
                                same_site=COOKIE_SAME_SITE_STRICT,
                                secure=True,
                            ),
                        )
                        user_info_response = requests.get(
                            self._config.get("base_url")
                            + "/protocol/openid-connect/userinfo",
                            headers={
                                "Authorization": f"Bearer {response_data['access_token']}"
                            },
                        )
                        if user_info_response.status_code == 200:
                            req.user_info = user_info_response.json()
                            return True, self._status_codes["success"], req, resp
                        else:
                            req.logger.log_warning(
                                f"Blocked unauthorized access, 401. Token refresh successful but get user info failes. access_token: {response_data['access_token']}",
                                131,
                                req,
                            )
                            return False, self._status_codes["unauthorized"], req, resp
                    else:
                        req.logger.log_warning(
                            f"Blocked unauthorized access, 401. Token refresh failed. access_token: {access_token}",
                            131,
                            req,
                        )
                        if self._config.get("redirect_to_login", False):
                            resp.set_header("Location", self._config.get("login_path"))
                            return False, 302, req, resp
                        else:
                            return False, self._status_codes["unauthorized"], req, resp
            else:
                req.logger.log_warning(
                    "Blocked unauthorized access, 401. No access_token found.", 132, req
                )
                if self._config.get("redirect_to_login", False):
                    resp.set_header("Location", self._config.get("login_path"))
                    return False, 302, req, resp
                else:
                    return False, self._status_codes["unauthorized"], req, resp
        except Exception as err:
            req.logger.log_error(
                "KcOidcAcfRouteGuardHook could not processed.",
                traceback.format_exc(),
                133,
                req,
            )
            return False, self._status_codes["error"], req, resp


class KcOidcCcfRouteGuardHook(PHook):
    """
    PHook implementation to secure a route with Keycloak OICD.
    This hook will be generated by the KcOIDCFactory class.
    It's recommended to not instance this class yourself.

    Args:
        config (dict): The OICD configuration for checking the authoritiy.
        status_codes (dict): {'success': 200, 'unauthorized': 401, 'error': 500} is default. You can provide other codes to return in case of success or an exception.
    """

    def __init__(
        self,
        config=None,
        status_codes: dict = {"success": 200, "unauthorized": 401, "error": 500},
    ):
        self._config = config
        self._status_codes = status_codes
        super().__init__()

    def process_hook(
        self, req: Request, resp: Response
    ) -> Tuple[bool, int, Request, Response]:
        try:
            access_token = req.get_bearer_token()
            if access_token:
                data = {
                    "token": access_token,
                    "client_id": self._config.get("client_id", ""),
                    "client_secret": self._config.get("client_secret", ""),
                }
                token_response = requests.post(
                    self._config.get("validate_url"),
                    data=data,
                )
                token_valid_response = token_response.json()
                if token_valid_response.get("active"):
                    req.user_info = token_valid_response
                    return True, self._status_codes["success"], req, resp
                else:
                    req.logger.log_warning(
                        "Blocked unauthorized access, 401. Invalid access token",
                        132,
                        req,
                    )
                    return False, self._status_codes["unauthorized"], req, resp
            else:
                req.logger.log_warning(
                    "Blocked unauthorized access, 401. No access_token found.", 133, req
                )
                return False, self._status_codes["unauthorized"], req, resp

        except Exception as err:
            req.logger.log_error(
                "KcOidcCcfRouteGuardHook could not processed.",
                traceback.format_exc(),
                134,
                req,
            )
            return False, self._status_codes["error"], req, resp


class UserInfoAuthorizationHook(PHook):
    def __init__(self):
        super().__init__()
        self._type: str = AUTH_ALLOW
        self._user_info_group_attribute_name: str = "roles"
        self._GET_groups: set = set()
        self._POST_groups: set = set()
        self._PUT_groups: set = set()
        self._DELETE_groups: set = set()
        self._add_user_sub_to_body: bool = False
        self._user_id_body_attribute_name: str | None = "user_id"

    @property
    def type(self) -> str:
        return self._type

    @type.setter
    def type(self, value: str) -> None:
        self._type = value

    @property
    def user_info_group_attribute_name(self) -> str:
        return self._user_info_group_attribute_name

    @user_info_group_attribute_name.setter
    def user_info_group_attribute_name(self, value: str) -> None:
        self._user_info_group_attribute_name = value

    @property
    def GET_groups(self) -> set:
        return self._GET_groups

    @GET_groups.setter
    def GET_groups(self, value: set) -> None:
        self._GET_groups = value

    @property
    def POST_groups(self) -> set:
        return self._POST_groups

    @POST_groups.setter
    def POST_groups(self, value: set) -> None:
        self._POST_groups = value

    @property
    def PUT_groups(self) -> set:
        return self._PUT_groups

    @PUT_groups.setter
    def PUT_groups(self, value: set) -> None:
        self._PUT_groups = value

    @property
    def DELETE_groups(self) -> set:
        return self._DELETE_groups

    @DELETE_groups.setter
    def DELETE_groups(self, value: set) -> None:
        self._DELETE_groups = value

    @property
    def add_user_sub_to_body(self) -> bool:
        return self._add_user_sub_to_body

    @add_user_sub_to_body.setter
    def add_user_sub_to_body(self, value: bool) -> None:
        self._add_user_sub_to_body = value

    @property
    def user_id_body_attribute_name(self) -> str | None:
        return self._user_id_body_attribute_name

    @user_id_body_attribute_name.setter
    def user_id_body_attribute_name(self, value: str | None) -> None:
        self._user_id_body_attribute_name = value

    def process_hook(
        self, req: Request, resp: Response
    ) -> Tuple[bool, int, Request, Response]:
        try:
            user_groups = req.user_info[self.user_info_group_attribute_name]
            if isinstance(user_groups, Iterable):
                user_groups_set = set(user_groups)
                match req.request_method:
                    case "GET":
                        group_check = len(user_groups_set & self.GET_groups)
                    case "POST":
                        group_check = len(user_groups_set & self.POST_groups)
                    case "PUT":
                        group_check = len(user_groups_set & self.PUT_groups)
                    case "DELETE":
                        group_check = len(user_groups_set & self.DELETE_groups)
                    case _:
                        raise ValueError(
                            f"Not supported http method found: {req.request_method}."
                        )

                match (self.type, group_check):
                    case ("allow", n) if n > 0:
                        if self.add_user_sub_to_body and req.body_json:
                            req.body_json[self.user_id_body_attribute_name] = (
                                req.user_info["sub"]
                            )
                        return True, 200, req, resp
                    case ("allow", n) if n < 1:
                        return False, 401, req, resp
                    case ("deny", n) if n < 1:
                        if self.add_user_sub_to_body and req.body_json:
                            req.body_json[self.user_id_body_attribute_name] = (
                                req.user_info["sub"]
                            )
                        return True, 200, req, resp
                    case ("deny", n) if n > 0:
                        return False, 401, req, resp
                    case _:
                        return False, 401, req, resp
            else:
                return False, 401, req, resp
        except Exception as err:
            req.logger.log_error(
                "Failed to check user groups.", traceback.format_exc(), 136, req
            )
            return False, 500, req, resp


class KcAcfCcfSwitchHook(PHook):
    def __init__(self, *, acfHook: PHook, ccfHook: PHook):
        super().__init__()
        self._acfHook: PHook = acfHook
        self._ccfHook: PHook = ccfHook

    def process_hook(
        self, req: Request, resp: Response
    ) -> Tuple[bool, int, Request, Response]:
        try:
            if req.get_bearer_token():
                ccf_result = self._ccfHook.process_hook(req, resp)
                if ccf_result[0]:
                    req.authentication_method = "kcCcf"
                    return ccf_result
            acf_result = self._acfHook.process_hook(req, resp)
            if acf_result[0]:
                req.authentication_method = "kcAcf"
            return acf_result
        except Exception as err:
            req.logger.log_error(
                "Failed to process KcAcfCcfSwitchHook.",
                traceback.format_exc(),
                137,
                req,
            )
            return False, 500, req, resp


class ApiKeyAuthorizationHook(PHook):
    def __init__(
        self,
        api_keys: list,
        api_key_qp_name: str = "apiKey",
        api_key_header_name: str = "Authorization",
        user_info_group_attribute_name: str = "roles",
    ):
        self._api_keys = api_keys
        self._api_key_qp_name = api_key_qp_name
        self._api_key_header_name = api_key_header_name
        self._user_info_group_attribute_name = user_info_group_attribute_name
        super().__init__()
        self._api_keys_dict: dict = {}
        for api_key in api_keys:
            self._api_keys_dict[api_key.key] = api_key

    def process_hook(
        self, req: Request, resp: Response
    ) -> Tuple[bool, int, Request, Response]:
        try:
            qp_api_key = req.query_string_dict.get(self._api_key_qp_name, None)
            if qp_api_key:
                api_key_check = self._api_keys_dict.get(qp_api_key, None)
                if api_key_check:
                    req.user_info = {
                        "api_key": qp_api_key,
                        self._user_info_group_attribute_name: api_key_check.groups,
                    }
                    return True, 200, req, resp
            header_api_key = req.authorization_header
            if header_api_key:
                api_key_check = self._api_keys_dict.get(header_api_key, None)
                if api_key_check:
                    req.user_info = {
                        "api_key": header_api_key,
                        self._user_info_group_attribute_name: api_key_check.groups,
                    }
                    return True, 200, req, resp
            req.logger.log_warning("Blocked unauthorized request.", 138, req)
            return False, 401, req, resp
        except Exception as err:
            req.logger.log_error(
                "Failed to process ApiKeyAuthorizationHook.",
                traceback.format_exc(),
                139,
                req,
            )
            return False, 500, req, resp
