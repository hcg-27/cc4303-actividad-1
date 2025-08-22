from proxy.proxy import (
    parse_HTTP_message,
    create_HTTP_message,
    get_host,
    get_path,
    is_forbidden
)

class TestParseCreateHTTP:
    response_html = """<html>
    <head>
        <title>An Example</title>
    </head>
    <body>
        <p>Hello World, this is a very simple HTML document.</p>
    </body>
</html>
"""

    request_msg = b"""GET / HTTP/1.1\r
Host: www.example.com\r
Content-Type: text/html; charset=UTF-8\r
User-Agent: Mosaic/1.0\r
Cookie: PHPSESSID=298zf09hf012fh2; csrftoke=u32t4o3tb3gg43; _gat=1\r
\r
"""

    response_msg = f"""HTTP/1.1 200 OK\r
Date: Mon, 23 May 2005 22:38:34 GMT\r
Content-Type: text/html; charset=UTF-8\r
Content-Length: 155\r
Last-modified: Wed, 08 Jan 2003 23:11:55 GMT\r
Server: Apache/1.3.3.7 (Unix) (Red-Hat/Linux)\r
Etag: 3f80f-1b6-3e1cb03b\r
Accept-Range: bytes\r
Connection: Close\r
\r
{response_html}""".encode()

    request_struct = {
        "START_LINE": b"GET / HTTP/1.1",
        "BODY": b"",
        "Host": b"www.example.com",
        "Content-Type": b"text/html; charset=UTF-8",
        "User-Agent": b"Mosaic/1.0",
        "Cookie": b"PHPSESSID=298zf09hf012fh2; csrftoke=u32t4o3tb3gg43; _gat=1"
    }

    response_struct = {
        "START_LINE": b"HTTP/1.1 200 OK",
        "BODY": f"{response_html}".encode(),
        "Date": b"Mon, 23 May 2005 22:38:34 GMT",
        "Content-Type": b"text/html; charset=UTF-8",
        "Content-Length": b"155",
        "Last-modified": b"Wed, 08 Jan 2003 23:11:55 GMT",
        "Server": b"Apache/1.3.3.7 (Unix) (Red-Hat/Linux)",
        "Etag": b"3f80f-1b6-3e1cb03b",
        "Accept-Range": b"bytes",
        "Connection": b"Close"
    }

    def test_parse_HTTP_request(self):
        assert parse_HTTP_message(self.request_msg) == self.request_struct

    def test_parse_HTTP_response(self):
        assert parse_HTTP_message(self.response_msg) == self.response_struct

    def test_create_HTTP_request(self):
        assert create_HTTP_message(self.request_struct) == self.request_msg

    def test_create_HTTP_response(self):
        assert create_HTTP_message(self.response_struct) == self.response_msg

class TestGetElementsFromURI:
    host = b"cc4303.bachmann.cl"
    
    request_struct_1 = {
        "START_LINE": b"GET / HTTP/1.1",
        "BODY": b"",
        "Host": host,
        "User-Agent": b"curl/8.5.0",
        "Accept": b"*/*"
    }

    request_struct_2 = {
        "START_LINE": b"GET /replace HTTP/1.1",
        "BODY": b"",
        "Host": host,
        "User-Agent": b"curl/8.5.0",
        "Accept": b"*/*"
    }

    def test_get_URI(self):
        assert get_host(self.request_struct_1) == self.host
        assert get_host(self.request_struct_2) == self.host
    
    def test_get_path(self):
        assert get_path(self.request_struct_1) == b"/"
        assert get_path(self.request_struct_2) == b"/replace"

class TestBlockForbiddenURI:
    blocked = {
        "cc4303.bachmann.cl/secret"
    }

    request_message = b"""GET /secret HTTP/1.1\r
Host: cc4303.bachmann.cl\r
User-Agent: curl/8.5.0\r
Accept: */*\r
\r
"""
    def test_is_forbidden(self):
        assert is_forbidden(self.request_message, self.blocked) == True

