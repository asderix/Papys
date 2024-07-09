import uuid
from papys.route import PRoute as R
from papys.actions.statics import StaticJsonAction as JsonA
from papys.actions.core import PAction as A
from papys.actions.schema_validators import JsonRespValidatorAction as RespV
from papys.actions.schema_validators import JsonReqValidatorAction as ReqV
from papys.actions.error_handlers import ErrorAction as ErrA
from papys.actions.mocks import PostBounceAction as PostA
from papys.actions.mocks import DummyAction as DA
from papys.hooks import PHook as Hook
from papys.hooks import ParaMapHook, FunctionHook
from papys.request_response import Request, Response
from papys.http_methods import GET, POST, PUT, DELETE
from papys.config import PConfig
import papys.core as papys
import papys.server as dev_server
from papys.security import KcOidcAcfFactory
from papys.security_hooks import UserInfoAuthorizationHook


"""
Document stuff
"""


docs_get_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "docId": {"type": "string", "format": "uuid"},
            "documentName": {"type": "string"},
            "documentType": {"type": "string"},
        },
        "required": ["docId"],
    },
}

doc_get_schema = {
    "type": "object",
    "properties": {
        "docId": {"type": "string", "format": "uuid"},
        "documentName": {"type": "string"},
        "documentType": {"type": "string"},
    },
    # "required": ["docId"], For using the simple PostBounceAction action it's not required.
}

doc_post_schema = {
    "type": "object",
    "properties": {
        "documentName": {"type": "string"},
        "documentType": {"type": "string"},
    },
    "required": ["documentName"],
    "additionalProperties": True,
}


def read_documents(req: Request, resp: Response):
    resp.to_convert = [
        {
            "docId": f"{req.path_variables.get('doc_owner', '?')} - {req.path_variables.get('owner_id', '?')} :c2fe8cee-d831-46f1-902c-92603ea06dfc",
            "documentName": "My first document",
            "documentType": "application/pdf",
        },
        {
            "docId": f"{req.path_variables.get('doc_owner', '?')} - {req.path_variables.get('owner_id', '?')} :7472cfbe-03d4-4f23-8fbe-623536198225",
            "documentName": "My second document",
            "documentType": "application/pdf",
        },
    ]

    return 200, req, resp


def read_document(req: Request, resp: Response):
    resp.to_convert = {
        "docId": f"{req.path_variables.get('doc_owner', '?')} - {req.path_variables.get('owner_id', '?')}, doc_id: {req.path_variables.get('doc_id', '?')}",
        "documentName": "My first document",
        "documentType": "application/pdf",
    }

    return 200, req, resp


"""
User stuff
"""


def read_users(req: Request, resp: Response):
    resp.to_convert = [
        {
            "userId": "712467cf-6b6b-4959-9cc1-5742d533177d",
            "username": "John Doe",
            "email": "jon@example.com",
        },
        {"userId": "3a8c0370-0deb-4feb-a80f-10d13a2ffdab", "username": "Jane Doe"},
    ]
    return 200, req, resp


def read_user(req: Request, resp: Response):
    resp.to_convert = {
        "userId": req.path_variables.get("user_id", ""),
        "username": "John Doe",
        "email": "jon@example.com",
    }
    return 200, req, resp


def read_user_from_post(req: Request, resp: Response):
    resp.to_convert = {
        "userId": req.process_data.get("userId", ""),
        "username": req.process_data.get("username", ""),
        "email": req.process_data.get("email", ""),
    }
    return 200, req, resp


def save_user(req: Request, resp: Response):
    req.process_data["userId"] = str(uuid.uuid4())
    req.process_data["username"] = req.body_json["username"]
    req.process_data["email"] = req.body_json["email"]
    return 200, req, resp


def update_user(req: Request, resp: Response):
    return 200, req, resp


# This function is not used. Instead, a lamda function is used directly as an example.
def delete_user(req: Request, resp: Response):
    pass


user_get_schema = {
    "type": "object",
    "properties": {
        "userId": {"type": "string", "format": "uuid"},
        "username": {"type": "string"},
        "email": {"type": "string"},
    },
    "required": ["userId", "username"],
}

users_get_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "userId": {"type": "string", "format": "uuid"},
            "username": {"type": "string"},
            "email": {"type": "string"},
        },
        "required": ["userId", "username"],
    },
}

user_post_schema = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "email": {"type": "string"},
    },
    "required": ["username"],
}

user_put_schema = {
    "type": "object",
    "properties": {
        "email": {"type": "string"},
    },
    "additionalProperties": False,
}


"""
Supplier stuff
"""


class ReadSuppliersAction(A):
    def __init__(self, name):
        super().__init__(name=name)
        self._response = [
            {
                "supplierId": "e394cdbf-a6fb-4d2b-8406-1ec47bed9709",
                "companyName": "Example & Co. ltd",
                "email": "contact@example.com",
            },
            {
                "supplierId": "d0455fbe-44db-4b35-8750-896a33674e38",
                "companyName": "Me & Brothers llc",
                "email": "brothers@example.com",
            },
        ]

    def process(
        self, req: Request, resp: Response
    ) -> papys.Tuple[int, Request, Response]:
        resp.to_convert = self._response
        return 200, req, resp


def read_supplier(req: Request, resp: Response):
    resp.to_convert = {
        "supplierId": req.path_variables.get("supplier_id", ""),
        "companyName": "A Company Name ltd",
        "email": "some@example.com",
    }
    return 200, req, resp


def read_supplier_from_post(req: Request, resp: Response):
    resp.to_convert = {
        "supplierId": req.process_data.get("supplierId", ""),
        "companyName": req.process_data.get("companyName", ""),
        "email": req.process_data.get("email", ""),
    }
    return 200, req, resp


def save_supplier(req: Request, resp: Response):
    req.process_data["supplierId"] = str(uuid.uuid4())
    req.process_data["companyName"] = req.body_json["companyName"]
    req.process_data["email"] = req.body_json["email"]
    return 200, req, resp


def update_supplier(req: Request, resp: Response):
    return 200, req, resp


supplier_get_schema = {
    "type": "object",
    "properties": {
        "supplierId": {"type": "string", "format": "uuid"},
        "companyName": {"type": "string"},
        "email": {"type": "string"},
    },
    "required": ["supplierId", "companyName"],
}

suppliers_get_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "supplierId": {"type": "string", "format": "uuid"},
            "companyName": {"type": "string"},
            "email": {"type": "string"},
        },
        "required": ["supplierId", "companyName"],
    },
}

supplier_post_schema = {
    "type": "object",
    "properties": {
        "companyName": {"type": "string"},
        "email": {"type": "string"},
    },
    "required": ["companyName"],
}

"""
Route definitions
"""

doc_route = R("/document") >> [
    (
        GET,
        A("Read documents", read_documents)
        >> [
            (
                200,
                RespV("Validate respone", docs_get_schema)
                >> [(500, ErrA("Handle validation error"))],
            ),
            (500, ErrA("Handle read document error")),
        ],
    ),
    (
        POST,
        ReqV("Validate input", doc_post_schema)
        >> [
            (
                200,
                PostA("Save document")
                >> [
                    (
                        200,
                        DA("Read document")
                        >> [
                            (
                                200,
                                RespV("Validate response", doc_get_schema)
                                >> [(500, ErrA("Handle verification error"))],
                            ),
                            (500, ErrA("Handle read error")),
                        ],
                    ),
                    (500, ErrA("Handle save error")),
                ],
            ),
            (500, ErrA("Handle validation error")),
        ],
    ),
] | R("/{doc_id}") >> [
    (
        GET,
        A("Read document", read_document)
        >> [
            (
                200,
                RespV("Validate response", doc_get_schema)
                >> [(500, ErrA("Handle validation error"))],
            ),
            (500, ErrA("Handle read error")),
        ],
    ),
    (
        PUT,
        ReqV("Validate input", doc_post_schema)
        >> [
            (200, DA("Update document") >> [(500, ErrA("Handle update error"))]),
            (500, ErrA("Handle input validation error")),
        ],
    ),
    (DELETE, DA("Delete document") >> [(500, ErrA("Handle delete error"))]),
]

users_route = R("/user") >> [
    (
        GET,
        A("List all users", read_users)
        >> [
            (
                200,
                RespV("Validate response", users_get_schema)
                >> [(500, ErrA("Handle validation error"))],
            ),
            (500, ErrA("Handle reading error")),
        ],
    ),
    (
        POST,
        ReqV("Validate input", user_post_schema)
        >> [
            (
                200,
                A("Save user", save_user)
                >> [
                    (
                        200,
                        A("Read user", read_user_from_post)
                        >> [
                            (
                                200,
                                RespV("Validate response", user_get_schema)
                                >> [(500, ErrA("Handle response validation error"))],
                            ),
                            (500, ErrA("Handle read error")),
                        ],
                    ),
                    (500, ErrA("Handle save error")),
                ],
            ),
            (500, ErrA("Handle input validation error")),
        ],
    ),
]

user_route = R(
    "/{user_id}", ParaMapHook({"owner_id": "{user_id}", "doc_owner": "customer"})
) >> [
    (
        GET,
        A("Read user", read_user)
        >> [
            (
                200,
                RespV("Validate response", user_get_schema)
                >> [(500, ErrA("Handle verification error"))],
            ),
            (500, ErrA("Handle read error")),
        ],
    ),
    (
        PUT,
        ReqV("Validate request", user_put_schema)
        >> [
            (
                200,
                A("Update user", update_user)
                >> [(500, ErrA("Handle user update error"))],
            ),
            (500, ErrA("Handle request verification error")),
        ],
    ),
    (
        DELETE,
        A("Delete user", lambda req, resp: (200, req, resp))
        >> [(500, ErrA("Handle user deletion error"))],
    ),
]

suppliers_route = R("/supplier") >> [
    (
        GET,
        ReadSuppliersAction("Read suppliers")
        >> [
            (
                200,
                RespV("Validate response", suppliers_get_schema)
                >> [(500, ErrA("Handle validation error"))],
            ),
            (500, ErrA("Handle read error")),
        ],
    ),
    (
        POST,
        ReqV("Validate request", supplier_post_schema)
        >> [
            (
                200,
                A("Save supplier", save_supplier)
                >> [
                    (500, ErrA("Handle save error")),
                    (
                        200,
                        A("Read supplier from Post", read_supplier_from_post)
                        >> [
                            (
                                200,
                                RespV("Validate response", supplier_get_schema)
                                >> [(500, ErrA("Handle response validation error"))],
                            ),
                            (500, ErrA("Handle read error form post")),
                        ],
                    ),
                ],
            ),
            (500, ErrA("Handle request validation error")),
        ],
    ),
]

supplier_route = R(
    "/{supplier_id}",
    ParaMapHook({"owner_id": "{supplier_id}", "doc_owner": "supplier"}),
) >> [
    (
        GET,
        A("Read supplier", read_supplier)
        >> [
            (
                200,
                RespV("Validate response", supplier_get_schema)
                >> [(500, ErrA("Handle verification error"))],
            ),
            (500, ErrA("Handle read error")),
        ],
    ),
    (
        PUT,
        ReqV("Validate request", supplier_post_schema)
        >> [
            (
                200,
                A("Update user", update_supplier)
                >> [(500, ErrA("Handle user update error"))],
            ),
            (500, ErrA("Handle request verification error")),
        ],
    ),
    (
        DELETE,
        A("Delete supplier", lambda req, resp: (200, req, resp))
        >> [(500, ErrA("Handle supplier deletion error"))],
    ),
]

schema_error_sanitizer_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
    },
    "required": ["name"],
    "additionalProperties": False,
}

bad_response = {"name": "Testname", "addElement": "Not allowed"}


test_neg_route = R("/test") >> [
    (
        GET,
        JsonA("A bad response", bad_response)
        >> [
            (
                200,
                RespV("Validate schema", schema_error_sanitizer_schema)
                >> [(500, ErrA("Handle Schema error"))],
            )
        ],
    )
]


def set_cookie(req: Request, resp: Response):
    resp.add_cookie(
        "authcookie",
        "Bearer 123",
        resp.create_cookie_attributes(
            http_only=True, same_site="Strict", http_domain="localhost"
        ),
    )

    resp.to_convert = {"cookie": True, "my_cookie": str(type(req.http_cookie))}
    return 200, req, resp

cookie_route = R("/cookie") >> [(GET, A("Test cookies", set_cookie))]

papys.set_config(PConfig(post_convert_201=True))

# OAuth integration

with KcOidcAcfFactory() as oidc:
    oidc.server_host = "http://localhost:8000"
    oidc.callback_path = "/callback"
    oidc.login_path = "/login"
    oidc.logout_path = "/logout"
    oidc.auth_url = "https://your-keycloak-host.com/auth/realms/"
    oidc.client_id = "your-client-id"
    oidc.client_secret = "your-secret"
    oidc.realm = "your-realm"
    oidc.redirect_to_login = True
    oidc.app_redirect_url = "http://localhost:8000/protected"

oidc_guard = oidc.get_route_guard_hook()

auth_hook = UserInfoAuthorizationHook()
auth_hook.type = "allow"
auth_hook.POST_groups = { "/normal-users" }
auth_hook.add_user_sub_to_body = True

oidc_guard >> auth_hook

protected_route = R("/protected", oidc_guard) >> [
    (GET, JsonA("Protected ressource", {"access": "granted"}))
]

papys.add_route(protected_route)

# ---

user_route | doc_route
users_route | user_route

supplier_route | doc_route
suppliers_route | supplier_route

papys.add_route(users_route)
papys.add_route(suppliers_route)
papys.add_route(test_neg_route)
papys.add_route(cookie_route)


class InitializeHook(Hook):
    def __init__(self):
        super().__init__()
        self._message = "Just print this to the console for demo."

    def process_hook(
        self, req: Request, resp: Response
    ) -> papys.Tuple[bool, int, Request, Response]:
        print(self._message)
        # req.path = "/some-path" -> Only here (init hook) you can change the path.
        # return False, 200, req, resp -> Would cancel the process.
        return True, 200, req, resp


def finalize(req, resp: Response):
    print("And here is the finalize hook message.")
    # True or False doesn't matter here.
    # Only the status code and the response are relevant.
    # You can still change all the properties of the response here.
    # resp.reset_content() -> This could, for example, ensure that no content is sent to the client.
    return True, resp.status_code, req, resp


# Set hook via a own class:
papys.set_initialize_hook(InitializeHook())

# Set hook via a function:
papys.set_finalize_hook(FunctionHook(finalize))


def test_app(env, func):
    return papys.app(env, func)


# Important:
# Start the application like this for test purposes only.
# For productive use, use a WSGI server, which is recommended for productive use.
dev_server.run(test_app)
