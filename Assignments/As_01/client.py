# Author: Richard Roy
from socket import socket, AF_INET, SOCK_STREAM
import re
# regex for correct pwd res
regex_check = r'^200'

# error handling
client_socket = None
try:
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 9000))
    while True:
        try:
            response = client_socket.recv(256)
            text = response.decode('utf-8')
            print (f'Server response {text}')
            if re.match(regex_check, text):
                break
            user_input = input ("> ")

            # Allocate an extensible array
            b = bytearray()
            b.extend(user_input.encode())
            client_socket.send(b)
        except ConnectionError as e:
            print(f"Connection error: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
finally:
    if client_socket:
        client_socket.close()
        print("Connection closed")
    
    