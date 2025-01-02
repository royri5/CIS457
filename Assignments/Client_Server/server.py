# Author: Richard Roy
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from time import sleep
from random import randint
import re

regex_checks = r'^\d{6}\s\w' # 6 digit number followed by a space and a "word"
# posesses enough tokens (6 digits and a word, min 7 characters)

def client_connection(connectionSocket, addr):
    try:
        #server responds with a 6 digit numeric seed in the range 100000-400000
        seed = randint(100000, 400000)
        connectionSocket.send(str(seed).encode())

        while True:
            try:
                passwd = connectionSocket.recv(1024).decode()
                if not passwd:
                    print(f"Connection lost with {addr}")
                    break

                print(f"Received password: {passwd}")

                #code handling here/
                code = re.search(r'^\d{6}', passwd)
                code_present = re.match(r'\d{1}', passwd)
                #retcode 401
                if len(passwd) < 7:
                    print("Invalid input: Not enough tokens")
                    connectionSocket.send((str(401)+" Not enough tokens").encode())
                    continue
                #code has valid length
                elif code != None:
                    num_code = int(code.group())
                    #retcode 402
                    if num_code < seed:
                        print("Invalid input: Numeric code less than seed")
                        connectionSocket.send((str(402)+" Numeric code less than seed").encode())
                        continue
                #code has invalid length
                else:
                    #retcode 403
                    if code_present == None:
                        print("Invalid input: Missing numeric code")
                        connectionSocket.send((str(403)+" Missing numeric code").encode())
                        continue
                    #retcode 404 (at least 1 digit, but less than 6)
                    else:
                        print("Invalid input: Numeric code is too short")
                        connectionSocket.send((str(404)+" Numeric code is too short").encode())
                        continue
                # valid format
                # password checks
                # sum of individual digits in numeric code is even
                code_sum = sum(int(digit) for digit in code.group())
                if code_sum % 2 != 0:
                    print("Incorrect password: Sum of digits is not even")
                    connectionSocket.send((str(405)+" Sum of digits is not even").encode())
                    continue
                else:
                    #shave off the numeric code from the password
                    remaining_string = passwd.replace(code.group(), '', 1)
                    #remove whitespace
                    words = re.sub(r'\s+', '', remaining_string)
                    if len(words) % 2 != 0:
                        print("Incorrect password: Number of characters is not even")
                        connectionSocket.send((str(405)+" Number of characters is not even").encode())
                        continue
                #retcode 200 (correct password)
                print("Password is correct")
                connectionSocket.send((str(200)+" Password Accepted").encode())
                print("Connection closed, ", addr)
                connectionSocket.close()
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                break
    finally:
        connectionSocket.close()
        print(f"Connection with {addr} closed.")

# Main server code
welcomeSocket = socket(AF_INET, SOCK_STREAM)
try:
    welcomeSocket.bind(("", 9000))
    welcomeSocket.listen(4)    # Max backlog 4 connections
    print ('Server is listening on port 9000')

    while True:
        try:
            connectionSocket, addr = welcomeSocket.accept()
            print ("Accept a new connection", addr)
            client_thread = Thread(target=client_connection, args=(connectionSocket, addr))
            client_thread.start()
            #look for user input to close server, wait until clients are done and cleanup
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    #welcomeSocket.close()
    #print("End of server")
finally:
    welcomeSocket.close()
    print("Server closed")