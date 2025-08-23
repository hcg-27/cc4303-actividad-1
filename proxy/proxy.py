import argparse
import json
import socket
import sys
from urllib.parse import urlparse
from datetime import datetime as dt
from pathlib import Path
from typing import TypedDict

IP, PORT = 'localhost', 8000
Config = TypedDict('Config', {
    'X-ElQuePregunta': str,
    'blocked': set[str],
    'forbidden_words': dict[str, str]
})

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

def get_host(http_struct: dict[str, bytes]) -> bytes:
    try:
        return http_struct['Host']
    except KeyError:
        print("Error: Header host no esta presente en la petición")
        sys.exit(1)

def get_path(http_struct: dict[str, bytes]) -> bytes:
    try:
        url = http_struct['START_LINE'].split(b" ")[1] 
        return urlparse(url.decode()).path.encode()
    except KeyError:
        print("Error: mensaje HTTP mal formado, no posee start line")
        sys.exit(1)

def is_forbidden(request: bytes, blocked: set[str]) -> bool:

    # Procesar petición
    request_struct = parse_HTTP_message(request)

    # Construir URI
    host = get_host(request_struct).decode()
    path = get_path(request_struct).decode()
    uri = f"{host}{path}"
    
    return uri in blocked

def parse_json(filepath: Path) -> Config:
    # Cargar json en memoria
    try:
        with open(filepath) as file:
            json_file = json.load(file)
    except json.JSONDecodeError:
        print("Error: formato JSON invalido en {filepath}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: el archivo {filepath} no existe")
        sys.exit(1)

    # Transformar json_file['forbidden_words'] de una lista de diccionarios
    # a un diccionario
    forbidden_words = {}
    for dictionary in json_file['forbidden_words']:
        for k, v in dictionary.items():
            forbidden_words[k] = v

    return {
        'X-ElQuePregunta': json_file['X-ElQuePregunta'],
        'blocked': {
            site for site in json_file['blocked']
        },
        'forbidden_words': forbidden_words
    }

def censor_content(content: bytes, to_replace: dict[str, str]) -> bytes:
    # Reemplazar las palabras
    for k, v in to_replace.items():
        content = content.replace(k.encode(), v.encode())
    
    return content

def receive_http_message(socket: socket.socket, buff_size: int) -> bytes:
    message = b''

    # Recibir todos los headers
    while b'\r\n\r\n' not in message:
        message += socket.recv(buff_size)

    # Procesar headers
    headers = parse_HTTP_message(message)

    # Recibir body de ser necesario
    if 'Content-Length' in headers.keys():
        content_length = int(headers['Content-Length'])
        received = len(headers['BODY'])
        while received < content_length:
            body = socket.recv(buff_size)
            message += body
            received += len(body)

    return message 

if __name__ == "__main__":

    # Inicializar y configurar cli parser
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", type=str,
                        help="full path al JSON de configuración",
                        default="config/config.json")
    
    # Obtener filepath
    filepath = Path(vars(parser.parse_args())['config'])

    # Leer archivo de configuración
    config_file = parse_json(filepath)

    # Inicializar socket del proxy
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Hacer que escuche en la dirección y puerto deseado
    proxy_socket.bind((IP, PORT))
    proxy_socket.listen(5)

    # Esperar petición de conexión de algún cliente
    client_socket, _ = proxy_socket.accept()

    # Esperar request del cliente
    request_message = receive_http_message(client_socket, 50)

    # Verificar que la dirección no este prohibida
    if is_forbidden(request_message, config_file['blocked']):
        # Cargar html en memoria 
        with open(Path("403.html"), 'rb') as file:
            error_html = file.read()

        # Construir response
        response_struct = {
            'START_LINE': b'HTTP/1.1 403 Forbidden',
            'BODY': error_html,
            'Server': b'Linux Mint/22.1',
            'Date': dt.now().strftime("%a, %d %b %Y %H:%M:%S UTC-4").encode(),
            'Content-Type': b'text/html; charset=utf-8',
            'Content-Length': f"{len(error_html)}".encode(),
            'Access-Control-Allow-Origin': b'*'
        }
        
        # Enviar Response
        client_socket.send(create_HTTP_message(response_struct))

        # Cerrar conexión
        client_socket.close()
    else:
        # Procesar request del cliente
        request_struct = parse_HTTP_message(request_message)

        # Agregar Header X-ElQuePregunta
        x_el_que_pregunta = config_file['X-ElQuePregunta'].encode()
        request_struct |= {'X-ElQuePregunta': x_el_que_pregunta}

        # Obtener dirección del servidor al que va dirigida la petición
        server_host = get_host(request_struct).decode()

        # Pedir conexión al servidor
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((server_host, 80))

        # Enviar request del cliente al servidor
        server_socket.send(create_HTTP_message(request_struct))

        # Esperar respuesta del servidor
        response_message = receive_http_message(server_socket, 50)

        # Procesar respuesta
        response_struct = parse_HTTP_message(response_message)

        # Censurar las palabras que sean necesarias
        response_struct['BODY'] = censor_content(
            response_struct['BODY'], config_file['forbidden_words']
        )
        
        # Ajustar content-length
        content_length = len(response_struct['BODY'])
        response_struct['Content-Length'] = f"{content_length}".encode()

        # Enviar respuesta del servidor al cliente
        client_socket.send(create_HTTP_message(response_struct))

        # Cerrar sockets
        server_socket.close()
        client_socket.close()
    
    # Cerrar socket del proxy
    proxy_socket.close()

    #if b'GET' in parse_HTTP_message(request)["START_LINE"]:
    #    # Leer archivo HTML
    #    with open("index.html", "rb") as html_file:
    #        content = html_file.read()
    #        content_length = len(content)

    #    # Crear estructura para la respuesta HTTP
    #    response_struct = {
    #        "START_LINE": b'HTTP/1.1 200 OK',
    #        "BODY": content,
    #        "Server": b'Linux Mint/22.1',
    #        "Date": f'{dt.now().strftime("%a, %d %b %Y %H:%M:%S UTC-4")}'.encode(),
    #        "Content-Type": b'text/html; charset=utf-8',
    #        "Content-Length": f' {content_length}'.encode(),
    #        "Connection": b'keep-alive',
    #        "Acces_Control-Allow-Origin": b'*'
    #    }
        
    #    # Agregar header
    #    response_struct |= {'X-ElQuePregunta': x_el_que_pregunta}

    #    # Construir respuesta
    #    response = create_HTTP_message(response_struct)

    #    # Enviar respuesta
    #    client_socket.send(response)

    #    # Cerrar conexión
    #    client_socket.close()
