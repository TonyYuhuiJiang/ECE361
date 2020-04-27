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

import socket
import datetime
import select
from ece361.lab2.frame import Frame


server_address = ('192.168.1.1', 10000)
send_queue = []

for i in range(10):
    # create a new Frame with sequence number i, a message and 1 second ack timeout
    new_frame = Frame(seqnum=i,
                      data=('This is message # ' + str(i)).encode('ascii'),
                      destination=server_address,
                      timeout=1)
    send_queue.append(new_frame)

t_start = datetime.datetime.now()

# send all frames at once
for frame in send_queue:
    frame.send()

frame_timedout = 0
frame_delivered = 0

# repeat until all frames either receive a response or time out
while send_queue != []:
    # will block until at least one frame receives some feedback (ACK/NACK, timed out etc.)
    Frame.wait_for_multiple_ack_nacks(send_queue)

    # at least one frame receives feedback, go through the send queue
    # we have to go through the queue in reverse because we are removing elements from the queue in the loop
    # if you don't believe that try write the loop the other way and you will see problems
    for i in range(len(send_queue) - 1, -1, -1):
        if (send_queue[i].status() == Frame.Status.ack_nacked):
            # frame received by the other side
            frame_delivered += 1
            # retrieve the acknowledgement frame, which is a frame with only sequence number and no data
            ack_frame = send_queue[i].retrieve_ack_nack()
            # print the original message, the ACK/NACK and the RTT
            print(send_queue[i].data,
                  'DELIVERED. ACK:', ack_frame.seqnum,
                  'RTT:', send_queue[i].socket.t_ack - send_queue[i].socket.t_send)

            # remove frame from send queue
            send_queue.remove(send_queue[i])
        elif (send_queue[i].status() == Frame.Status.timedout):
            # timedout
            frame_timedout += 1
            print(send_queue[i].data, 'TIMED OUT.')

            # remove frame from send queue
            send_queue.remove(send_queue[i])
        else:
            # frame is still in flight. do nothing.
            pass

t_finish = datetime.datetime.now()

print("Frames delivered:", frame_delivered)
print("Frames timed out:", frame_timedout)
print("Total transmission time:", t_finish - t_start)
