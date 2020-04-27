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

import select
import sys
from senderbase import SenderBase
from ece361.frame import Frame, unpack_data
import socket
import struct
import time
from enum import Enum

class CongestionControlSlidingWindowSender(SenderBase):
    # class Status(Enum):
    #     slow_start = 0,
    #     congestion_avoidance = 1,


    def __init__(self, file, destination, frame_size, timeout, maxseqnum, window_size, keepalive_timeout, use_flowcontrol, max_window_size, args):
        super().__init__(file, destination, frame_size, maxseqnum)
        self.args = args

        # Send window size
        self.send_window_size = window_size
        self.max_window_size = max_window_size

        # Slowstar Threshold
        self.ssthreshold = max_window_size

        # Send Queue
        self.send_queue = []
        self.send_queue_byte_length = 0

        # RTT and RTO timer info
        self.rtt = None
        self.rtt_max = 0
        self.rtt_timer_status = SenderBase.TimerStatus.notsent
        self.rtt_timer_seqnum = None # the expected seqnum for calculating RTT
        self.rtt_timer = None

        self.rto_timer_status = SenderBase.TimerStatus.notsent
        self.rto_timer = None
        self.rto = timeout

        # end of file is reached for the file to send
        self.end_of_file_reached = False

        # Flow control
        self.use_flowcontrol = use_flowcontrol

        # Keep alive
        self.keepalive_timeout = keepalive_timeout
        self.keepalive_last_time = time.time()

        self.avail_receiver_window = window_size # initialized to same as the sender window size
        self.maxseqnum = maxseqnum

        # Socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #*************new parameters list here************
        # self.cc_status = CongestionControlSlidingWindowSender.Status.slow_start
        self.cwnd = frame_size
        # self.cc_thres = self.max_window_size



    def _calcualte_rto_from_rtt(self, rtt):
        # Fixed RTO for now
        return self.rto

    '''
    Update the send queue based on the ACK number
    ack_seqnum: ACK sequence number
    @return: frames confirmed
    '''
    def _update_send_queue(self, ack_seqnum):
        ''' remember to update the rto timer '''
        frames_confirmed = 0
        confirmed_list = []
        ''' your code here '''

        for i in range(len(self.send_queue)):
            if self.send_queue[i].seqnum < ack_seqnum:
                frames_confirmed += 1
        for _ in range(frames_confirmed):
            self.send_queue_byte_length -= self.send_queue[0].length
            frame = self.send_queue.pop(0)
            pair = (frame.seqnum, frame.seqnum+frame.length)
            confirmed_list.append(pair)

        current_time = time.time()
        if frames_confirmed != 0:
            self.rto_timer_status = SenderBase.TimerStatus.inflight
            self.rto_timer = current_time

            if self.rtt_timer_status == SenderBase.TimerStatus.inflight:
                for pair in confirmed_list:
                    if self.rtt_timer_seqnum in range(pair[0], pair[1]):
                        self.rtt_timer_status = SenderBase.TimerStatus.notsent
                        self.rtt = current_time - self.rtt_timer
                        self.rtt_max = max(self.rtt, self.rtt_max)
                        break
        elif current_time - self.rto_timer > self.rto:
            self.rto_timer_status = SenderBase.TimerStatus.timedout
        
        #********************CC implementation******************
        # if self.cwnd <= self.ssthreshold: 
        #     self.cwnd += frames_confirmed * self.args.frame_size #slow_start: x2 every rtt
        # else:
        #     self.cwnd = self.args.frame_size #congestion_avoidance: x2 every rtt


        return frames_confirmed 

    def _recv_from(self):
        message, _ = self.sock.recvfrom(struct.calcsize('ii'))
        if message != b'':
            ack_seqnum, flow_control_window = struct.unpack("ii", message)
            return ack_seqnum, flow_control_window

    '''
    Get the frame size
    '''
    def _get_next_frame_size(self, window_size):
        if window_size < self.frame_size:
            return window_size
        else:
            return self.frame_size

    '''
    append a frame to the queue
    '''
    def _append_to_queue(self, current_frame):
        if SenderBase.ENABLE_DEBUG:
            # print("DEBUG - %s %s INSERTED TO BUFFER" % (current_frame.seqnum, current_frame.data))
            print("DEBUG - %s INSERTED TO BUFFER" % (current_frame.seqnum))
        self.send_queue.append(current_frame)
        self.send_queue_byte_length += current_frame.length

    '''
    send frame
    '''
    def _send_frame(self, frame):
        packed_frame = frame.get_frame()
        self.sock.sendto(packed_frame, self.destination)
        frame.set_sent()

    '''
    fill the buffer based on the available window size
    '''
    def fill_buffer(self, window_size):
        end_of_file_reached = False
        while self.send_queue_byte_length + self._get_next_frame_size(window_size) <= window_size:
            # fill up the sending window
            current_frame = self.get_next_frame()
            # add frame to queue
            if current_frame is not None:
                self._append_to_queue(current_frame)
            else: # End of File
                end_of_file_reached = True
                break
        return end_of_file_reached

    '''
    Calculate the sender window size
    '''
    def calc_window_size(self):
        ''' calculate the sender window based on wether flow control is turned on '''
        ''' return the actual window size '''
        actual_window_size = 0
        if self.use_flowcontrol:
            ''' Your code here '''
            actual_window_size = min(self.send_window_size, self.avail_receiver_window, self.maxseqnum)
        else:
            ''' Your code here'''
            actual_window_size = self.send_window_size


        return actual_window_size

    '''
    send frames in queue
    max_frames: maximum number of frames to send, None means no limit
    @return: number of frame sent
    '''
    def _send_frames_in_queue(self, max_frames=None):
        ''' send the frames in queue, start from the oldest unACKed frame '''
        ''' you should update the rto timer here and self.frames_sent'''
        frame_sent_count = 0
        if self.rto_timer_status == SenderBase.TimerStatus.notsent:
            self.rto_timer = time.time()
            self.rto_timer_status = SenderBase.TimerStatus.inflight

        for f in self.send_queue:
            if f.status != Frame.Status.inflight:
                self._send_frame(f)
                frame_sent_count += 1

            if self.rtt_timer_status == SenderBase.TimerStatus.notsent:
                self.rtt_timer_seqnum = f.seqnum
                self.rtt_timer = time.time()
                self.rtt_timer_status = SenderBase.TimerStatus.inflight

            if max_frames and frame_sent_count == max_frames:
                break

       
        self.frames_sent += frame_sent_count
        return frame_sent_count


    def _check_received_data_from_socket(self):
        while True:
            waiting_sockets = [self.sock]
            readable, _, exceptional = select.select(waiting_sockets, [], waiting_sockets, 0)

            ''' Step 3: Receive ack'''
            if len(readable) >= 1:
                recv_info = self._recv_from()
                if recv_info is not None:
                    ack_seqnum, flow_control_window = recv_info
                    if SenderBase.ENABLE_DEBUG:
                        print('DEBUG - Received control message from receiver. ack seqnum: %s flow_control_window: %s' % (ack_seqnum, flow_control_window))



                    frame_confirmed = self._update_send_queue(ack_seqnum)
                    self.frames_delivered += frame_confirmed

                    ''' Your code here for congestion control '''
                    if frame_confirmed == 0:
                        self.send_window_size = self.frame_size
                    else:
                        new_size = self.send_window_size + frame_confirmed*self.args.frame_size
                        self.send_window_size = min(self.max_window_size, new_size, self.avail_receiver_window)
                    # print("send_window_size is {}".format(self.send_window_size))


                    if flow_control_window != self.avail_receiver_window:
                        if SenderBase.ENABLE_DEBUG:
                            print('DEBUG - Updated flow control window from %s to %s' % (self.avail_receiver_window, flow_control_window))
                        self.avail_receiver_window = flow_control_window


            elif len(exceptional) >= 1:
                # should never be here
                print("socket exception", file=sys.stderr)
            else:
                break

    ''' Check if timeout occurs '''
    def _check_timeout(self):
        ''' check if there is a timeout'''
        ''' You should probably update the rto_timer_status and resend the last ACKed frame'''
        ''' Only a single timer is used '''
        ''' You should also consider congestion control here'''
        ''' Your code here '''
        if self.rto_timer_status == SenderBase.TimerStatus.timedout:
            ################ CC
            # Crash
            # self.ssthreshold = self.cwnd/2
            # self.cwnd = self.args.frame_size

            # self.cc_status = CongestionControlSlidingWindowSender.Status.slow_start
            ################### CC

            self.rto_timer_status = SenderBase.TimerStatus.inflight
            for frame in self.send_queue:
                frame.set_timeout()
            self.rto_timer = time.time()
            self._send_frames_in_queue(1)


    def _arqsend(self):
        # For verbose printing
        print_time = time.time()

        # implementation of the Sliding Window ARQ protocol
        # a queue is the perfect data structure for implementing sliding window
        while True:

            ''' Step 1: push frames to the send queue'''
            # initially assume receive window is infinite until the first control message is received
            self.end_of_file_reached = self.fill_buffer(self.calc_window_size())
            if self.end_of_file_reached and self.send_queue_byte_length == 0: #finished all the sending and receiving ack for all the packets
                break

            ''' Step 2: Send all frames in the send queue'''

            self._send_frames_in_queue()

            ''' Step 3: check timeout'''

            self._check_timeout()

            ''' Step 4: check Receive data from socket'''

            self._check_received_data_from_socket()



            # Keep alive for handling the TCP stall issue
            if time.time() - self.keepalive_last_time > self.keepalive_timeout:
                keepalive_frame = Frame(0, "", ack=1)
                self._send_frame(keepalive_frame)
                self.keepalive_last_time = time.time()


            if self.args.verbose:
                if time.time() - print_time > 5:
                    print("-------------------")
                    print("Periodic Printing:")
                    print("Send queue length: %s" % self.send_queue_byte_length)
                    print("Flow control receiving window: %s" % self.avail_receiver_window)
                    print("Frames sent: %s" % self.frames_sent)
                    print("Frames delivered: %s" % self.frames_delivered)
                    print("")
                    print_time = time.time()

            # Uncomment this line if your code takes up too much, but make sure you comment it out when you submit
            # time.sleep(0.0001)


