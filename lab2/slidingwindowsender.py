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
from senderbase import SenderBase
from ece361.lab2.frame import Frame

class SlidingWindowSender(SenderBase):
    def __init__(self, file, destination, frame_size, timeout, maxseqnum, sender_window_size):
        super().__init__(file, destination, frame_size, timeout, maxseqnum)
        self.send_queue = []
        self.sender_window_size = sender_window_size

    def _arqsend(self):
        # implementation of the Sliding Window ARQ protocol
        while True:
            # a queue is the perfect data structure for implementing sliding window
            while (len(self.send_queue) < self.sender_window_size):
                # fill up the sending window
                current_frame = self.get_next_frame()
                # add frame to queue
                self.send_queue.append(current_frame)

            if (self.send_queue[0].data == b''):
                # end of file
                break

            ''' Part 2: Implement the sliding window ARQ protocol:'''

            ''' Step 1: Go through the send queue and send those frames that need to be sent/resent'''
            ''' Do not forget to update the frames_sent variable'''
            ''' Your Code'''

            for current_frame in self.send_queue:
                current_frame.send()
                if SenderBase.ENABLE_DEBUG:
                    print('DEBUG -', current_frame.seqnum, current_frame.data, 'SENT')
                self.frames_sent += 1


            ''' Step 2: wait on all frames in the send_queue in parallel'''
            ''' Hint: call the wait_for_multiple_ack_nacks function'''
            ''' Your Code'''

            Frame.wait_for_multiple_ack_nacks(self.send_queue)


            ''' Step 3: Go through the send queue and process ack/nack/timeout'''
            ''' Use the status() method to check status of the frame'''
            ''' Hint: In the sliding window ARQ if a frame is acked it is implied that all earlier frames are also acked even without receiving an explicit ack(why?)'''
            ''' Your Code'''

            to_pop = 0
            for i in range(len(self.send_queue)):
                current_frame = self.send_queue[i]
                if (current_frame.status() == Frame.Status.ack_nacked):
                    to_pop = i+1

                    if SenderBase.ENABLE_DEBUG:
                        print ('DEBUG -', current_frame.seqnum, 
                                current_frame.data, 'DELIVERED',
                               'ACK:', current_frame.retrieve_ack_nack().seqnum)
                    

                elif (current_frame.status() == Frame.Status.timedout):
                    if SenderBase.ENABLE_DEBUG:
                        print('DEBUG -', current_frame.seqnum, current_frame.data, 'TIMEDOUT')
                else:
                    pass




            ''' Step 4: Remove acked frames by calling the 'pop' method on the send queue'''
            ''' In the sliding window ARQ there might be more than 1 acked frames in an iteration'''
            ''' so you might need to call 'pop' multiple times'''
            ''' Do not forget to update the frames_delivered variable'''
            ''' Your Code'''

            if SenderBase.ENABLE_DEBUG:
                print("Popping", to_pop, "frames.")
            for i in range(to_pop):
                self.send_queue.pop(0)
                self.frames_delivered+=1




