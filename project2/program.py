import hashlib
import os
import random
import select
import socket
import sys

VERBOSE = True


class Packet:
    # Packet layout parameters
    # 40-byte checksum
    # 1-byte sequence number
    # 3-byte data size
    # 1-byte last flag
    # 467-byte data payload
    PACKET_SIZE = 512
    SZ_CHECKSUM = 40
    SZ_SEQ_NUM = 1
    SZ_DATA_SIZE = 3
    SZ_LAST = 1
    SZ_DATA = PACKET_SIZE - SZ_CHECKSUM - SZ_SEQ_NUM - SZ_DATA_SIZE - SZ_LAST

    POS_CHECKSUM = 0
    POS_SEQ_NUM = POS_CHECKSUM+SZ_CHECKSUM
    POS_DATA_SIZE = POS_SEQ_NUM+SZ_SEQ_NUM
    POS_LAST = POS_DATA_SIZE+SZ_DATA_SIZE
    POS_DATA = POS_LAST+SZ_LAST

    SEQ_NUMS = 2

    def __init__(self, seq_num, last, data, checksum=''):
        self.seq_num = seq_num
        self.data_size = len(data)
        self.last = last
        self.data = data

        if checksum:
            self.checksum = checksum
        else:
            hashed_str = str(
                self.seq_num)+str(self.data_size).zfill(Packet.SZ_DATA_SIZE)+str(int(self.last))+self.data
            hashed_str += ' ' * (Packet.PACKET_SIZE-len(hashed_str))
            self.checksum = hashlib.sha1(hashed_str.encode()).hexdigest()

    def send(self, sock):
        '''Send the packet through the socket'''
        sock.send(str(self).encode())

    def inc_seq_num(self):
        '''Cycle the packet's sequence number'''
        self.seq_num = next_seq_num(self.seq_num)

    def __str__(self):
        packet = self.checksum + \
            str(self.seq_num)+str(self.data_size).zfill(Packet.SZ_DATA_SIZE) + \
            str(int(self.last))+self.data
        packet += ' '*(Packet.PACKET_SIZE-len(packet))
        return packet

    def is_valid(self):
        '''Validate the packet's checksum'''
        packet = Packet(self.seq_num, self.last, self.data)
        return packet.checksum == self.checksum

    @classmethod
    def from_string(cls, string):
        '''Create a Packet from a string'''
        checksum = string[cls.POS_CHECKSUM:cls.POS_CHECKSUM+cls.SZ_CHECKSUM]
        seq_num = int(string[cls.POS_SEQ_NUM:cls.POS_SEQ_NUM+cls.SZ_SEQ_NUM])
        data_size = int(
            string[cls.POS_DATA_SIZE:cls.POS_DATA_SIZE+cls.SZ_DATA_SIZE])
        last = bool(int(string[cls.POS_LAST:cls.POS_LAST+cls.SZ_LAST]))
        data = string[cls.POS_DATA:cls.POS_DATA+data_size]
        packet = cls(seq_num, last, data, checksum)
        return packet


def main():
    c = len(sys.argv)
    if c == 4:
        client_main()
    elif c == 3:
        server_main()
    else:
        print(':(')
        sys.exit(1)


def client_main():
    host = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]
    print('Transferring {}...'.format(filename))

    cSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cSock.connect((host, port))

    file_size = os.path.getsize(filename)

    cur_seq_num = 0  # Initial sequence number

    # Send the filename to the server
    filename_packet = Packet(cur_seq_num, False, filename)
    client_send(cSock, filename_packet)

    # Send the file data
    with open(filename, 'r') as f:
        while True:
            cur_seq_num = next_seq_num(cur_seq_num)

            # Make the packet
            data = f.read(Packet.SZ_DATA)
            if not data:
                break

            seq_num = cur_seq_num
            last = f.tell() == file_size
            packet = Packet(seq_num, last, data)

            if client_send(cSock, packet):
                # Got ACK for last packet.
                break

    print('Done!')


def client_send(sock, packet, timeout=0.5):
    # Keep trying until we get an acceptable ACK
    while True:
        packet.send(sock)

        # Set up timeout
        ready = select.select([sock], [], [], timeout)

        if ready[0]:
            ack = sock.recv(Packet.PACKET_SIZE).decode()

            ok = True  # Packet is not corrupt
            right_seq_num = True  # Packet has the  sequence number we're looking for
            try:
                # Make a Packet from the socket data
                ack = Packet.from_string(ack)
            except ValueError:
                # Can't parse string. Must be corrupt
                ok = False
            else:
                # Check checksum
                ok = ack.is_valid()

                # Check sequence number
                right_seq_num = ack.seq_num == packet.seq_num

            if not ok:
                if VERBOSE:
                    print('ACK is corrupt. Retransmitting...')
            elif not right_seq_num:
                if VERBOSE:
                    print('Received wrong ACK sequence number. Retransmitting...')
            else:
                # This packet is OK. Return to send the next one.
                return ack.last
        elif VERBOSE:
            print('Timeout! Retransmitting...')


def server_main():
    port = 5001
    print('Running the server on port', port)

    # Set up socket
    cx = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cx.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    cx.bind(('', port))
    cx.listen(20)

    while True:
        try:
            sSock, _ = cx.accept()
        except KeyboardInterrupt:
            print('\b\bShutting down server')
            cx.close()
            break

        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        expected_seq_num = 0  # Initial sequence number

        # Listen for the filename first
        output_filename = server_recv(sSock, expected_seq_num, filename_cb)
        output_filename = os.path.join(
            output_dir, os.path.basename(output_filename))
        print('Reading into', output_filename)

        f = open(output_filename, 'w+')

        while True:
            # Cycle sequence number
            expected_seq_num = next_seq_num(expected_seq_num)

            if server_recv(sSock, expected_seq_num, filedata_cb, [f]):
                # The packet we just got was the last one
                break

        # Clean up open file and sockets
        f.close()
        sSock.close()

        print('Done!')


def server_recv(sock, expected_seq_num, cb, cb_args=[]):
    # Keep listening until we get an acceptable packet
    while True:
        result = sock.recv(Packet.PACKET_SIZE).decode()

        ok = True  # Packet is not corrupt
        ack_seq_num = expected_seq_num  # Packet has the expected sequence number
        try:
            packet = Packet.from_string(result)
            if not packet.is_valid():
                raise ValueError
        except ValueError:
            # Packet is corrupt
            ok = False

            # Send a different sequence number than what we expected
            ack_seq_num = next_seq_num(expected_seq_num)

            if VERBOSE:
                print('Packet {} is corrupt, sending back ACK {}'.format(
                    expected_seq_num, ack_seq_num))
        else:
            if packet.seq_num != expected_seq_num:
                ok = False
                ack_seq_num = packet.seq_num
                if VERBOSE:
                    print('Received num {}, expected {}'.format(
                        packet.seq_num, expected_seq_num))

        # Send an ACK
        ack_data = 'ACK'
        ack = Packet(ack_seq_num, False, ack_data)
        ack.send(sock)

        if ok:
            # We got what we needed. Listen for the next packet.
            break

    # Call a callback function with the OK packet
    return cb(packet, *cb_args)


def filename_cb(packet):
    return packet.data


def filedata_cb(packet, f):
    f.write(packet.data)
    return packet.last


def next_seq_num(n):
    return (n+1) % Packet.SEQ_NUMS


main()
