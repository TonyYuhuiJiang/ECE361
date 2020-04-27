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

import argparse
import struct
from itertools import cycle
import json
import time
import select
# from ece361.lab3.timed_socket import TimedSocket
import socket
from ece361.network_buffer import NetworkBuffer
from ece361.application import ApplicationProcess

# unpack received data into sequence number and data
def unpack_data(packed_data):
    payload_size = len(packed_data) - struct.calcsize('ii')
    format = 'ii' + str(payload_size) + 's'
    # print("format: %s; %s %s %s" % (format, packed_data, payload_size, struct.calcsize('ii')))
    return struct.unpack(format, packed_data)

# For loading configuration file from json
def load_config_from_json(filename):
    # read config parameters
    with open(filename, 'r') as config_file:
        config = json.load(config_file)

    config = argparse.Namespace(**config)
    return config

# Load config and convert everything to namespace.
# Arguments provided in command line will overwrite arguments in json config file
def load_config():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument('--config-file', default='./config.json')
    parser.add_argument('--debug', help='print debug messages', action="store_true")
    parser.add_argument('--receiver_port', help="port number the receiver is listening on", type=int, default=6789)

    args = parser.parse_args()

    config = load_config_from_json(args.config_file)

    config = vars(config)
    config.update(vars(args))

    args = argparse.Namespace(**config)

    if args.debug:
        print("Configuration loaded: ")
        print(json.dumps(vars(args), indent=2))

    return args


class Receiver():
    def __init__(self, args):
        self.Wr = args.receiver_window_size
        self.r_next = 0 # The next sequence number of the queue
        self.r_last = 0 # The last sequence number that has not been processed
        self.r_next_buf_idx = 0 # Helper index for for the buffer location for r_next (optional depending on your implementation)
        self.r_last_buf_idx = 0 # Helper index for for the buffer location for r_last (optional depending on your implementation)

        # self.current_receiver_window_size = self.Wr
        self.args = args
        self.receiver_buffer = NetworkBuffer(self.Wr)
        # received size is size of frame + size of sequence number in bytes + size of ack message
        self.bufsize = self.args.frame_size + struct.calcsize('ii')

        # create UDP socket
        self.serverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverSock.bind((args.receiver_address, args.receiver_port))

        self.maxseqnum = args.maxseqnum

        # for storing the sender address, this implementation only assume connected by a single sender
        self.sender_addr = None

        # use as counter for ack message decision
        self.recv_n_recv = 0

    '''
    Update r_next based on what had been received
    '''
    def update_r_next(self):
        ''' Your code here '''
        ''' update r_next based on the packets in the queue'''
        ''' you will need to update self.r_next and most likely self.r_next_buf_idx'''
        # n = self.receiver_buffer.Wr-self.receiver_buffer.buffer.count(None)
        
        frame_length = self.receiver_buffer.get_frame_length(self.r_next)
        while frame_length is not None:
            self.r_next = (self.r_next + frame_length) % self.maxseqnum
            frame_length = self.receiver_buffer.get_frame_length(self.r_next)



    '''
    Check if sequence number is valid for the current receiver window
    '''
    def _check_if_seqnum_is_valid(self, seqnum):
        ''' Your code here '''
        ''' Return True if the sequence number is valid else return False'''
        available_seqnum = []
        lower_bound = self.r_next
        upper_bound = self.r_last+self.Wr-1
        if(lower_bound%self.maxseqnum == upper_bound%self.maxseqnum):
            available_seqnum.append(lower_bound%self.maxseqnum)

        else:
            for i in range(lower_bound, upper_bound+1):
                available_seqnum.append(i%self.maxseqnum)
                
        if (seqnum%self.maxseqnum) in available_seqnum and self.receiver_buffer._check_if_frame_can_insert(seqnum, self.args.frame_size):
            return True
        else:
            return False


    '''
    Calculate and return the flow control window size
    '''
    def _get_flow_control_window(self):
        flow_control_window_size = 0
        ''' Your code here '''
        if self.r_last > self.r_next:
            flow_control_window_size = self.r_last+self.Wr-self.r_next - self.maxseqnum
        else:
            flow_control_window_size = self.r_last+self.Wr-self.r_next
        ''' Calculate and return the flow control window size '''
        return flow_control_window_size

    '''
    seqnum: sequence number of the frame
    data: data of the frame
    '''
    def insert_packet_to_queue(self, seqnum, data):
        ''' Your code here'''
        ''' Insert a new packet to the queue, depending on the seqnum and the condition of the queue'''
        ''' Maybe helpful to use the _check_if_seqnum_is_valid helper function'''

        if self._check_if_seqnum_is_valid(seqnum) and self.receiver_buffer.insert_frame(seqnum, data):
            self.update_r_next()





    '''
    Receive packet and insert packet to queue
    '''
    def receive_from_available_packets(self, max_receive=1):
        n_recv = 0
        while True:
            if n_recv >= max_receive:
                break
            waiting_sockets = [self.serverSock]
            readable, _, exceptional = select.select(waiting_sockets, [], waiting_sockets, 0)

            if len(readable) >= 1:
                packed_data, self.sender_addr = self.serverSock.recvfrom(self.bufsize)
                seqnum, keepalive, data = unpack_data(packed_data)
                if (self.args.debug):
                    print('DEBUG - seq: %s, ack: %s, data: %s RECEIVED' % (seqnum, keepalive, data))
                if keepalive == 1:
                    self.send_ack(self._get_flow_control_window())
                    continue
                ''' The following line calls the insert_packet_to_queue which we will need to implement '''

                self.insert_packet_to_queue(seqnum, data)
                n_recv += 1
            elif len(exceptional) >= 1:
                print("socket exception")
            else:
                # nothing to be read or handled
                break
        return n_recv

    ''' Sending ack message to the sender '''
    def send_ack(self, flow_control_window_size=0):
        if self.sender_addr is not None:
            if (self.args.debug):
                print('DEBUG - Acking with r_next: %s, and W_A (available window size) %s' % (self.r_next, flow_control_window_size))

            self.serverSock.sendto(struct.pack('ii', self.r_next, flow_control_window_size), self.sender_addr)
            return True


    '''
    This function is used by the application process to obtain data from the networking
    max_bytes: max number of bytes the application would like to read
    '''
    def application_get_data(self, max_bytes=None):
        return_data = b''

        ''' Your code here '''
        ''' based on r_last and the max_bytes, read the data from the queue and return it to the application '''
        ''' you will want to update the self.r_last and most likely self.r_last_buf_idx '''
        byte_poped = 0
        if max_bytes!=None:
            frame_len = self.receiver_buffer.get_frame_length(self.r_last)
            while  frame_len != None and byte_poped+frame_len<=max_bytes:
                return_data += self.receiver_buffer.pop_frame(self.r_last)
                byte_poped += frame_len
                self.r_last = (self.r_last + frame_len) % self.maxseqnum #Not sure here
                frame_len = self.receiver_buffer.get_frame_length(self.r_last)

        else:
            while self.receiver_buffer.is_start_of_frame(self.r_last):
                frame_len = self.receiver_buffer.get_frame_length(self.r_last)
                return_data += self.receiver_buffer.pop_frame(self.r_last)
                # print("After poped, the buffer is look like: {}".format(self.receiver_buffer.buffer))
                self.r_last = (self.r_last + frame_len) % self.maxseqnum



        return return_data



    '''Execute one iteration of receiver tasks'''
    def run_receive(self):

        # Step 1: Receive available packet from socket and insert to receiver queue
        self.recv_n_recv += self.receive_from_available_packets()

        # Step 2: Send control message (i.e. ACK and Flow control window info)
        avail_window_size = self._get_flow_control_window()
        if self.recv_n_recv > 0:
            self.send_ack(avail_window_size)
            self.recv_n_recv = 0

    def __del__(self):
        if self.serverSock:
            self.serverSock.close()

def start_receiver():
    args = load_config()
    receiver = Receiver(args)
    application_process = ApplicationProcess(args)
    application_process.application_processing_setup()
    while True:
        # Receiver and application take turn processing
        receiver.run_receive()
        application_process.process(receiver)

        # Uncomment this line if your code takes up too much, but make sure you comment it out when you submit
        # time.sleep(0.0001)

if __name__ == "__main__":
    start_receiver()
