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

import datetime
import sys
from senderbase import SenderBase
from ece361.lab2.frame import Frame

class StopWaitSender(SenderBase):
    def __init__(self, file, destination, frame_size, timeout, maxseqnum):
        super().__init__(file, destination, frame_size, timeout, maxseqnum)
        self.send_queue = []

        self.rtt_total = datetime.timedelta()
        self.rtt_max = datetime.timedelta()

    def _update_rtt(self, t_send, t_ack):
        rtt = datetime.timedelta()
        ''' Part 1: Calculate RTT based on the send and ack receive time:

            Step 1: calculate a new RTT sample based on t_send and t_ack
            Step 2: update the statistics rtt_total and rtt_max.'''

        ''' Your Code'''
        rtt_sample = t_ack-t_send
        self.rtt_total += rtt_sample
        self.rtt_max = max(self.rtt_max, rtt_sample)

        return rtt

    def _arqsend(self):
        # implementation of the Stop and Wait ARQ protocol
        while True:
            if (self.send_queue == []):
                # previous frame cleared. send the next frame.
                current_frame = self.get_next_frame()
                if (current_frame.data == b''):
                    # end of file
                    break
                # add frame to queue
                self.send_queue.append(current_frame)

            # send the frame
            current_frame.send()
            if SenderBase.ENABLE_DEBUG:
                print('DEBUG -', current_frame.seqnum, current_frame.data, 'SENT')

            self.frames_sent += 1

            # wait for acknowledgement
            current_frame.wait_for_ack_nack()

            # check frame status and respond accordingly
            if (current_frame.status() == Frame.Status.ack_nacked):
                # in our implementation of stop and wait there is no nack so just accept the frame as an ack
                self._update_rtt(current_frame.sendtime(), current_frame.acktime())

                self.frames_delivered += 1
                if SenderBase.ENABLE_DEBUG:
                    print ('DEBUG -', current_frame.seqnum, current_frame.data, 'DELIVERED',
                           'ACK:', current_frame.retrieve_ack_nack().seqnum)
                self.send_queue.pop(0)

            elif (current_frame.status() == Frame.Status.timedout):
                if SenderBase.ENABLE_DEBUG:
                    print('DEBUG -', current_frame.seqnum, current_frame.data, 'TIMEDOUT')
            else:
                # since this is stop and wait we should never be here
                print('Error! Should never see status', current_frame.status(),
                      'after receiving acknowledgement for stop and wait ARQ', file=sys.stderr)
