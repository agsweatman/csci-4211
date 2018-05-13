from pox.core import core
from pox.lib.util import dpid_to_str
from pox.lib.addresses import EthAddr, IPAddr
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.arp import arp
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt

log = core.getLogger()


class Controller (object):

    def __init__(self, connection):
        # Keep track of the connection to the switch so that we can
        # send it messages!
        self.connection = connection
        dpid = connection.dpid
        connections[dpid] = connection

        # This binds our PacketIn event listener
        connection.addListeners(self)

        # Push rule to send all ARP requests to the controller
        fm = of.ofp_flow_mod()
        fm.priority -= 0x1000  # lower than the default
        fm.match.dl_type = ethernet.ARP_TYPE
        fm.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
        self.connection.send(fm)

        # Leaf switches
        if dpid < 4:
            msg = of.ofp_flow_mod()
            msg.priority += 0x100
            msg.match.dl_dst = int_to_mac(dpid*2-1)
            msg.actions.append(of.ofp_action_output(port=3))
            self.connection.send(msg)

            msg = of.ofp_flow_mod()
            msg.priority += 0x100
            msg.match.dl_dst = int_to_mac(dpid*2)
            msg.actions.append(of.ofp_action_output(port=4))
            self.connection.send(msg)

            msg = of.ofp_flow_mod()
            msg.match.dl_src = int_to_mac(dpid*2-1)
            msg.actions.append(of.ofp_action_output(port=1))
            self.connection.send(msg)

            msg = of.ofp_flow_mod()
            msg.match.dl_src = int_to_mac(dpid*2)
            msg.actions.append(of.ofp_action_output(port=2))
            self.connection.send(msg)

        # Spine switches
        else:
            for i in range(1, 7):
                msg = of.ofp_flow_mod()
                msg.match.dl_dst = int_to_mac(i)
                msg.actions.append(of.ofp_action_output(port=(i+1)//2))
                self.connection.send(msg)

    def _handle_PacketIn(self, event):
        """
        Handles packet in messages from the switch.
        """

        packet = event.parsed  # This is the parsed packet data.
        if not packet.parsed:
            log.warning("Ignoring incomplete packet")
            return

        a = packet.find('arp')
        if not a:
            return

        if a.opcode == arp.REQUEST:
            r = arp()
            r.hwtype = a.hwtype
            r.prototype = a.prototype
            r.hwlen = a.hwlen
            r.protolen = a.protolen
            r.opcode = arp.REPLY
            r.hwdst = a.hwsrc
            r.protodst = a.protosrc
            r.protosrc = a.protodst
            r.hwsrc = arp_table[a.protodst]
            e = ethernet(type=packet.type, src=event.connection.eth_addr,
                         dst=a.hwsrc)
            e.payload = r
            log.info("%s answering ARP for %s" % (dpid_to_str(event.connection.dpid),
                                                  str(r.protosrc)))
            msg = of.ofp_packet_out()
            msg.data = e.pack()
            msg.actions.append(of.ofp_action_output(port=of.OFPP_IN_PORT))
            msg.in_port = event.port
            event.connection.send(msg)


def handle_fail(event):
    if event.removed:
        ldpid = event.link.dpid1
        sdpid = event.link.dpid2
        if ldpid > sdpid:
            ldpid, sdpid = sdpid, ldpid
        log.debug("Link failed between %d and %d" %
                  (ldpid, sdpid))

        if sdpid == 4:
            new_port = 2
            mac = 2 * ldpid - 1
            omac = 2 * ldpid
        else:
            new_port = 1
            mac = 2 * ldpid
            omac = 2 * ldpid - 1

        msg = of.ofp_flow_mod()
        msg.command = of.OFPFC_MODIFY
        msg.match.dl_src = int_to_mac(mac)
        msg.actions.append(of.ofp_action_output(port=new_port))
        connections[ldpid].send(msg)

        msg = of.ofp_flow_mod()
        msg.match.dl_dst = int_to_mac(mac)
        msg.actions.append(of.ofp_action_output(port=new_port))
        for i in range(1, 4):
            if i == ldpid:
                continue
            connections[i].send(msg)

        msg = of.ofp_flow_mod()
        msg.match.dl_dst = int_to_mac(omac)
        msg.actions.append(of.ofp_action_output(port=new_port))
        for i in range(1, 4):
            if i == ldpid:
                continue
            connections[i].send(msg)


def int_to_mac(i):
    return EthAddr("00:00:00:00:00:0%d" % (i,))


# dpid to connection
connections = {}

arp_table = {
    IPAddr('10.0.0.1'): EthAddr('00:00:00:00:00:01'),
    IPAddr('10.0.0.2'): EthAddr('00:00:00:00:00:02'),
    IPAddr('10.0.0.3'): EthAddr('00:00:00:00:00:03'),
    IPAddr('10.0.0.4'): EthAddr('00:00:00:00:00:04'),
    IPAddr('10.0.0.5'): EthAddr('00:00:00:00:00:05'),
    IPAddr('10.0.0.6'): EthAddr('00:00:00:00:00:06')
}


def launch():
    """
    Starts the component
    """
    def start_switch(event):
        core.openflow_discovery.addListenerByName("LinkEvent", handle_fail)
        log.debug("Controlling %s" % (event.connection,))
        Controller(event.connection)
    core.openflow.addListenerByName("ConnectionUp", start_switch)
