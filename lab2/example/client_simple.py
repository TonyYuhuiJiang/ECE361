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
from ece361.lab2.frame import Frame

server_address = ('192.168.1.1', 10000)
send_queue = []

for i in range(10):
    # create a new Frame object with 1 second ack timeout
    new_frame = Frame(seqnum=i,
                      data=('This is message # ' + str(i)).encode('ascii'),
                      destination=server_address,
                      timeout=1)
    send_queue.append(new_frame)

frame_delivered = 0
frame_timedout = 0

t_start = datetime.datetime.now()
# send the frame, wait for its ack/nack, send next frame ... (i.e. stop and wait)
for frame in send_queue:
    frame.send()
    frame.wait_for_ack_nack()

    if (frame.status() == Frame.Status.ack_nacked):
        # frame received by the other side
        frame_delivered += 1
        print(frame.data,
              'DELIVERED. ACK:', Frame.unpack_data(frame.socket.msg_received['message']).seqnum,
              'RTT:', frame.socket.t_ack - frame.socket.t_send)
    else:
        # Timed out
        frame_timedout += 1
        print(frame.data, "TIMED OUT.")

t_finish = datetime.datetime.now()

print("Frames delivered:", frame_delivered)
print("Frames timed out:", frame_timedout)
print("Total transmission time:", t_finish - t_start)
