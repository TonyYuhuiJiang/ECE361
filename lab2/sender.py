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
from stopwaitsender import StopWaitSender
from slidingwindowsender import SlidingWindowSender

parser = argparse.ArgumentParser()
parser.add_argument('file')
parser.add_argument('--config-file', default='./config.json')
parser.add_argument('--debug', help='print debug messages', action="store_true")

args = parser.parse_args()

if (args.debug):
    SenderBase.ENABLE_DEBUG = True
else:
    SenderBase.ENABLE_DEBUG = False

# read config parameters
with open(args.config_file, 'r') as config_file:
    config = json.load(config_file)

# send the file using the ARQ protocol specified in the config file
if (config['arq_protocol'] == 'stopandwait'):
    sender = StopWaitSender(args.file,
                           (config['receiver_address'], config['receiver_port']),
                            config['frame_size'],
                            config['timeout'],
                            config['maxseqnum'])
elif (config['arq_protocol'] == 'slidingwindow'):
       sender = SlidingWindowSender(args.file,
                                   (config['receiver_address'], config['receiver_port']),
                                    config['frame_size'],
                                    config['timeout'],
                                    config['maxseqnum'],
                                    config['sender_window_size'])
else:
    print('Unkown ARQ protocol %s.' %config['arq_protocol'], file=sys.stderr)
    sys.exit(0)

sender.sendfile()

print("ARQ protocol:", config['arq_protocol'])
print("Frame size:", config['frame_size'])
print("Frames sent:", sender.frames_sent)
print("Frames delivered:", sender.frames_delivered)
print("Total transmission time:", sender.t_finish - sender.t_start)

if (config['arq_protocol'] == 'stopandwait'):
    print("Average RTT:", sender.rtt_total/sender.frames_delivered)
    print("Maximum RTT:", sender.rtt_max)
else:
    print("Sender window size:", config['sender_window_size'])
