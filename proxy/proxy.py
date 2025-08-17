def parse_HTTP_message(http_message: bytes) -> dict[str, bytes | dict]:
    """Parse an HTTP message into a 3-key dictionary.
    
    The returned dictionary has the following keys: 'START_LINE', 'HEADERS' and
    'BODY', they hold bytes, dict and bytes respectively. 
    
    Note that the dictionary follows the typical structure of an HTTP message.
    """

    # Separar mensaje en head y body
    head, body = http_message.split(b'\r\n\r\n')

    # Separar la start-line de el resto de headers
    start_line, *headers = head.split(b'\r\n')

    # Crear la estructura de datos
    http_struct = {
        "START_LINE": start_line,
        "HEADERS": {
            k: v for k, v in [
                header.split(b':', maxsplit=1) for header in headers
            ]
        },
        "BODY": body
    }

    return http_struct