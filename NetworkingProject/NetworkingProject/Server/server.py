from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, socket
from threading import Thread
import os
import time
import pickle


def unicast_msg(msg):
    for k, v in clients.items():
        if int(v) == 1:
            k.send(msg.encode('utf8'))
            print('Sent with Unicast')


def send_big_file(client, file_name):
    print('Sending big file found on server.')
    print('sending warning first')
    warningData = (file_name, 'large.file.incoming')
    warningData = pickle.dumps(warningData)
    client.sendall(warningData)

    # then send big file
    server_file = open("Server/" + file_name, "rb")
    server_file_data = server_file.read()
    client.sendall(server_file_data)

    # Close the file opened at server side once copy is completed
    print('File has been sent successfully')
    server_file.close()
    print('file closed')


def search_and_send_small_file(client, file_name, thread_count):
    if os.path.exists("Server/" + file_name):  # checks if file exists on server
        print('Sending file found on server.')
        server_file = open("Server/" + file_name, "r")
        server_file_data = server_file.read()
        tokenData = (server_file_data, file_name)
        tokenData = pickle.dumps(tokenData)
        client.send(tokenData)

        # Close the file opened at server side once copy is completed
        print('File has been sent successfully')
        server_file.close()
        print('file closed')

    else:  # ask other clients to upload, if not return error message
        for k, v in clients.items():
            if int(v) != thread_count and k != client:
                SendData2 = (file_name, "upload.now")
                SendData2 = pickle.dumps(SendData2)
                k.send(SendData2)

        # go back and download once the data is sent, or error if it doesn't
        print('waiting for file to send')
        time.sleep(1)
        if os.path.exists("Server/" + file_name):  # checks if file exists on server
            print('Sending file from other client.')
            server_file = open("Server/" + file_name, "r")
            server_file_data = server_file.read()
            tokenData = (server_file_data, file_name)
            tokenData = pickle.dumps(tokenData)
            client.send(tokenData)

            # Close the file opened at server side once copy is completed
            print('File has been sent successfully')
            server_file.close()
            print('file closed')
        else:
            print('No file found.')
            error_msg = ('File not found!', 'read.now')
            error_msg = pickle.dumps(error_msg)
            client.send(error_msg)
            print('Sent Error Message')


def single_client(client, thread_count, to_be_deleted):
    welcome_msg = ('Connection Successful!', 'read.now')
    welcome_msg = pickle.dumps(welcome_msg)
    client.send(welcome_msg)
    clients[client] = thread_count

    while True:
        msg = client.recv(4096)
        receivedToken = pickle.loads(msg)
        receivedCommand = receivedToken[0]

        if receivedCommand == 'DOWNLOAD':  # Send a file to

            # if os.path.exists("Server/" + receivedToken[1]):  # checks if file exists on server
            if len(receivedToken) == 2:  # only 1 file to be sent
                if os.path.exists("Server/" + receivedToken[1]):
                    if os.stat("Server/" + receivedToken[1]).st_size > 4096:  # large file
                        send_big_file(client, "Server/" + receivedToken[1])
                    else:  # small file
                        search_and_send_small_file(client, receivedToken[1], thread_count)

            elif len(receivedToken) == 3:  # 2 files to be sent
                EXPERIMENT_MODE = False  # True: testing download speed, false for testing different scenarios
                if EXPERIMENT_MODE:
                    strategyOption = 'a'
                else:
                    print('Which Strategy?')
                    print('a: 2-1')
                    print('b: 2-2')
                    print('c: 2-3')
                    strategyOption = input('Enter an option: ')

                # Scenario 2-1
                if strategyOption == 'a':
                    count = 1
                    while count < len(receivedToken):
                        print('Looking for ' + receivedToken[count] + '...')  # The file it wants
                        search_and_send_small_file(client, receivedToken[count], thread_count)
                        count = count + 1

                # Scenario 2-2
                elif strategyOption == 'b':
                    count = 1
                    count2 = 0
                    while count < len(receivedToken) and count2 == 0:
                        print('Looking for ' + receivedToken[count] + '...')  # The file it wants
                        if os.path.exists("Server/" + receivedToken[count]):  # find other selected file
                            if count == 1:
                                count2 = 2
                            else:
                                count2 = 1
                        else:
                            count = count + 1

                    if count > 2:  # neither files were found on server
                        print('No file found.')
                        error_msg = ('File not found!', 'read.now')
                        error_msg = pickle.dumps(error_msg)
                        client.send(error_msg)
                        print('Sent Error Message')

                    # count2 is the client2 file, count1 is file on server.
                    elif not os.path.exists("Server/" + receivedToken[count2]):  # request file upload from other client
                        for k, v in clients.items():
                            if int(v) != ThreadCount and k != client:
                                SendData2 = (receivedToken[count2], "upload.now")
                                SendData2 = pickle.dumps(SendData2)
                                k.send(SendData2)

                        # go back and download once the data is sent, or error if it doesn't
                        print('waiting for file to send')
                        time.sleep(1)

                        if os.path.exists("Server/" + receivedToken[count2]):  # checks if file has been uploaded to server
                            print('Appending files')
                            client_file = open("Server/" + receivedToken[count2], "r")
                            client_file_data = client_file.read()
                            client_file.close()
                            print('file closed')
                            server_file = open("Server/" + receivedToken[count], "r")
                            server_file_data = server_file.read()
                            appended_data = server_file_data + "\n\n" + client_file_data
                            tokenData = (appended_data, "mergedFiles")
                            tokenData = pickle.dumps(tokenData)
                            client.send(tokenData)
                            # Close the file opened at server side once copy is completed
                            print('File has been sent successfully')

                        else:
                            print('No file found.')
                            error_msg = ('File not found!', 'read.now')
                            error_msg = pickle.dumps(error_msg)
                            client.send(error_msg)
                            print('Sent Error Message')

                # Scenario 2-3
                elif strategyOption == 'c':
                    count = 1
                    count2 = 0
                    while count < len(receivedToken) and count2 == 0:
                        print('Looking for ' + receivedToken[count] + '...')  # The file it wants
                        if os.path.exists("Server/" + receivedToken[count]):  # find other selected file
                            if count == 1:
                                count2 = 2
                            else:
                                count2 = 1
                        else:
                            count = count + 1

                    if count > 2:  # neither files were found on server
                        print('No file found.')
                        error_msg = ('File not found!', 'read.now')
                        error_msg = pickle.dumps(error_msg)
                        client.send(error_msg)
                        print('Sent Error Message')

                    # count2 is the client2 file, count1 is file on server.
                    elif not os.path.exists("Server/" + receivedToken[count2]):  # request file upload from other client
                        for k, v in clients.items():
                            if int(v) != ThreadCount and k != client:
                                SendData2 = (receivedToken[count2], "upload.now")
                                SendData2 = pickle.dumps(SendData2)
                                k.send(SendData2)

                        # go back and download once the data is sent, or error if it doesn't
                        print('waiting for file to send')
                        time.sleep(1)

                        if os.path.exists("Server/" + receivedToken[count2]):  # checks if file has been uploaded to server
                            client_file = open("Server/" + receivedToken[count2], "r")
                            client_file_data = client_file.read()
                            client_file.close()
                            print('client file read and closed')
                            tokenData = (client_file_data, receivedToken[count2])
                            tokenData = pickle.dumps(tokenData)
                            client.send(tokenData)
                            print('client file sent')

                            server_file = open("Server/" + receivedToken[count], "r")
                            server_file_data = server_file.read()
                            print('server file read and closed')
                            tokenData = (server_file_data, receivedToken[count])
                            tokenData = pickle.dumps(tokenData)
                            client.send(tokenData)
                            print('server file sent')

                        else:
                            print('No file found.')
                            error_msg = ('File not found!', 'read.now')
                            error_msg = pickle.dumps(error_msg)
                            client.send(error_msg)
                            print('Sent Error Message')

        # receivedCommand = receivedToken[0], which is the first index of the incoming message.
        elif receivedCommand == "UPLOAD":
            print('Received data from Client')
            write_file = open("Server/" + receivedToken[2], "w")  # opens file for writing/saving sent file
            write_file.write(receivedToken[1])  # writes/saves file received
            print("File written.")
            if receivedToken[3] == "server_request":
                to_be_deleted.append("Server/" + receivedToken[2])
            write_file.close()
            print("File saved and closed.")

        elif receivedCommand == "ACK":
            print("received acknowledgement message")
            for file in to_be_deleted:
                if os.path.exists(file):
                    os.remove(file)
                    print("Removed downloaded file.")

        else:
            print('hmm idk king how did we get here')


def incoming_connections(to_be_deleted):  # Handles each Client
    while True:
        client, addr = s.accept()
        print(f'A client has connected {addr}')
        thread_count = int(addr[1])
        Thread(target=single_client, args=(client, thread_count, to_be_deleted)).start()


if __name__ == "__main__":
    toBeDeleted = []  # array of file names that will be deleted after temporary use
    ThreadCount = 0  # placeholder for incrementing amount of client threads

    # Setting Up Client Threads
    clients = {}

    # Creating Server
    host = '127.0.0.1'  # local is 127.0.0.1
    port = 2004
    s = socket(AF_INET, SOCK_STREAM)
    s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    s.bind((host, port))
    print('Server is set up!')
    print('Socket is listening..')
    s.listen(5)

    ACCEPT_THREAD = Thread(target=incoming_connections(toBeDeleted))
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    s.close()
