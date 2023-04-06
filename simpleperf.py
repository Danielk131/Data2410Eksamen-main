import argparse
import sys
import ipaddress
from socket import * 
import time
def validate_number(val):
    try:
        value = int(val)
    except ValueError:
        argparse.ArgumentTypeError('Input was a string, but expected to be an integer')
    return value

def positive_int(val):
    value = validate_number(val)
    if (value > 0):
      return value
    else:
        print("Expected a positve integer")
        argparse.ArgumentTypeError("Input was a negative integer, expected a positve")
        quit()
        
def validate_port(val):
    value = validate_number(val)
    print(value)
    if (value<65535 and value>1024 ):
          print("Port " + val + " er ok")
    else:
        print("Feil port", val)
        quit()
    return value

def validate_ip(val):
    print('Bind ip =', val)
    return val

def validate_serverip(val):
    try:
        value = ipaddress.ip_address(val)
        print(value) 
    except ValueError:
        argparse.ArgumentTypeError("Something went wrong in the serverio")
        quit()
    return value
    
def create_parallel():
    print("Laget parallel")

def validate_num(val):
    #list = val.split()
    print(val)
    fullList=['', '']
    num = ''
    size = ''
    liste = list(val)
    print(liste)
    for var in liste:
        if(var.isdigit()):
            num+=var
        else:
            size+=var
    
    positive_int(num)
    # Sjekk om du kan gjøre om til byte før du sender den videre
    if(size == 'MB' or size == 'KB' or size =='B'):
        fullList[0]=num
        fullList[1]=size
        print(fullList)
        return fullList
    else: 
        quit()




#Vi er her!
def server():
    print('A simpleperf server is listening on port', args.port)
    server_port = args.port
    server_ip = args.bind
    print(server_ip)

    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((server_ip, server_port))
    serverSocket.listen(1)

    totalTime = args.time
    print(totalTime)
   

    while True:
        try:
            print("try")
            connectionSocket, addr = serverSocket.accept()
            print("etter try")
            totalTime = 25
            
            startTime = time.time() 
            currTime = time.time()-startTime
            print(currTime)
            while (currTime < totalTime):
                send = connectionSocket.send("wohooo".encode()) 
                print("sender!")
        except:
            print("Noe gikk galt")
            quit()


#def newConnection():



def client():
    print("Er i klient")
    print('A simpleperf client with', args.serverip," is connected with ", args.port)
    server_addr = str(args.serverip)
    server_port = args.port

    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((server_addr, server_port))
    clientSocket.send(str(args.time).encode())


    startTime = time.time()
    currTime = time.time() - startTime
    totalTime = args.time
    while True:
        recieve = clientSocket.recv(1000)
        if (currTime > totalTime):
            print("Ferdig med å sende")
            clientSocket.send("BYE".encode())
            quit()
        currTime = time.time()-startTime
        print(currTime)

parser = argparse.ArgumentParser(description="positional arguments")

parser.add_argument('-s', '--server', action='store_true')
parser.add_argument('-p', '--port', type=validate_port, default=8080)
parser.add_argument('-b', '--bind', type=validate_ip, default="127.0.0.1")
parser.add_argument('-f', '--format', choices=('MB', 'KB', 'B'), default='MB')

parser.add_argument('-c', '--client', action='store_true')
parser.add_argument('-I', '--serverip', type=validate_serverip, default="127.0.0.1")
parser.add_argument('-t', '--time', type=positive_int, default=25)
parser.add_argument('-i', '--interval', type=positive_int, default=1)
parser.add_argument('-P', '--parallel', type=create_parallel)
parser.add_argument('-n', '--num', action='append', type=validate_num, default=[100, 'MB'])

args = parser.parse_args() 


if (args.server and args.client) == True:
    print("You must either run in client mode or server mode, not both!")
    quit()
if (args.server == True):
    print("Du er i server")
    server()
if (args.client == True):
        print("Du er i klienten")
        client()
else:
    print("You must run in either client or server mode")
    quit()

def quit():
    sys.exit()
    print("Connection closed!")

