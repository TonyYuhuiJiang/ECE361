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

import json, ipaddress

class SwitchRouter(object):
    def __init__(self, VLAN_config_content, routing_table_content, IP_to_mac_content):
        # Newly added variables for part 3

        # Routing table for the routers.
        # Example:
        #   { "r8" : [{'destination': '10.0.1.0/24', 'address': '172.30.0.1', 'port': 1] }
        self.routing_table = json.loads(routing_table_content)

        # Keep track of IP to MAC.
        # Format:
        #   { ip_addr : mac }
        #   ex. { '10.0.1.1' : '00:00:00:00:00:22', '10.0.2.1', '00:00:00:00:00:24' }
        self.ip_to_mac = json.loads(IP_to_mac_content)

        # Variables for parts 1 and 2

        # Forwarding table.
        # Format:
        #     { dpid : [ MAC_addr : port_no ]}
        #     ex.  { 1: {'d6:8e:ec:98:f4:a7': 5, '00:00:00:00:00:01': 1},
        #            2: {'00:00:00:00:00:09': 5, '72:95:18:aa:47:16': 5}
        #          }
        self.forwarding_table = {}

        # Translating the bridges' name to their dpid.
        # You do not need to touch this dictionary
        # Format:
        #     { [ swith_name : dpid ] }
        #     ex.  {'s4': 64, 's1': 16, 's3': 32, 's2': 21}
        self.bridgeName_to_dpid = {}

        # Translating VLANs to corresponding ports for each bridge.
        # Format:
        #     { dpid : { VLAN : [port_no] } }
        #     ex.  { 1: {'VLAN2': [3], 'VLAN1': [1, 2]},
        #            2: {'VLAN2': [2, 4], 'VLAN1': [1, 3]}
        #          }
        self.vlan_to_port = {}

        # Load and initialize the VLAN_CONFIG data into local data structure
        self.VLAN_config = json.loads(VLAN_config_content)


    def set_bridgeName_to_dpid(self, name, dpid):
        self.bridgeName_to_dpid[name] = dpid

    # Inputs:
    #   BridgeName: like the names in the topology file
    #               ex. "s1", "s2", "s3", "s4"
    def initialize_vlan_to_port(self, bridgeName):
        if bridgeName in self.bridgeName_to_dpid:
            dpid = self.bridgeName_to_dpid[bridgeName]
            self.vlan_to_port[dpid] = self.VLAN_config[bridgeName]

    def initialize_forwarding_table(self, dpid):
        if dpid not in self.forwarding_table:
            # Why we have to do this?
            self.forwarding_table.setdefault(dpid, {})

    def get_forwarding_table(self):
        return self.forwarding_table


    #### TO BE COMPLETED BY STUDENTS ####
    # Perform learning when a packet with the given source Ethernet address
    # arrives at a given bridge (specified by the dpid) on the given port.
    # given to you above to familiar yourself with its format)
    #
    # Inputs:
    #   dpid: ID of the bridge (int)
    #   etc_src: The source MAC of the incoming packet to the bridge (str)
	#			 This in the format of "00:00:00:00:00:03"
    #   in_port: The input port of the packet coming into the bridge (int)
    #
    # Returns:
    #   Nothing
    def learn_mac_to_port(self, dpid, eth_src, in_port):
        self.initialize_forwarding_table(dpid)
        '''
        TO DO

        '''
        self.forwarding_table[dpid][eth_src] = in_port



    #### TO BE COMPLETED BY STUDENTS ####
    # Given a bridge (specified by the dpid) and the destination Ethernet
    # address, return the appropriate output port. This is done by looking up
    # the forwarding table of the bridge with the given the dpid.
    #
    # Inputs:
    #   dpid: ID of the bridge (int)
    #   eth_dst: Destination MAC address (str)
    #
    # Returns:
    #   The output port (int) to forward the packet to
    #   Returns -1 if the destination MAC was not in the bridge's forwarding_table,
    #   which means the packet will be flooded to all ports.
    def get_out_port(self, dpid, eth_dst):
        # return the output port, -1 otherwise
        self.initialize_forwarding_table(dpid)
        '''
        TO DO
        '''
        if eth_dst not in self.forwarding_table[dpid]:
        	return -1
        else:
        	return self.forwarding_table[dpid][eth_dst]


    #### TO BE COMPLETED BY STUDENTS ####
    # Returns a list of VLAN name(s) for the given port of the given bridge with dpid
    #
    # Inputs:
    #   dpid: ID of the bridge (int)
    #   port_no: Port number (int)
    #
    # Returns:
    #   List of VLANs for the given port_no in the bridge with the given dpid
    #   (There might be more than one VLAN corresponding to a port)
    def get_vlans_of_port(self, dpid, port_no):
        '''
        TO DO
        '''
        VLANs = []
        for VLAN, ports in self.vlan_to_port[dpid].items():
        	if port_no in ports:
        		VLANs.append(VLAN)
        return VLANs




    #### TO BE COMPLETED BY STUDENTS ####
    # Return the appropriate output port(s) when VLAN is enabled.
    # You have to consider two cases:
    #   1. If the destination MAC address is in the forwarding_table
    #       - Return the output port if and only if the port belongs to a VLAN
    #         where the source host is a member.
    #       - Otherwise, if the output port does not belong in any of the source
    #         host's VLANs, then the packet must be dropped.
    #   2. If the output port corresponding to the destination MAC is not in the
    #      forwarding_table, then return all ports that belong in a VLAN where
    #      the source host is a member (not all VLANs)
    #       - i.e. this is a VLAN-constrained broadcast
    #
    # Inputs:
    #   dpid: ID of the bridge (int)
    #   source_host_vlans: A list containing the VLANs of the source host of the packet (list)
    #       ex. ["VLAN1", "VLAN2"] (a host might belong to multiple VLAN)
    #   eth_dst: Destination MAC of the incoming packet to the bridge (str)
    #
    # Returns:
    #   A list of output ports, or -1 variable if there is no matching port
    #       e.g. Returning [5] means the packet will be sent out on port 5
    #            Returning [1, 2, 4] means the packet will be sent out on ports 1, 2, and 4
    #            Returning -1 means there is no matching port, and the packet will be dropped
    def get_out_port_vlan(self, dpid, source_host_vlans, eth_dst):
        self.initialize_forwarding_table(dpid)
        '''
        TO DO
        '''
        out_ports = []
        if eth_dst in self.forwarding_table[dpid]:
        	port_no = self.forwarding_table[dpid][eth_dst]
        	for vlan in source_host_vlans:
        		if port_no in self.vlan_to_port[dpid][vlan]:
        			out_ports.append(port_no)
        			return out_ports
        	else:
        		return -1
        else:
        	for vlan in source_host_vlans:
        		out_ports.extend(self.vlan_to_port[dpid][vlan])
        	return out_ports


    #### PART 3, New Functions

    # Return the bridge name for the given dpid
    # Inputs:
    #   dpid: ID of the bridge (int)
    # Returns:
    #   Bridge name (str)
    def get_bridgeName_by_dpid(self, dpid):
        for bridgeName, this_dpid in self.bridgeName_to_dpid.items():
            if this_dpid == dpid:
                return bridgeName

    # Return the MAC address associated to an IP
    # Input:
    #   IP: IP address (str)
    # Returns:
    #   MAC address: Associated MAC address to the given IP (str)
    def get_mac_by_ip(self, ip):
        if ip in self.ip_to_mac:
            return self.ip_to_mac[ip]

    # Check if the given IP is withing the destination network
    # Input:
    #   IP: IP address (str)
    #   Destination network: The destination network is a string that refers back 
    #                        to the network address in CIDR format.
    #                        ex. "10.0.1.0/24" which shows hosts within this network 
    #                            can have addresses from 10.0.1.0 to 10.0.1.255.
    def is_ip_within_net(self, ip, dstNet):
        if ipaddress.ip_address(ip) in ipaddress.ip_network(dstNet):
            return True
        return False

    #### TO BE COMPLETED BY STUDENTS ####
    # Return the next hop IP and the output port that the router should send the frame on.
    # You need to use the routing_table to find out the right output interface and port.
    # You may need to use the function is_ip_within_net and get_bridgeName_by_dpid.
    # Inputs:
    #   dpid: ID of the bridge (int)
    #   ip_addr:   IP address (str) ex. "10.0.1.1"
    #
    # Returns:
    #   1. The next hop IP (str)
    #   2. The output port that the frame should be sent to (int)
    #   Return None if there is no entry in the routing_table for this ip_addr.
    #   ex.
    #   if <intf_ip and port were found>:
    #       return intf_ip, port
    def get_out_iface_info(self, dpid, ip_addr):
        '''
        TO DO
        '''
        bridgeName = self.get_bridgeName_by_dpid(dpid)
        routing_table = self.routing_table[bridgeName]
        for dic in routing_table:
        	if self.is_ip_within_net(ip_addr, dic['destination']):
        		return dic['address'],dic['port']
        else:
        	return None


    #### TO BE COMPLETED BY STUDENTS ####
    # In the router, when there is a new frame, we called this function to determine where the frame should be sent on.
    # The router need to change addresses of the frame. You have to understand which addresses need to be
    # changed and which one remains unchanged.
    # Inputs:
    #   dpid: ID of the bridge (int)
    #   src_mac: The source mac of the frame which arrives at the router
    #   dst_mac: The destination mac of the frame which arrives at the router
    #   src_ip:  The source IP of the frame which arrives at the router
    #   dst_ip:  The destination IP of the frame which arrives at the router
    #
    # Returns:
    # A list of
    #   new_src_mac: (str) The source mac address of the frame which leaves the router
    #   new_dst_mac: (str) The destination mac address of the frame which leaves the router
    #   new_src_ip: (str) The source IP address of the frame which leaves the router
    #   new_dst_ip: (str) The destination IP address of the frame which leaves the router
    #   out_port: (int) output port of the router which the frame should leave the router using it
    #
    #   Note: you have to return the output in the form of list with specific order as:
    #   ex. [new_src_mac, new_dst_mac, new_src_ip, new_dst_ip, out_port]
    def send_frame_by_router(self, dpid, src_mac, dst_mac, src_ip, dst_ip):
        '''
        TO DO
        '''
        intf_ip, out_port = self.get_out_iface_info(dpid, dst_ip)
        new_src_mac = self.get_mac_by_ip(intf_ip)
        new_dst_mac = self.get_mac_by_ip(dst_ip)

        new_src_ip = src_ip
        new_dst_ip = dst_ip 

        return [new_src_mac, new_dst_mac, new_src_ip, new_dst_ip, out_port]
