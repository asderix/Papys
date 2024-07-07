from urllib.parse import urlencode
import papys.core
from papys.route import PRoute as R
from papys.actions.flows import RedirectAction
from papys.http_methods import GET
from papys.hooks import PHook
from papys.security_hooks import KcOidcAcfRouteGuardHook, KcOidcCcfRouteGuardHook
from papys.actions.authentication import KcOidcAcfCallbackAction, KcOidcAcfLogoutAction


class KcOidcAcfFactory:
    """
    A class providing Keycloak OIDC security on the Papys app
    with Authorization Code Flow.
    Use this factory with the with statement:

    Minimum usage:

    with KcOidcAcfFactory() as oidc:
        oidc.server_host = "https://host-of-papys-rest-api.com"
        oidc.auth_url = "https://host-of-keycloak.com/auth/realms/"
        oidc.client_id = "client-id"
        oidc.client_secret = "the-secret-from-keycloak"
        oidc.realm = "your-realm"
        oidc.app_redirect_url = "http://example.com/where-your-app-is"

    Full configuration:

    with KcOidcAcfFactory() as oidc:
        oidc.server_host = "https://host-of-papys-rest-api.com"
        oidc.callback_path = "/callback"
        oidc.login_path = "/login"
        oidc.logout_path = "/logout"
        oidc.auth_url = "https://host-of-keycloak.com/auth/realms/"
        oidc.client_id = "client-id"
        oidc.client_secret = "the-secret-from-keycloak"
        oidc.realm = "your-realm"
        oidc.redirect_to_login = True
        oidc.app_redirect_url = "http://example.com/where-your-app-is"

    Get your guard hook:

    oicd_guard = oidc.get_route_guard_hook()

    Now you can use this hook in your route(s) you want to protect:

    protected_route = R("/protected", oicd_guard) >> [
        (GET, YourActionHere("My action"))
    ]

    """

    def __init__(self):
        self._server_host: str | None = None
        self._callback_path: str | None = "/callback"
        self._login_path: str | None = "/login"
        self._logout_path: str | None = "/logout"
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._auth_url: str | None = None
        self._realm: str | None = None
        self._app_redirect_url: str | None = None
        self._redirect_to_login: bool = False

        self._auth_url_postfix: str | None = "protocol/openid-connect/auth"
        self._is_open: bool = True

    @property
    def server_host(self):
        return self._server_host

    @server_host.setter
    def server_host(self, value: str | None):
        self._server_host = value

    @property
    def callback_path(self):
        return self._callback_path

    @callback_path.setter
    def callback_path(self, value: str | None):
        self._callback_path = value

    @property
    def login_path(self):
        return self._login_path

    @login_path.setter
    def login_path(self, value: str | None):
        self._login_path = value

    @property
    def logout_path(self):
        return self._logout_path

    @logout_path.setter
    def logout_path(self, value: str | None):
        self._logout_path = value

    @property
    def client_id(self):
        return self._client_id

    @client_id.setter
    def client_id(self, value: str | None):
        self._client_id = value

    @property
    def client_secret(self):
        return self._client_secret

    @client_secret.setter
    def client_secret(self, value: str | None):
        self._client_secret = value

    @property
    def auth_url(self):
        return self._auth_url

    @auth_url.setter
    def auth_url(self, value: str | None):
        self._auth_url = value

    @property
    def realm(self):
        return self._realm

    @realm.setter
    def realm(self, value: str | None):
        self._realm = value

    @property
    def app_redirect_url(self):
        return self._app_redirect_url

    @app_redirect_url.setter
    def app_redirect_url(self, value: str | None):
        self._app_redirect_url = value

    @property
    def redirect_to_login(self):
        return self._redirect_to_login

    @redirect_to_login.setter
    def redirect_to_login(self, value: bool):
        self._redirect_to_login = value

    def get_route_guard_hook(self) -> PHook:
        config = {
            "base_url": f"{self.auth_url}/{self._realm}/",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_to_login": self.redirect_to_login,
            "login_path": self.login_path,
        }
        return KcOidcAcfRouteGuardHook(config)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        redirect_url = f"{self.server_host + self.callback_path}"
        if self._is_open:
            query_param = {
                "client_id": self.client_id,
                "response_type": "code",
                "scope": "openid",
                "redirect_uri": redirect_url,
            }
            login_route = R(self.login_path) >> [
                (
                    GET,
                    RedirectAction(
                        "Redirect to IAM login url",
                        url=f"{self.auth_url}/{self._realm}/{self._auth_url_postfix}?{urlencode(query_param, safe=':/')}",
                    ),
                )
            ]
            papys.core.add_route(login_route)

            config = {
                "base_url": f"{self.auth_url}/{self._realm}/",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_url": redirect_url,
                "app_redirect_url": self.app_redirect_url,
            }

            callback_route = R(self.callback_path) >> [
                (GET, KcOidcAcfCallbackAction("Handle IAM callback", config))
            ]
            papys.core.add_route(callback_route)

            logout_config = {
                "base_url": f"{self.auth_url}/{self._realm}/",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            logout_route = R(self.logout_path) >> [
                (GET, KcOidcAcfLogoutAction("Logout user at IAM", logout_config))
            ]
            papys.core.add_route(logout_route)

            self._is_open = False


class KcOidcCcfFactory:
    """
    A class providing Keycloak OIDC security on the Papys app
    with Client Credential Flow (M2M).
    Use this factory with the with statement:

    Usage:

    with KcOidcCcfFactory() as oidc:
        oidc.auth_url = "https://host-of-keycloak.com/auth/realms/"
        oidc.realm = "your-realm"

    Get your guard hook:

    oicd_guard = oidc.get_route_guard_hook()

    Now you can use this hook in your route(s) you want to protect:

    protected_route = R("/protected", oicd_guard) >> [
        (GET, YourActionHere("My action"))
    ]

    """

    def __init__(self):
        self._auth_url: str | None = None
        self._realm: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None

        self._auth_url_postfix: str | None = "protocol/openid-connect/token/introspect"
        self._is_open: bool = True

    @property
    def auth_url(self):
        return self._auth_url

    @auth_url.setter
    def auth_url(self, value: str | None):
        self._auth_url = value

    @property
    def realm(self):
        return self._realm

    @realm.setter
    def realm(self, value: str | None):
        self._realm = value

    @property
    def client_id(self):
        return self._client_id
    
    @client_id.setter
    def client_id(self, value: str):
        self._client_id = value

    @property
    def client_secret(self):
        return self._client_secret
    
    @client_secret.setter
    def client_secret(self, value: str):
        self._client_secret = value


    def get_route_guard_hook(self) -> PHook:
        config = {
            "validate_url": f"{self.auth_url}/{self._realm}/{self._auth_url_postfix}",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        return KcOidcCcfRouteGuardHook(config)

    def __enter__(self):
        return self

    def __exit__(self, *args):        
        if self._is_open:
            self._is_open = False
