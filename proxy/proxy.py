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
    http_struct: dict[str, bytes | dict] = {
        "START_LINE": start_line,
        "HEADERS": {
            k: v for k, v in [
                header.split(b':', maxsplit=1) for header in headers
            ]
        },
        "BODY": body
    }

    return http_struct

def create_HTTP_message(http_struct: dict[str, bytes | dict]) -> bytes:

    # Inicializar mensaje HTTP con la start line
    assert isinstance(http_struct["START_LINE"], bytes)
    message = http_struct["START_LINE"] + b'\r\n'

    # Agregar headers
    assert isinstance(http_struct["HEADERS"], dict)
    for k, v in http_struct["HEADERS"].items():
        assert isinstance(k, bytes) and isinstance(v, bytes)
        message += (k + b':' + v + b'\r\n')
    
    # Agregar body
    assert isinstance(http_struct["BODY"], bytes)
    message += (b'\r\n' + http_struct["BODY"])

    return message 
