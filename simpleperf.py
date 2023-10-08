import argparse
import sys
import ipaddress
import socket 
import time
from tabulate import tabulate
import threading


def main():

    #Portnumber and server ip
    server_port = args.port
    server_ip = str(args.bind)
    #Creating serversocket
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #Fixing an error with reusable socket
    serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    outputID=f"{args.serverip}:{args.port}"
    #Binding a socket to ip/port
    serverSocket.bind((server_ip, server_port))
    #Server listes to new connections
    serverSocket.listen(1)
    print("-----------------------------------------------------------")
    print("A simpleperf server is listening on port ", args.port)
    print("-----------------------------------------------------------")
    #Server will wait for new client to connect to the server and start a new thread for each, 
    #there will be one thread waiting at the first line, looking for new connections
    while True:
        connectionSocket, addr = serverSocket.accept()
        #Creating a new thread
        t = threading.Thread(target=handle_client, args =(connectionSocket, ))  
        t.daemon=True
        #Starting a thread -> Thread jumps to handle_client and prepares to send data
        t.start()
        #print("Active connections: ", threading.active_count()) 
        print(f" A simpleperf client with {addr[0]}:{addr[1]} is connected with {outputID}")
        print("Active threads server: ", threading.active_count())
    
    print("serverSocket closed")
    serverSocket.close()
    
#This function will recieve data from the client
def handle_client(connectionSocket):
    #<ServerIp>:<port>
    outputID=f"{args.serverip}:{args.port}"
    #Start timer
    startTime = time.time() 
    #Variable for recieved bytes from client
    recieved_bytes = 0
    #Recieve date until client sends a bye msg
    while (True):
        #Recieve bytes from client
        rec = connectionSocket.recv(1000)
        #Add the amount of bytes sent
        recieved_bytes += len(rec)
        #Will send a ack to the client and display data in a table
        if ("BYE" in rec.decode()):
            connectionSocket.send("ACK".encode())
            total_time = time.time()-startTime
            #Needs to convert to the type that the user wanted
            totalTransfer = int(convert_To_Type(recieved_bytes, args.format))
            #1 byte = 8 bit, 1 megabyte = 1_000_000 bytes 
            megaBitsPerSec = recieved_bytes*8/1000000
            #Printing into a table with python library tabulate
            totalOutputData = [[outputID, f"0-{round(total_time, 1)}", f"{totalTransfer} {args.format}", f"{round(megaBitsPerSec/total_time, 2)} Mbps"]]
            print(tabulate(totalOutputData, headers=["ID", "Interval", "Transfer", "Bandwidth"]))
            print("\n")
            break
    print("Connection closed")
    connectionSocket.close()

#This function will connect clients to the server and create a thread for each
def client():
    print("-----------------------------------------------------------")
    print("A simpleperf client connecting to server ", args.serverip)
    print("-----------------------------------------------------------")
    
    #Create amount of threads equal to input from user in args.parallel
    for i in range(args.parallel):
        #Save ip adress and port from arguments
        server_addr = str(args.serverip)
        server_port = args.port
        #Create socket
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #clientSocket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 0)
        #Connect socket to args.server ip and args.port
        clientSocket.connect((server_addr, server_port))
        #Create a new client thread
        t = threading.Thread(target=client_thread, args=(clientSocket, ))
        #Start a thread
        t.start()
        print('A simpleperf client with', args.serverip," is connected with port ", args.port)

#This function will send data until it is over the time limit or data limit set by the user
def client_thread(clientSocket):   
    print("Number of connections ", threading.active_count())
   #Sending 1000 bytes each time
    data = bytes(1000)   
    #If the user specifies byte limit, it will create a max limit
    totalTime = args.time
    #Boolean attribute which will be true, when over the time limit or byte limit
    sendBye = False

    #If the user specifies num it will create the max byte limit
    if(args.num):
        maxBytes = args.num
    #If the user specifies interval
    if (args.interval):
        #Time between interval
        interval = args.interval
        startInterval = 0
        endInterval = startInterval+interval
        #Variable to save bytes in the interval
        interval_bytes=0
    #Variable for total sent bytes to server
    sent_bytes = 0
    #For the output table
    outputData=[]
    #Saving server ip and port for ease of use inside the output table
    outputID=f"{args.serverip}:{args.port}"
    #Start time
    startTime = time.time()
    #This sends data until over timelimit or bytelimit
    while True:
        #Send 1000 bytes to server
        send = clientSocket.send(data)
        #Add number of bytes into sent_bytes
        sent_bytes+=send
        #Update time
        currTime = time.time()-startTime 
        if(args.interval):
            #When the time is over the endinterval
            if(currTime> endInterval):
                #The amount of bytes since the last interval
                interval_data = (sent_bytes-interval_bytes)
                #Amount of time since last interval
                interval_time = endInterval-startInterval
                #Change value to Mbs, 1 Megabit per second = 8/(1_000_000*total_time):
                megaBitsPerSec = interval_data*8/(interval_time*1000000)
                #Converting to correct type
                interval_Transfer = convert_To_Type(interval_data,args.format)
                #Adding to a table
                outputData.append([outputID, f"{startInterval}-{round(currTime, 1)}", f"{round(interval_Transfer, 0)} {args.format}", f"{round(megaBitsPerSec,2)} Mbps"])
                #Update variables
                startInterval=round(currTime, 0)
                endInterval+=interval
                interval_bytes=sent_bytes
        
        #If it is over the byte limit, we check this before time to be able to prioritize this over time if user writes --num
        if (args.num):
            if(sent_bytes > maxBytes):
                sendBye=True
        
        #If over time limit
        else:
            if (currTime> totalTime):
                sendBye=True
        #Send bye msg if over limit 
        if(sendBye==True):
            while True:
                #Send bye msg to stop the server
                byemsg = clientSocket.send("BYE".encode())
                #Wait for Ack from server
                ackMsg = clientSocket.recv(24)
                if('ACK' in ackMsg.decode()):
                    #When we recieve the ack we "stop" the time
                    endTime = time.time()-startTime
                    break
            #Update values            
            megaBitsPerSec = sent_bytes*8/1000000
            #Convert to correct type/amount
            total_Transfer = int(convert_To_Type(sent_bytes, args.format))
            
            if (args.interval):
                #Prints the interval values at the end if it was chosen by user
                print(tabulate(outputData, headers=["ID", "Interval", "Transfer", "Bandwidth"]))
            #Print the table with correct values
            print("-----------------------------------------------")
            totalOutputData=[[outputID, f"0-{round(endTime, 1)}", f"{int(total_Transfer)} {args.format}", f"{round(megaBitsPerSec/endTime, 2)} Mbps"]]
            print(tabulate(totalOutputData,headers=["ID", "Interval", "Transfer", "Bandwidth"]))
            print("\n")
            break
    #Closes the clientsocket        
    clientSocket.close()
    return

#Check if input is an integer
def validate_number(val):
    try:
        value = int(val)
        #Returns a valid integer
        return value
    except ValueError:
        print("Not a integer, try again")
        argparse.ArgumentTypeError('Input was not a integer')
#Check if integer is larger than 0    
def positive_int(val):
    value = validate_number(val)
    if (value > 0):
      #returns a number above 0
      return value
    else:
        print("Expected a positve integer")
        argparse.ArgumentTypeError("Input was a negative integer, expected a positve")
        quit()
 #Check if port is valid       
def validate_port(val):
    #Check if val is a integer
    try:
        value = validate_number(val)
    except:
        print("Value was not a integer, try again!")
        argparse.ArgumentTypeError("Not a integer")
    print(value)
    if (value<65535 and value>1024 ):
        #Returns a valid port between 1025 and 65534
        return value    
    else:
        print("Wrong port, please try again")
        quit()
#Check if ip adress is valid
def validate_serverip(val):
    try:
        #See if val= a valid ip adress
        value = ipaddress.ip_address(val)
    except ValueError:
        print("Wrong input in server ip, please input a valid ip adress")
        argparse.ArgumentTypeError("Something went wrong in the serverip")
        quit()
    return value
    
#Check if valid byte type and convert to bytes
def validate_num(val):
    #list = val.split()
    #fullList=['', '']
    num = ''
    byteType = ''
    #List of letters/numbers from the args.num input
    liste = list(val)
    #Variable to controll that the input is in the right order, numbers then letters
    order=False
    for var in liste:   
        if(var.isdigit()):
            num+=var
            #If order is true, then there have already been a non digit. Therefore if the list 
            #jumps into a digit again, there is a mistake in input: Example: 12M3B
            if(order == True):
                print("Error in -n input, please try again. Watch out for numbers first then type!")
                argparse.ArgumentTypeError("Wrong order in input")
                quit()
        else:
            byteType+=var
            order = True
    #Convert to bytes with amount and right type
    number = int(convert_To_Bytes(num, byteType))
    #Returns number of bytes, that will be the maxlimit before the client stops sending data
    return number

#Converts to bytes
def convert_To_Bytes(number, byteType):
    #Check if number is an integer    
    number = validate_number(number)
    #Check if valid type then convert to bytes. Returns number of bytes
    if(byteType == 'MB'):
        return number*1000000
    elif(byteType == 'KB'):
        number=number*1000
        return number
    elif(byteType == 'B'):
        return number
    else: 
        quit()

#Convert to right byte-type
def convert_To_Type(number, byteType):
    #Number = amount of a specific bytetype
    number=int(number)
    #Bytetype = MB/KB/B
    if(byteType=='MB'):
        return number/1000000
    if(byteType=='KB'):
        return number/1000
    if(byteType=='B'):
        return number
    else:
        quit()

#Creates parallell connections, number is amount of connections
def create_parallel(number):
    #Check if number is between 1 and 5   
    if(number>5 or number<1):
        print("Wrong input, must be between 1 and 5")
        quit()


parser = argparse.ArgumentParser(description="positional arguments")

#Server arguments
parser.add_argument('-s', '--server', action='store_true', help="Runs in server mode")
parser.add_argument('-b', '--bind', type=validate_serverip, default="127.0.0.1", help="Specify ip adress for server")

#Client arguments
parser.add_argument('-c', '--client', action='store_true', help="Runs in client mode")
parser.add_argument('-I', '--serverip', type=validate_serverip, default="127.0.0.1", help="Specify which server ip you wish to connect to")
parser.add_argument('-t', '--time', type=positive_int, default=25, help="How long do you wish to run the program")
parser.add_argument('-i', '--interval', type=positive_int, help="How often per x sec do you want to write out statistics")
parser.add_argument('-P', '--parallel', type=create_parallel, default=1, help="How many parallel connections?")
parser.add_argument('-n', '--num', type=validate_num, help="How much data do you wish to send?")

#Common arguments
parser.add_argument('-p', '--port', type=validate_port, default=8080, help="Which portnumber?")
parser.add_argument('-f', '--format', choices=('MB', 'KB', 'B'), default='MB', help="Specify format, either in MB, B or KB")

args = parser.parse_args() 

#Checking if server or client is selected, can`t have both
if (args.server and args.client) == True:
    print("You must either run in client mode or server mode, not both!")
    quit()
if (args.server == True):
        main()
if (args.client == True):   
            client()   
else:
    print("You must run in either client or server mode")
    quit()

def quit():
    print("Program terminated")
    sys.exit()

