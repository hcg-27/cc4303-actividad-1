import argparse
import json
import socket
import sys
from datetime import datetime as dt
from pathlib import Path

IP, PORT = 'localhost', 8000

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

def create_HTTP_message(http_struct: dict[str, bytes]) -> bytes:

    # Obtener start_line, body y headers
    start_line, body, *headers = http_struct.items()

    # Inicializar mensaje HTTP con la start line
    message = start_line[1] + b'\r\n'

    # Agregar headers
    for k, v in headers:
        message += (k.encode() + b': ' + v + b'\r\n')
    
    # Agregar body
    message += (b'\r\n' + body[1])

    return message 

def get_host(http_struct: dict[str, bytes]) -> bytes: ...

if __name__ == "__main__":

    # Inicializar y configurar cli parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str,
                        help="full path al JSON de configuración",
                        default="config/config.json")
    
    # Obtener filepath
    filepath = Path(vars(parser.parse_args())['config'])

    # Leer archivo de configuración
    try:
        with open(filepath, "r") as json_file:
            x_el_que_pregunta = bytes(
                json.load(json_file)["X-ElQuePregunta"], encoding="UTF-8"
            )
    except json.JSONDecodeError:
        print(f"Error: formato JSON invalido en {filepath}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: el archivo {filepath} no existe")
        sys.exit(1)

    # Inicializar socket del proxy
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Hacer que escuche en la dirección y puerto deseado
    proxy_socket.bind((IP, PORT))
    proxy_socket.listen(5)

    # Esperar petición de conexicón de algún cliente
    client_socket, _ = proxy_socket.accept()

    # Esperar GET del cliente
    request = client_socket.recv(8192)
    if b'GET' in parse_HTTP_message(request)["START_LINE"]:
        # Leer archivo HTML
        with open("index.html", "rb") as html_file:
            content = html_file.read()
            content_length = len(content)

        # Crear estructura para la respuesta HTTP
        response_struct = {
            "START_LINE": b'HTTP/1.1 200 OK',
            "BODY": content,
            "Server": b'Linux Mint/22.1',
            "Date": f'{dt.now().strftime("%a, %d %b %Y %H:%M:%S UTC-4")}'.encode(),
            "Content-Type": b'text/html; charset=utf-8',
            "Content-Length": f' {content_length}'.encode(),
            "Connection": b'keep-alive',
            "Acces_Control-Allow-Origin": b'*'
        }
        
        # Agregar header
        response_struct |= {'X-ElQuePregunta': x_el_que_pregunta}

        # Construir respuesta
        response = create_HTTP_message(response_struct)

        # Enviar respuesta
        client_socket.send(response)

        # Cerrar conexión
        client_socket.close()
