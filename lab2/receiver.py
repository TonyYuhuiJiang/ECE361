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
from ece361.lab2.socket import Socket
from ece361.lab2.frame import Frame

parser = argparse.ArgumentParser()
parser.add_argument("file")
parser.add_argument('--config-file', default='./config.json')
parser.add_argument('--debug', help='print debug messages', action="store_true")

args = parser.parse_args()

# read config parameters
with open(args.config_file, 'r') as config_file:
    config = json.load(config_file)

maxseqnum = config['maxseqnum']
seqnum_pool = cycle(range(0, maxseqnum + 1))

# received size is size of frame + size of sequence number in bytes
bufsize = config['frame_size'] + struct.calcsize('i')

# open a new socket to listen on a fixed port
serverSock = Socket(destination = None,
                    recvfrom_bytes = bufsize,
                    bind_addr = (config['receiver_address'], config['receiver_port']))

with open(args.file, 'wb') as f:
    rnext = next(seqnum_pool)
    ack_frame = None
    while True:
        # wait for message from the sender
        serverSock.recvfrom()
        frame = Frame.unpack_data(serverSock.msg_received['message'])
        if (args.debug):
            print('DEBUG -', frame.seqnum, frame.data, 'RECEIVED')
        if (frame.seqnum == rnext):
            # frame with correct sequence number, accept it
            rnext = next(seqnum_pool)
            f.write(frame.data)
            # update an aknowledgement frame with rnext and no data
            ack_frame = Frame(seqnum = rnext,
                              data = b'',
                              destination = serverSock.msg_received['address'])
            if (args.debug):
                print('DEBUG -', frame.seqnum, frame.data, 'ACCEPTED')

        # send the acknowledgement for rnext
        if (ack_frame):
            ack_frame.send()
