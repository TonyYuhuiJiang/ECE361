#
# Copyright 2020 University of Toronto
#
# Permission is hereby granted, to use this software and associated
# documentation files (the "Software") in course work at the University
# of Toronto, or for personal use. Other uses are prohibited, in
# particular the distribution of the Software either publicly or to third
# parties.
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_2
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types, arp, ipv4, icmp
from ryu.lib import mac
import ipaddress, json
import os, sys
from switch_router import SwitchRouter


LAB_PATH = "/home/ubuntu/lab5/"
CONFIG_DIR = "configs/"
IP_CONFIG_FILE = LAB_PATH + CONFIG_DIR + "IP_CONFIG"
CONFIG_FILE = LAB_PATH + CONFIG_DIR +"CONFIG"
VLAN_CONFIG_FILE = LAB_PATH + CONFIG_DIR + "VLAN_CONFIG"
ROUTING_CONFIG_FILE = LAB_PATH + CONFIG_DIR + "ROUTING"


class MyController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_2.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MyController, self).__init__(*args, **kwargs)
        VLAN_config_content = self.get_config_file_content(VLAN_CONFIG_FILE)
        ROUTING_config_content = self.get_config_file_content(ROUTING_CONFIG_FILE)
        self.vlan_enalbed = False
        self.l3_enabled = False
        self.initialize_config(CONFIG_FILE)
        ip_to_mac_content = \
        '''{
        "10.0.1.11" : "00:00:00:00:00:01",
        "10.0.1.12" : "00:00:00:00:00:02",
        "10.0.1.13" : "00:00:00:00:00:03",
        "10.0.1.14" : "00:00:00:00:00:04",
        "10.0.2.11" : "00:00:00:00:00:05",
        "10.0.2.12" : "00:00:00:00:00:06",
        "10.0.2.13" : "00:00:00:00:00:07",
        "10.0.3.11" : "00:00:00:00:00:08",
        "10.0.3.12" : "00:00:00:00:00:09",
        "10.0.3.13" : "00:00:00:00:00:10"
        }'''
        self.switchRouter = SwitchRouter(VLAN_config_content, ROUTING_config_content, ip_to_mac_content)
        self.mac_to_port = {}  # Forwarding table for the switches
        self.intfName_to_mac = {}  # { 's3-eth1' : [1, MAC_addr] }
        self.routers_dpid = []  # DPID of the router
        self.router_intf_IPs = {}  # { 's5' : { ['s5-eth1', '10.0.1.1'] } }
        self.map_intf_to_IP(IP_CONFIG_FILE)
        self.hostsIP_to_switch_port = {}  # { '10.0.1.11' : [ dpid, 1] }

    def get_config_file_content(self, file_path):
        with open(file_path, "r") as f:
            return f.read()

    def get_vlan_of_incoming_packet(self, src_dpid, src_port_no):
        vlans = []
        for vlan_name, ports in self.switchRouter.vlan_to_port[src_dpid].items():
            if src_port_no in ports:
                vlans.append(vlan_name)
        return vlans

    def initialize_config(self, file_path):
        try:
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                if data['VLAN'] == "enable":
                    self.vlan_enalbed = True
                if data['L3'] == "enable":
                    self.l3_enabled = True
        except:
            self.logger.error("Cannot open the CONFIG file. Please let the TAs know.")
            sys.exit(1)

    # Read the IP_CONFIG file and populates the router_intf_IPs dictionary
    def map_intf_to_IP(self, file_path):
        # router_intf_IPs{ 's5' : { ['s5-eth1', '10.0.1.1'] } }
        try:
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                for router in data['router']:
                    self.router_intf_IPs.setdefault(router, {})
                    for intfName, intfIP in data['router'][router]:
                        self.router_intf_IPs[router][intfName] = intfIP
                        if self.l3_enabled:
                            # self.router_intf_IPs
                            self.logger.info("Router[%s][%s] = %s detected.", router, intfName, intfIP)
        except:
            self.logger.error("Cannot open the IP_CONFIG file. Please let the TAs know.")
            sys.exit(1)

    def get_router_ip_by_intfName(self, intfName):
        for router in self.router_intf_IPs:
            if intfName in self.router_intf_IPs[router]:
                return self.router_intf_IPs[router][intfName] # IP

    # set_ev_cls is used to declare an event handler in Ryu.
    # This decorator takes two arguments,
    #   1. The event which invokes the event handler
    #   2. The state of the switch
    #
    # We call this function when there is an OpenFlow Switch Function event.
    # Look here fore more information:
    # set_ev_cls:
    # https://ryu.readthedocs.io/en/latest/ryu_app_api.html#ryu-controller-handler-set-ev-cls
    #
    # Parameters:
    #   CONFIG_DISPATHCHER:
    #       Means the switch is a state which the version is
    #       negotiated and the features-request message has been sent.
    #
    #   EventOFPSwitchFeatures:
    #       The controller sends a feature request to the switch upon session establishment.
    #       https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPSwitchFeatures
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):

        # Datapath class describes an OpenFlow switch connected to this controller.
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        msg = ev.msg

        # Add router names from ROUTING file
        router_names = []
        for names, data in self.switchRouter.routing_table.items():
            router_names.append(names)

        for entry_id, data in msg.ports.items():
            portName = data.name.decode("utf-8").strip()
            portNo = data.port_no
            hwAddr = data.hw_addr
            self.intfName_to_mac[portName] = [portNo, hwAddr]
            # Is this an interface?
            if "eth" in portName:
                # Is this a router?
                if portName.split('-')[0] in router_names:
                    # Has this added previously?
                    if datapath.id not in self.routers_dpid:
                        self.routers_dpid.append(datapath.id)

                    # Add this router ip_addr/mac to the ip_to_mac list.
                    self.switchRouter.ip_to_mac[self.get_router_ip_by_intfName(portName)] = hwAddr

                self.switchRouter.set_bridgeName_to_dpid(portName.split('-')[0], datapath.id)
                self.logger.info("Bridge Registration [%s, dpid: %s]: [%s] = [%s, %s]",
                                 portName.split('-')[0], datapath.id, portName, portNo, hwAddr)
            if self.vlan_enalbed and not self.l3_enabled:
                    self.switchRouter.initialize_vlan_to_port(portName.split('-')[0])

        # install table-miss flow entry, whenever a frame comes to the switch, it has to ask
        # controller how to handle the frame. The default behavior in OF 1.3 is drop the frame.
        # Thus, we add an entry to forward every incoming frame to the controller.
        #
        # Match every incoming frame to be sent to the controller for further instructions.
        # Look here for more information:
        # parser.OFPMatch():
        # https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#flow-match-structure
        match = parser.OFPMatch()

        # parser.OFPActionOutput:
        # https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPActionOutput
        # Parameters:
        #   ofproto.OFPP_CONTROLLER: send to the controller
        #   ofproto.OFPCML_NO_BUFFER: indicates that no buffering should be applied and
        #                             the whole packet is to be sent to the controller.
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        # Save this flow rule in the switch packet forwarding table and the switch performs the same
        # action when the match is True (in this case always)
        self.add_flow(datapath, 0, match, actions)


    # Send a flow rule to the switch
    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        # datapath: datapath of the switch.
        # priority: When there multiple flow rules in the packet forwarding table,
        #           rules with higher priority will be matched. Rules with the same
        #           priority will be matched sequentially.
        # match: OFPMatch() instance
        # action: OFPActionOutput instance
        # buffer_id: Indicates whether the switch has buffered the incoming packet and
        #            has sent only the header or the complete packet including its payload
        #            has been sent to the controller.

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Action for the switch to handle the frame
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]

        # parser.OFPFlowMod: Modify Flow entry message
        # https://ryu.readthedocs.io/en/latest/ofproto_v1_3_ref.html#ryu.ofproto.ofproto_v1_3_parser.OFPFlowMod
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def send_packet(self, datapath, out_port, pkt):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt.serialize()
        # Notice that for the in_port, we use the special OFPP_CONTROLLER since we don't
        # technically have an inbound port.
        data = pkt.data
        actions = [parser.OFPActionOutput(out_port)]
        out = parser.OFPPacketOut(datapath=datapath,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER,
                                  actions=actions,
                                  data=data)
        datapath.send_msg(out)

    def router_handle_arp(self, msg):
        datapath = msg.datapath
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_arp = pkt.get_protocols(arp.arp)[0]
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        # self.logger.info("[%s]: arp_src: %s, arp_dst: %s", datapath.id, pkt_arp.src_mac, pkt_arp.dst_mac)

        router_intf_mac = self.switchRouter.get_mac_by_ip(pkt_arp.dst_ip)
        # self.logger.info("[%s], self.get_router_mac_by_ip(%s) = %s", datapath.id, pkt_arp.dst_ip, router_intf_mac)
        if router_intf_mac is None:
            # self.logger.info("Destination of ARP was not router's interfaces. Discard the frame.")
            # Destination of ARP was not router's interfaces, thus it is broadcast.
            # Prevent the router to handle broadcast ARP
            return

        # The ARP is for one of router's interfaces
        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=ether_types.ETH_TYPE_ARP,
                                           dst=eth.src,
                                           src=router_intf_mac))
        pkt.add_protocol(arp.arp(opcode=arp.ARP_REPLY, src_mac=router_intf_mac,
                                 src_ip=pkt_arp.dst_ip, dst_mac=eth.src,
                                 dst_ip=pkt_arp.src_ip))

        # self.logger.info("ARP Reply src_mac: %s, src_ip: %s, dst_mac: %s, dst_ip: %s",
        #                  router_intf_mac, pkt_arp.dst_ip, eth.src, pkt_arp.src_ip)
        out_port = msg.match['in_port']
        self.send_packet(datapath, out_port, pkt)

    def router_handle_icmp(self, msg):
        datapath = msg.datapath
        self.logger.info("[dpid: %s]: A ping request was received!", datapath.id)

        # We have to decode the packet and look into src and dst of the frame
        pkt = packet.Packet(msg.data)
        pkt_ethernet = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_icmp = pkt.get_protocol(icmp.icmp)
        in_port = msg.match['in_port']

        # Check if this ICMP is destined for the one of the router's interfaces
        # { 's5' : { {'s5-eth1' : '10.0.1.1'} }}
        for router in self.router_intf_IPs:
            for intfName, intfIP in self.router_intf_IPs[router].items():
                if pkt_ipv4.dst == intfIP:
                    router_intf_mac = self.switchRouter.get_mac_by_ip(pkt_ipv4.dst)

                    # Send echo reply
                    pkt = packet.Packet()
                    pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                                       dst=pkt_ethernet.src,
                                                       src=router_intf_mac))
                    pkt.add_protocol(ipv4.ipv4(dst=pkt_ipv4.src,
                                               src=pkt_ipv4.dst,
                                               proto=pkt_ipv4.proto))
                    pkt.add_protocol(icmp.icmp(type_=icmp.ICMP_ECHO_REPLY,
                                               code=icmp.ICMP_ECHO_REPLY_CODE,
                                               csum=0,
                                               data=pkt_icmp.data))
                    self.logger.info("ICMP Replay [src_mac: %s, src_ip: %s, dst_mac: %s, dst_ip: %s]",
                                     router_intf_mac, pkt_ipv4.dst,
                                     pkt_ipv4.src, pkt_ethernet.src)

                    out_port = in_port
                    self.send_packet(datapath, out_port, pkt)
                    return


        self.logger.info("[dpid: %s], Destination IP is Not in the router's interfaces", datapath.id)
        # Add the src MAC of the ARP into the router's arp table.
        # self.router_arp_table[pkt_ipv4.src] = pkt_ethernet.src

        if  self.switchRouter.send_frame_by_router(datapath.id, pkt_ethernet.src, pkt_ethernet.dst,
                                                   pkt_ipv4.src, pkt_ipv4.dst) is None:
            self.logger.info("Have you completed the send_frame_by_router function? It seems you have not.")
            return
        # This is for another network
        [new_src_mac, new_dst_mac, new_src_ip, new_dst_ip, new_out_port] = \
            self.switchRouter.send_frame_by_router(datapath.id, pkt_ethernet.src, pkt_ethernet.dst,
                                                   pkt_ipv4.src, pkt_ipv4.dst)

        router_intf_mac = ""

        # print([new_src_mac, new_dst_mac, new_src_ip, new_dst_ip, new_out_port])


        self.logger.info("[dpid: %s]: Frame to be sent (dst_ip: %s, dst_mac: %s, outport: %s, src_mac: %s]",
                         datapath.id, pkt_ipv4.dst, new_dst_mac, new_out_port, new_src_mac)

        pkt = packet.Packet()
        pkt.add_protocol(ethernet.ethernet(ethertype=pkt_ethernet.ethertype,
                                           dst=new_dst_mac,
                                           src=new_src_mac))
        pkt.add_protocol(ipv4.ipv4(dst=pkt_ipv4.dst,
                                   src=pkt_ipv4.src,
                                   proto=pkt_ipv4.proto))
        pkt.add_protocol(icmp.icmp(type_=pkt_icmp.type,
                                   code=pkt_icmp.code,
                                   csum=0,
                                   data=pkt_icmp.data))
        # out_port = self.intfName_to_mac[router_outport_intf][0]
        self.send_packet(datapath, int(new_out_port), pkt)
        return


    # PacketIn Event will be called whenever ther is an incoming packet to the switch
    # and the switch has forwarded that to the controller to get instructions.
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        # datapath identifies the switch which has sent the 'msg' to the controller
        # for get further instructions.
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # in_port is the incoming port that the packet has entered the switch
        in_port = msg.match['in_port']

        # To get the IP and MAC addresses of the packet we have to decode
        # the packet and look into src and dst of the frame.
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_arp = pkt.get_protocol(arp.arp)
        pkt_icmp = pkt.get_protocol(icmp.icmp)

        # Each IP is added to the list only by the first switch which sees that.
        # Guarantee the routers are not added to the list.
        if pkt_arp and pkt_arp.src_ip not in self.hostsIP_to_switch_port:
            self.hostsIP_to_switch_port[pkt_arp.src_ip] = [dpid, in_port]

        # Ignore lldp packet
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        if eth.ethertype != ether_types.ETH_TYPE_ARP and eth.dst == mac.BROADCAST_STR:
            return

        if eth.ethertype != ether_types.ETH_TYPE_ARP:
            # do the learning
            self.switchRouter.learn_mac_to_port(dpid, eth.src, in_port)
            self.logger.info("[dpid: %s]: learn_mac_to_port(%s, in_port: %s)", dpid, eth.src, in_port)

        if self.l3_enabled and self.vlan_enalbed:
            self.logger.info("You have set VLAN and L3 enabled. This is not supported in this lab.")
            self.logger.info("Please change the VLAN setting to disable in CONFIG file and restart the controller.")
            return

        if self.l3_enabled and dpid in self.routers_dpid:
            if eth.ethertype == ether_types.ETH_TYPE_ARP:
                # This is ARP request / reply.
                self.logger.info('[dpid: %s]: The router[%s], received an ARP frame.', dpid, dpid)
                self.router_handle_arp(msg)
                return
            elif pkt.get_protocol(icmp.icmp):
                # This is an ICMP packet.
                # self.logger.info('The router received an ICMP frame.')
                self.router_handle_icmp(msg)
                return
            else:
                print("something else")
        else:
            # Part 1 and Part 2 of the lab
            if self.vlan_enalbed:
                # VLAN is enabled

                out_port_vlan = None

                # If this is very first of beginning, just flood everything
                if not bool(self.hostsIP_to_switch_port):
                    self.flood_packet(msg)
                    return

                # If the incoming frame is not ARP, IPv4 or ICMP just flood it.
                myPkt_ip = None
                if pkt_arp: myPkt_ip = pkt_arp.src_ip
                elif pkt_ipv4: myPkt_ip = pkt_ipv4.src
                else:
                    self.flood_packet(msg)
                    return

                # If this is the first time we see this frame just flood it.
                # Somebody should have seen a frame (ARP, etc.) from the host before we continue.
                if myPkt_ip not in self.hostsIP_to_switch_port:
                    self.flood_packet(msg)
                    return

                # Get the original source bridge of this frame and its port
                [original_dpid, port] = self.hostsIP_to_switch_port[myPkt_ip]
                pkt_vlans = self.get_vlan_of_incoming_packet(original_dpid, port)

                if self.switchRouter.get_out_port_vlan(dpid, pkt_vlans, eth.dst) is None:
                    self.logger.error("Have you completed get_out_port_vlan function?")
                    return

                out_ports_vlan = self.switchRouter.get_out_port_vlan(dpid, pkt_vlans, eth.dst)
                self.logger.info("[dpid: %s]: get_out_port_vlan(%s, %s, %s) = %s", dpid, dpid, pkt_vlans, eth.dst, out_ports_vlan)

                if out_ports_vlan == -1:
                    # VLANs do not match, discard the frame
                    self.logger.info("[dpid: %s]: VLANs do not match. Discard the frame.", dpid)
                    return

                # Remove the incoming port of the packet from the list of return port
                # In case of flooding for example.
                out_ports_vlan = list(out_ports_vlan)
                if in_port in out_ports_vlan:
                    out_ports_vlan.remove(in_port)

                if len(out_ports_vlan) == 1:
                    # We already know which port the frame should be sent to.
                    out_port = out_ports_vlan[0]
                    actions = [parser.OFPActionOutput(out_port)]
                    data = None
                    if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                        data = msg.data
                    # else:
                    #     print("Message has buffered!")
                    actions = [parser.OFPActionOutput(out_port)]
                    out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                              in_port=in_port, actions=actions, data=data)
                    datapath.send_msg(out)

                elif len(out_ports_vlan) > 1:
                    # This is a new frame and we flood it to all VLANs ports.
                    for port in out_ports_vlan:
                        actions = [parser.OFPActionOutput(port)]
                        data = None
                        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                            data = msg.data
                        # else:
                        #     print("Message has buffered!")
                        actions = [parser.OFPActionOutput(port)]
                        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                                  in_port=in_port, actions=actions, data=data)
                        datapath.send_msg(out)
                return
            else:
                # out_port = -1
                out_port = ofproto.OFPP_FLOOD
                if self.switchRouter.get_out_port(dpid, eth.dst) is None:
                    self.logger.error("Have you completed get_out_port function?")
                    return

                self.logger.info("[dpid: %s]: get_out_port(%s, %s) = %s", dpid, dpid, eth.dst,
                                 self.switchRouter.get_out_port(dpid, eth.dst))
                if self.switchRouter.get_out_port(dpid, eth.dst) != -1:
                    # We already know which port the frame should be sent to.
                    # out_port = self.switchRouter.forwarding_table[dpid][eth.dst]
                    out_port = self.switchRouter.get_out_port(dpid, eth.dst)
                    self.logger.info("[dpis: %s]: forwarding_table[%s][%s] = %s", dpid, dpid, eth.dst, out_port)
                else:
                    # This is a new frame and we flood it to all ports.
                    out_port = ofproto.OFPP_FLOOD

                actions = [parser.OFPActionOutput(out_port)]
                data = None
                if msg.buffer_id == ofproto.OFP_NO_BUFFER:
                    data = msg.data
                # else:
                #     print("Message has buffered!")
                actions = [parser.OFPActionOutput(out_port)]
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                          in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)


    def flood_packet(self, msg):
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']
        out_port = ofproto.OFPP_FLOOD
        actions = [parser.OFPActionOutput(out_port)]
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data
        # else:
        #     print("Message has buffered!")
        actions = [parser.OFPActionOutput(out_port)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
