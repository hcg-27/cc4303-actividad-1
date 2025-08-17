from proxy.proxy import parse_HTTP_message

class TestParseHTTP:
    request_msg = b"""GET / HTTP/1.1\r
Host: www.example.com\r
Content-Type: text/html; charset=UTF-8\r
User-Agent: Mosaic/1.0\r
Cookie: PHPSESSID=298zf09hf012fh2; csrftoke=u32t4o3tb3gg43; _gat=1\r
\r
"""

    response_msg = b"""HTTP/1.1 200 OK\r
Date: Mon, 23 May 2005 22:38:34 GMT\r
Content-Type: text/html; charset=UTF-8\r
Content-Length: 155\r
Last-modified: Wed, 08 Jan 2003 23:11:55 GMT\r
Server: Apache/1.3.3.7 (Unix) (Red-Hat/Linux)\r
Etag: 3f80f-1b6-3e1cb03b\r
Accept-Range: bytes\r
Connection: Close\r
\r
<html>
    <head>
        <title>An Example</title>
    </head>
    <body>
        <p>Hello World, this is a very simple HTML document.</p>
    </body>
</html>
"""

    request_struct = {
        "START_LINE": b"GET / HTTP/1.1",
        "HEADERS": {
            b"Host": b" www.example.com",
            b"Content-Type": b" text/html; charset=UTF-8",
            b"User-Agent": b" Mosaic/1.0",
            b"Cookie": b" PHPSESSID=298zf09hf012fh2; csrftoke=u32t4o3tb3gg43; _gat=1"
        },
        "BODY": b""
    }

    response_struct = {
        "START_LINE": b"HTTP/1.1 200 OK",
        "HEADERS": {
            b"Date": b" Mon, 23 May 2005 22:38:34 GMT",
            b"Content-Type": b" text/html; charset=UTF-8",
            b"Content-Length": b" 155",
            b"Last-modified": b" Wed, 08 Jan 2003 23:11:55 GMT",
            b"Server": b" Apache/1.3.3.7 (Unix) (Red-Hat/Linux)",
            b"Etag": b" 3f80f-1b6-3e1cb03b",
            b"Accept-Range": b" bytes",
            b"Connection": b" Close"
        },
        "BODY": b"""<html>
    <head>
        <title>An Example</title>
    </head>
    <body>
        <p>Hello World, this is a very simple HTML document.</p>
    </body>
</html>
"""
    }

    def test_parse_HTTP_request(self):
        assert parse_HTTP_message(self.request_msg) == self.request_struct

    def test_parse_HTTP_response(self):
        assert parse_HTTP_message(self.response_msg) == self.response_struct