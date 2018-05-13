# Spring 2018 CSci4211: Introduction to Computer Networks
# This program serves as the server of DNS query.
# Written in Python v3.

import sys
import threading
import os
import random
import re
from socket import *


def main():
    port = 5001  # Port number.

    try:
        # create a socket object, SOCK_STREAM for TCP
        sSock = socket(AF_INET, SOCK_STREAM)
        # bind socket to the current address on port 5001
        sSock.bind(('', port))
    except error as msg:
        print("cannot open socket:", msg)
        sys.exit(1)

    # Listen on the given socket maximum number of connections queued is 20
    sSock.listen(20)

    monitor = threading.Thread(target=monitorQuit, args=[])
    monitor.start()

    print("Server is listening...")

    while True:
        # blocked until a remote machine connects to the local port 5001
        connectionSock, addr = sSock.accept()
        server = threading.Thread(target=dnsQuery, args=[
                                  connectionSock, addr[0]])
        server.start()


def dnsQuery(connectionSock, srcAddress):
    # Get the client request
    url = connectionSock.recv(1024).decode()

    # Check that client's request is a hostname
    if re.match("[\w\d-]+\.([\w\d-]+\.?)+", url) is None:
        connectionSock.send("Invalid format".encode())
        connectionSock.close()
        return

    # Create the cache file if it doens't exist
    cache = "DNS_Mapping.txt"
    if not os.path.isfile(cache):
        mode = "w+"
    else:
        mode = "r+"
    try:
        f = open(cache, mode)

        # Keep track of if we've found the hostname in the file yet
        found = False
        for line in f:
            # Get each field of the line in a list, minus the newline at the end
            fields = line[:-1].split(':')

            # If the client's request matches the first field
            if url == fields[0]:
                # Found in the cache
                found = True
                source = "Local DNS"

                # call dnsSelection with a list of the IPs in the cache for the host
                ip = dnsSelection(fields[1:])
                break
        if not found:
            # Client's request wasn't in the cache
            try:
                # Query Root DNS
                ip = gethostbyname(url)
            except gaierror as e:
                # Root DNS failed
                ip = "Host not found"
            source = "Root DNS"
            # Write the DNS record to the cache
            # Don't have to handle writing a second IP to the same host since
            # the first would be returned if that host was ever queried
            f.write("{}:{}\n".format(url, ip))

        response = "{}:{}:{}".format(source, url, ip)
        print(response)
        # Send our response back to the client
        connectionSock.send(response.encode())
    finally:
        # Make sure we close the cache file and the client socket
        f.close()
        connectionSock.close()


def dnsSelection(ipList):
    # return a random element from the list
    return random.choice(ipList)


def monitorQuit():
    while 1:
        sentence = input()
        if sentence == "exit":
            os.kill(os.getpid(), 9)


main()
