from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import pickle
import os
import time


def upload_file(file_name, who_request):
    if os.path.exists(file_name):
        file = open(file_name, "r")
        file_text = file.read()
        tokens = ("UPLOAD", file_text, file_name, who_request)
        tokenToSend = pickle.dumps(tokens)
        s.send(tokenToSend)
        print("Uploaded File\n")
        file.close()
    else:
        print("dog I don't have that file")


def get_request(is_connected):
    print("-------------------------------------------------------------------------------------------")
    print('Welcome Client! Enter an Option:')
    if not is_connected:
        print('CONNECT [host address] [server port] to connect to server: host is 127.0.0.1, port is 2004')
    else:
        print('Connected to server.')
    print('UPLOAD fileName')
    print('DOWNLOAD fileName')
    print('DELETE fileName')
    print('DIR')
    print("-------------------------------------------------------------------------------------------")
    tokens = input("Input Command with arguments: ").split(" ")
    command = str(tokens[0])
    if len(tokens) > 3:
        print("only one command and two arguments max please!")
        return 0
    else:
        if command == "CONNECT":
            if is_connected:
                print("You're already connected, silly.")
                input("Click 'Enter' to continue.")
                return 0
            else:
                return tokens
        elif command == "UPLOAD":
            if is_connected:
                upload_file(tokens[1], "client_request")
                input("Click 'Enter' to continue.")
                return 0
            else:
                print("Please connect to a server first.")
                input("Click 'Enter' to continue.")
                return 0
        elif command == "DOWNLOAD":
            if is_connected:
                return tokens
            else:
                print("Please connect to a server first.")
                input("Click 'Enter' to continue.")
                return 0
        elif command == "DELETE":  # complete
            if os.path.exists(tokens[1]):
                os.remove(tokens[1])
                print("deleted file " + tokens[1])
            else:
                print("file does not exist")
            input("Click 'Enter' to continue.")
            return 0
        elif command == "DIR":
            path = os.getcwd()
            file_list = os.listdir(path)
            for file in file_list:
                path = os.getcwd() + "\\" + file
                stat = os.stat(file)
                print("file name: " + file)  # returns name
                print("file size: " + str(stat.st_size) + " bytes")  # returns size
                print("file upload date/time: " + time.ctime(os.path.getctime(path)))
            print("number of downloads: " + str(downloadCount))
            input("Click 'Enter' to continue.")
            return 0
        else:
            print('Wrong option, try again')
            input("Click 'Enter' to continue.")
            return 0

def recv_timeout(the_socket,timeout=2):
    the_socket.setblocking(0)
    total_data = []
    data= ''
    begin = time.time()
    while 1:
        #if you got some data, then break after wait sec
        if total_data and time.time() - begin > timeout:
            break
        #if you got no data at all, wait a little longer
        elif time.time() - begin > timeout*2:
            break
        try:
            data = the_socket.recv(8192)
            if data:
                total_data.append(data)
                begin = time.time()
            else:
                time.sleep(0.1)
        except:
            pass
    return ''.join(total_data)

def receive_msg():
    large_file_name = ''
    while True:
        try:
            if large_file_name == '':  # smol stuff
                msg = s.recv(4096)
                msg = pickle.loads(msg)

                if msg[1] == 'read.now':  # welcome/error message
                    print(msg[0])
                elif msg[1] == 'upload.now':
                    upload_file(msg[0], "server_request")
                elif msg[1] == 'large.file.incoming':
                    large_file_name = msg[0]

                else:  # will be a duple with {file, file_name}
                    if large_file_name == '':  # smol file
                        write_file = open(msg[1], "w")  # opens file for writing/saving sent file
                        write_file.write(msg[0])  # writes/saves file received
                        write_file.close()
                        print('Saved and closed new file.')
                        end_time = time.time()
                        time_lapsed = end_time - start_time
                        print("Time to receieve file since request: " + str(time_lapsed) + " seconds.")
                    ack_message = pickle.dumps(("ACK", msg[1]))
                    s.send(ack_message)  # sends acknowledgement
                    print("Sent acknowledgement message")
            else:  # large file
                large_file = recv_timeout(s)
                print('finished getting large file')
                tempFile = open(large_file_name, 'wb')
                tempFile.write(large_file)
                tempFile.close()
                print('Saved and closed new file.')
                end_time = time.time()
                time_lapsed = end_time - start_time
                print("Time to receieve file since request: " + str(time_lapsed) + " seconds.")
                large_file_name = ''
                ack_message = pickle.dumps(("ACK", msg[1]))
                s.send(ack_message)  # sends acknowledgement
                print("Sent acknowledgement message")

        except OSError as error:
            return error


# start of code
s = socket(AF_INET, SOCK_STREAM)
downloadCount = 0

# local host = '127.0.0.1'
EXPERIMENT_MODE = False  # True for ease of running experiments, false for testing different scenarios
if EXPERIMENT_MODE:
    firstConnect = True
    host = '127.0.0.1'  # 127.0.0.1 for local
    port = 2004
else:
    firstConnect = False
    tokenData = get_request(firstConnect)
    while tokenData == 0:
        tokenData = get_request(firstConnect)
    # after setting up socket and
    if tokenData[0] == "CONNECT":  # Connect to server
        host = str(tokenData[1])
        port = int(tokenData[2])


s.connect_ex((host, port))
print('Waiting for connection response...')
receive_thread = Thread(target=receive_msg)
firstConnect = True
receive_thread.start()

escapeKey = ''
while escapeKey != 'quit':
    # send the file that you want
    tokenData = get_request(firstConnect)
    while tokenData == 0:
        tokenData = get_request(firstConnect)
    if tokenData[0] == "DOWNLOAD":
        start_time = time.time()
        downloadCount = downloadCount + 1
    tokenData = pickle.dumps(tokenData)
    s.send(tokenData)
    print('sent data!')
    escapeKey = input("Waiting... (enter 'quit' to quit early)\n")
s.close()
# confirmation ^
