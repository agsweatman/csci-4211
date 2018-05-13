 CSCI 4211 - Project 2
 Jon Huhn
 huhnx025

 I wrote my solution in Python 3, so no compilation is necessary.

 Both my client and server each have main functions that do setup and coordinate their higher-level operations. The details of the state machine described in the book are implemented in the client_send and server_recv functions. Each run an infinite loop that terminates when an acceptable packet is received. I also have a Packet class to encapsulate all of the packet-specific functions, like the layout and marshaling.

 My Packets are laid out as follows:
    - 40-byte checksum
    - 1-byte sequence number
    - 3-byte data size
    - 1-byte last flag
    - 467-byte data payload

I used this format because it maximizes the amount of data in each packet without dealing with raw binary, since the simulated network layer can't handle bytes arrays.

I found that increasing the probability of error increased the total transfer time. Increasing the network layer delay slowed down transfers even when no errors were present in the packets.

I handled errors the same way as the state machines described in the book do.
