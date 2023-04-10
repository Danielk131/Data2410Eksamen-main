import argparse
import sys
import ipaddress
from socket import * 
import time
from tabulate import tabulate


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
    
def create_parallel():
    print("Laget parallel")

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
        return number
    if(byteType=='KB'):
        return number*1000
    if(byteType=='B'):
        return number*1000000
    else:
        quit()



#Vi er her!
def server():
    print('A simpleperf server is listening on port', args.port)
    server_port = args.port
    server_ip = args.bind
    outputID=f"{args.serverip}:{args.port}"

    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind((server_ip, server_port))
    serverSocket.listen(1)
    
    
    

    while True:
        try:
            connectionSocket, addr = serverSocket.accept()
            totalTime = int(connectionSocket.recv(1000).decode())
            print("Totaltid =", totalTime)
            connectionSocket.send("OK".encode())
            
            startTime = time.time() 
            currTime = time.time()-startTime
            print("STart tid = ", currTime)
            recieved_Megabytes = 0
            
            #Timebased 
            while (True):
                print("fær bye msg")
                rec = connectionSocket.recv(1000) 
                print("sender!")
                currTime=time.time()-startTime
                print(currTime)
                recieved_Megabytes+=0.001
                if ("BYE" in rec.decode()):
                    #byeMsg = connectionSocket.recv(24).decode()
                    print("Bye msg =", rec.decode())
                    connectionSocket.send("ACK".encode())
                    #print("Sender ack")
                    realTime = time.time()-startTime
                    print("Virkelig totaltid =", realTime)
                    print("TotalMB= ", recieved_Megabytes)
                    print("MegaBytes per sek = ", recieved_Megabytes/realTime)
                    totalTransfer = int(convert_To_Type(recieved_Megabytes, args.format))
                    totalOutputData = [[outputID, f"0-{round(currTime, 1)}", f"{totalTransfer} {args.format}", f"{round(recieved_Megabytes/realTime, 2)} Mbps"]]
                    print(tabulate(totalOutputData, headers=["ID", "Interval", "Transfer", "Bandwidth"]))
                    break

        except:
            print("Noe gikk galt")
            quit()


#def newConnection():



def client(timeTimer):
    print("Er i klient")
    print('A simpleperf client with', args.serverip," is connected with ", args.port)
    server_addr = str(args.serverip)
    server_port = args.port
    data = bytes(1000)
    print(timeTimer)


    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((server_addr, server_port))
    clientSocket.send(str(args.time).encode())
    clientSocket.recv(1000).decode()

    startTime = time.time()
    currTime = time.time() - startTime
    totalTime = args.time
    interval = args.interval
    maxBytes = args.num
    sendBye = False
    
    totalBytes=0
    intervalTimer = 0
    startInterval = 0
    endInterval = startInterval+interval
    sent_Megabytes = 0
    outputData=[]
    megaBytesTransfer=0
    print("-----------------------------------------------------------")
    print("A simpleperf client connecting to server ", args.serverip)
    print("-----------------------------------------------------------")
    outputID=f"{args.serverip}:{args.port}"
    print(maxBytes)

    while True:
        clientSocket.send(data)
        sent_Megabytes+=0.001
        totalBytes+=1000
        megaBytesTransfer+=0.001
        if(currTime > endInterval):
            bandwidth = megaBytesTransfer/interval
            megaBytesTransfer = convert_To_Type(megaBytesTransfer,args.format) 
            outputData.append([outputID, f"{startInterval}-{round(currTime, 1)}", f"{megaBytesTransfer} {args.format}", f"{round(bandwidth,2)} Mbps"])
            startInterval=round(currTime, 1)
            endInterval+=interval
            megaBytesTransfer=0

        #time based 
        if(timeTimer==True):        
            if (currTime > int(totalTime)):
                sendBye=True
        elif(timeTimer==False):
            if(totalBytes > maxBytes):
                sendBye=True
                print(sendBye)
        
        if(sendBye==True):     
            print(sendBye)   
            clientSocket.send("BYE".encode())
            ackMsg = clientSocket.recv(200).decode()
    
            if(ackMsg == "ACK"):
                #print("ACK =", ackMsg)
                realTime = time.time()-startTime
                total_Transfer = int(convert_To_Type(sent_Megabytes, args.format))
                print("Virkelig totaltid =", realTime)
                print(tabulate(outputData, headers=["ID", "Interval", "Transfer", "Bandwidth"]))
                print("-----------------------------------------------")
                print("Total values")
                totalOutputData=[[outputID, f"0-{round(currTime, 1)}", f"{int(total_Transfer)} {args.format}", f"{round(sent_Megabytes/realTime, 2)} Mbps"]]
                print(tabulate(totalOutputData,headers=["ID", "Interval", "Transfer", "Bandwidth"]))
                clientSocket.close()
                quit()      
        currTime = time.time()-startTime
        print(currTime)
        print(totalTime)
        

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
parser.add_argument('-i', '--interval', type=positive_int, default=1)
parser.add_argument('-P', '--parallel', type=create_parallel)
parser.add_argument('-n', '--num', type=validate_num)

args = parser.parse_args() 


if (args.server and args.client) == True:
    print("You must either run in client mode or server mode, not both!")
    quit()
if (args.server == True):
    server()
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
    

