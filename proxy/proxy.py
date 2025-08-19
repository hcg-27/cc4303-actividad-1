def parse_HTTP_message(http_message: bytes) -> dict[str, bytes]:
    """Parse an HTTP message into a dictionary.
    
    The returned dict always contains the following keys: 'START_LINE' and
    'BODY'. It also contains a variable number of keys, each representing a
    header of the original message.
    """

    # Separar mensaje en head y body
    head, body = http_message.split(b'\r\n\r\n')

    # Separar la start-line de el resto de headers
    start_line, *headers = head.split(b'\r\n')

    # Crear la estructura de datos y añadir start line y body
    http_struct = {
        "START_LINE": start_line,
        "BODY": body,
        **{k.decode(): v for k, v in [
            header.split(b': ', maxsplit=1) for header in headers
        ]}
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
