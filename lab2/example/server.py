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

from ece361.lab2.socket import Socket
from ece361.lab2.frame import Frame

# bind the socket to the port
server_address = ('192.168.1.1', 10000)

# create the socket
serverSock = Socket(destination = None,
                    recvfrom_bytes = 4096,
                    bind_addr = server_address)

while True:
    # wait for incoming data
    serverSock.recvfrom()
    # parse the received raw bytes into a frame object with sequence number and data
    frame = Frame.unpack_data(serverSock.msg_received['message'])

    # construct the acknowledgement frame with the next sequence number of the received frame and no data
    ack = frame.seqnum + 1
    ack_frame = Frame(seqnum = ack,
                      data = b'',
                      destination = serverSock.msg_received['address'])
    ack_frame.send()

    print ('RECEIVED:', frame.seqnum, frame.data, 'ACK:', ack)
