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
import sys
import json

from senderbase import SenderBase
from flow_control_sender import FlowControlSlidingWindowSender
from congestion_control_sender import CongestionControlSlidingWindowSender

''' Parsing command line arguments and config from json file '''
#--------- Parsing command line arguments and config from json file ---------
parser = argparse.ArgumentParser()
parser.add_argument('file')
parser.add_argument('--config-file', default='./config.json')
parser.add_argument('--debug', help='print debug messages', action="store_true")
parser.add_argument('--verbose', help="print extra information", action="store_true")
parser.add_argument('--receiver_port', help="port number the receiver is listening on", default=6789)

args = parser.parse_args()

if (args.debug):
    SenderBase.ENABLE_DEBUG = True
else:
    SenderBase.ENABLE_DEBUG = False

# read config parameters
with open(args.config_file, 'r') as config_file:
    config = json.load(config_file)

config.update(vars(args))

args = argparse.Namespace(**config)
#--------- End of config parsing ---------


# send the file using the flow control and congestion control protocol specified in the config file
if (args.protocol == 'many_to_many_slidingwindow' or args.protocol == 'flow_control'):
    sender = FlowControlSlidingWindowSender(args.file,
                                (args.receiver_address, int(args.receiver_port)),
                                args.frame_size,
                                args.timeout,
                                args.maxseqnum,
                                args.sender_window_size,
                                args.keepalive_timeout,
                                args.use_flow_control,
                                args)
elif (args.protocol == 'congestion_control'):
    sender = CongestionControlSlidingWindowSender(args.file,
                                (args.receiver_address, int(args.receiver_port)),
                                args.frame_size,
                                args.timeout,
                                args.maxseqnum,
                                args.sender_window_size,
                                args.keepalive_timeout,
                                args.use_flow_control,
                                args.sender_max_window_size,
                                args)
else:
    print('Unkown ARQ protocol %s.' %args.arq_protocol, file=sys.stderr)
    sys.exit(0)

sender.sendfile()

print("Protocol:", args.protocol)
print("Final frames sent:", sender.frames_sent)
print("Final frames delivered:", sender.frames_delivered)
print("transmission time:", sender.t_finish - sender.t_start)
print("max RTT: %s" % sender.rtt_max)

