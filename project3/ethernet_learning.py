"""
This is based on the OpenFlow Tutorial found at:
https://github.com/mininet/openflow-tutorial/wiki/Create-a-Learning-Switch

It acts as a simple hub, but can be modified to act like an L2
learning switch.

It's roughly similar to the one Brandon Heller did for NOX.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()


class EthernetLearning (object):
    """
    A EthernetLearning object is created for each switch that connects.
    A Connection object for that switch is passed to the __init__ function.
    """

    def __init__(self, connection):
        # Keep track of the connection to the switch so that we can
        # send it messages!
        self.connection = connection

        # This binds our PacketIn event listener
        connection.addListeners(self)

        # Use this table to keep track of which ethernet address is on
        # which switch port (keys are MACs, values are ports).
        self.mac_to_port = {}

    def _handle_PacketIn(self, event):
        """
        Handles packet in messages from the switch.
        """

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        packet_in = event.ofp  # The actual ofp_packet_in message.

        # Learn the port for the source MAC
        self.mac_to_port[packet.src] = packet_in.in_port

        if packet.dst in self.mac_to_port:
            port = self.mac_to_port[packet.dst]

            log.debug("Installing flow for {}.{} -> {}.{}".format(packet.src,
                                                                  packet_in.in_port, packet.dst, port))

            msg = of.ofp_flow_mod()

            # Set fields to match received packet
            msg.match = of.ofp_match.from_packet(packet, packet_in.in_port)
            msg.idle_timeout = 10
            msg.hard_timeout = 30
            msg.actions.append(of.ofp_action_output(port=port))
            msg.data = packet_in
            self.connection.send(msg)

        else:
            # Flood the packet out everything but the input port
            log.debug("Port for {} unknown -- flooding".format(packet.src))
            msg = of.ofp_packet_out()
            msg.data = packet_in

            # Add an action to send to the specified port
            action = of.ofp_action_output(port=of.OFPP_ALL)
            msg.actions.append(action)

            # Send message to switch
            self.connection.send(msg)


def launch():
    """
    Starts the component
    """
    def start_switch(event):
        log.debug("Controlling %s" % (event.connection,))
        EthernetLearning(event.connection)
    core.openflow.addListenerByName("ConnectionUp", start_switch)
