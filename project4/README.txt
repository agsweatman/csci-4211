CSCI 4211
Project 4

huhnx025 - Jon Huhn
larse702 - Zachary Larsen

a) Code implementation and design details

We implemented our solution in Python with POX. We use a single Controller object to handle the installing rules and the ARP responder.

We have every switch forward every ARP request to the controller. This triggers PacketIn events on the controller. Since the installed rules take care of all other traffic, we know that only ARP requests will trigger PacketIn events at the controller. The controller has a hard-coded map of IP addresses to MAC addresses that it uses to construct ARP responses.

On startup, each switch installs its appropriate rules according to the static topology.

We implemented an event listener function which adds rules to each switch to redirect traffic away from broken links. This function listens for LinkEvent messages from the openflow.discovery module to detect link failures.

b) Any relevant details for running the project

Our implementation requires the openflow.discovery module to detect link failures, so to run our controller, move controller.py to ~/pox/pox/samples and run the following command to start the controller:

    ./pox.py log.level -DEBUG openflow.discovery samples.controller

The topology is run as prescribed in the writeup.

c) A detailed breakdown of individual contributions

ARP Responder - Jon
Helped build network map - Zach
Installing Rules - Jon
Helped with rule priorities - Zach
Link Failures - Jon
README - Jon/Zach
