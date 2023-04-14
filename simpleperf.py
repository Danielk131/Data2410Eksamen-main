import argparse
import sys
import ipaddress
from socket import * 
import socket 
import time
from tabulate import tabulate
import threading
import _thread as thread


def main():
    print("Main")
    print("Inne i thread")

    server_port = args.port
    server_ip = args.bind
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #serverSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    

    outputID=f"{args.serverip}:{args.port}"
    print("ETter attributter")
    
    serverSocket.bind((server_ip, server_port))
   
    serverSocket.listen(5)
    print("-----------------------------------------------------------")
    print("A simpleperf server is listening on port ", args.port)
    print("-----------------------------------------------------------")
    while True:
        i=0
        for number in range(args.parallel):
            print("Acitve connections: ", threading.active_count())
            connectionSocket, addr = serverSocket.accept()
            t= threading.Thread(target=handle_client, args =(connectionSocket, ))  
            t.start()
            print("Tråd nr, ", threading.active_count()) 
    serverSocket.close()
    print("Serversocket closed")

def handle_client(connectionSocket):
    #connectionSocket.setblocking(0)
    outputID=f"{args.serverip}:{args.port}"
    print("Inne i handle client")
    startTime = time.time() 
    recieved_bytes = 0
    #Timebased 
    while (True):
        rec = connectionSocket.recv(1000)
        recieved_bytes+= len(rec)
        
        if ("BYE" in rec.decode()):
            print("Tid når vi får bye", time.time()-startTime)
            connectionSocket.send("ACK".encode())
            print("Sender ack", time.time()-startTime)
            realTime = time.time()-startTime
            print("Virkelig totaltid =", realTime)
            print("TotalMB= ", recieved_bytes)
            totalTransfer = int(convert_To_Type(recieved_bytes, args.format))
            megaBitsPerSec = recieved_bytes*8/1000000
            totalOutputData = [[outputID, f"0-{round(realTime, 1)}", f"{totalTransfer} {args.format}", f"{round(megaBitsPerSec/realTime, 2)} Mbps"]]
            print("TOtal output ok")
            print(tabulate(totalOutputData, headers=["ID", "Interval", "Transfer", "Bandwidth"]))
            print("Tabell ok")
            break
        rec=''
    connectionSocket.close()
    print("Etter conn close")  

def client(timeTimer):
    print("-----------------------------------------------------------")
    print("A simpleperf client connecting to server ", args.serverip)
    print("-----------------------------------------------------------")
    
    for i in range(args.parallel):
        print(i)
        server_addr = str(args.serverip)
        server_port = args.port
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #clientSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 0)
        clientSocket.connect((server_addr, server_port))

        t = threading.Thread(target=client_thread, args=(clientSocket, ))
        t.start()
        print("CLient tråd nr ", threading.active_count())
        print('A simpleperf client with', args.serverip," is connected with ", args.port)

def client_thread(clientSocket):   
    
    data = bytes(1000)   
    totalTime = args.time
    if(args.num):
        maxBytes = args.num
    sendBye = False
    if (args.interval):
        interval = args.interval
        intervalTimer = 0
        startInterval = 0
        endInterval = startInterval+interval

    totalBytes=0
    interval_bytes=0
    sent_bytes = 0
    outputData=[]
    outputID=f"{args.serverip}:{args.port}"

    startTime = time.time()
    while True:
        print(time.time()-startTime, "Tid før send")
        send = clientSocket.send(data)
        sent_bytes+=send
        interval_bytes+=send
        currTime = time.time()-startTime 
        print(currTime)
        if(args.interval):
            print(currTime)
            if(currTime> endInterval):
                print("Endinterval: ", endInterval)
                megaBitsPerSec = interval_bytes*8/(interval*1000000)
                interval_Transfer = convert_To_Type(interval_bytes,args.format)
                outputData.append([outputID, f"{startInterval}-{round(currTime, 1)}", f"{round(interval_Transfer, 0)} {args.format}", f"{round(megaBitsPerSec,2)} Mbps"])
                startInterval=round(currTime, 0)
                endInterval+=interval
                interval_bytes=0

        #time based 
        if(timeTimer==True):
            print(time.time()-startTime, "Tid fær if setning")        
            if (currTime> totalTime):
                print("I if setning over tiden")
                sendBye=True
        else:
            if(totalBytes > maxBytes):
                sendBye=True
                print(sendBye)
        
        if(sendBye==True):
            while True:
                byemsg = clientSocket.send("BYE".encode())
                print("Tid etter send bye", time.time()-startTime)   
                ackMsg = clientSocket.recv(100)
                if('ACK' in ackMsg.decode()):
                    print("Tid etter motatt ack", time.time()-startTime)
                    break
                    
    
                #if('ACK' in ackMsg.decode()):
                    #print("ACK =", ackMsg)
            endTime = time.time()-startTime
            print("Endtime ", endTime)
            total_Transfer = int(convert_To_Type(sent_bytes, args.format))
            megaBitsPerSec = total_Transfer*8
            print("Real =", endTime)
            if (args.interval):
                print(tabulate(outputData, headers=["ID", "Interval", "Transfer", "Bandwidth"]))
            print("-----------------------------------------------")
            print("Total values for thread ", threading.active_count())
            totalOutputData=[[outputID, f"0-{round(endTime, 1)}", f"{int(total_Transfer)} {args.format}", f"{round(megaBitsPerSec/endTime, 2)} Mbps"]]
            print(tabulate(totalOutputData,headers=["ID", "Interval", "Transfer", "Bandwidth"]))
            break
    clientSocket.close()
    print("Clientsocket closed")
    return

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
        argparse.ArgumentTypeError("Something went wrong in the serverip")
        quit()
    return value
    

def validate_num(val):
    #list = val.split()
    print(val)
    #fullList=['', '']
    num = ''
    byteType = ''
    liste = list(val)
    print(liste)
    for var in liste:
        if(var.isdigit()):
            num+=var
        else:
            byteType+=var
    number = int(convert_To_Bytes(num, byteType))
    return number

def convert_To_Bytes(number, byteType):    
    number = validate_number(number)
    if(byteType == 'MB'):
        return number*1000000
    elif(byteType == 'KB'):
        number=number*1000
        return number
    elif(byteType == 'B'):
        return number
    else: 
        quit()

def convert_To_Type(number, byteType):
    number=int(number)
    if(byteType=='MB'):
        return number/1000000
    if(byteType=='KB'):
        return number/1000
    if(byteType=='B'):
        return number
    else:
        quit()

def create_parallel(number):
    positive_int(number)


print("Er i parser")
parser = argparse.ArgumentParser(description="positional arguments")

#Server arguments
parser.add_argument('-s', '--server', action='store_true')
parser.add_argument('-p', '--port', type=validate_port, default=8080)
parser.add_argument('-b', '--bind', type=validate_ip, default="127.0.0.1")
parser.add_argument('-f', '--format', choices=('MB', 'KB', 'B'), default='MB')

#Client arguments
parser.add_argument('-c', '--client', action='store_true')
parser.add_argument('-I', '--serverip', type=validate_serverip, default="127.0.0.1")
parser.add_argument('-t', '--time', type=positive_int, default=25)
parser.add_argument('-i', '--interval', type=positive_int)
parser.add_argument('-P', '--parallel', type=positive_int, default=1)
parser.add_argument('-n', '--num', type=validate_num)

args = parser.parse_args() 


if (args.server and args.client) == True:
    print("You must either run in client mode or server mode, not both!")
    quit()
if (args.server == True):
        main()
if (args.client == True):
        timeTimer=True
        if(args.num):
            timeTimer=False
            print("Num er aktivert")
            client(timeTimer)
        else:
            client(timeTimer)
else:
    print("You must run in either client or server mode")
    quit()

def quit():
    print("Connection closed!")
    sys.exit()

