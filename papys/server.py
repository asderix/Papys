from wsgiref.simple_server import make_server
import papys.core as core


def run(app=core.app, host="localhost", port=8000):
    """
    IMPORTANT!
    Please you this function just in case of testing. You a production ready WSGI server for running the application in production.

    Args:
        app (function): The WSGI compatible function. Default: core.app
        host (str): The host of the server. Default: 'localhost'.
        port (int): The port of the server. Default: 8000.
    """
    httpd = make_server(host, port, app)
    print(f"Server is running on: {host}:{port}")
    print(f"WARNING: Don't use in production environement!")
    print(f"Use a production ready WSGI server instead.")
    httpd.serve_forever()
