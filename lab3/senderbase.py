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

from abc import ABC, abstractmethod
from itertools import cycle
from enum import Enum
import datetime
from ece361.frame import Frame

class SenderBase(ABC):
    ENABLE_DEBUG = False

    class TimerStatus(Enum):
        notsent = 0, # Have not send a frame, timer has not started
        inflight = 1, # Packet(s) sent, timer started
        timedout = 2, # timeout for the timer

    def __init__(self, file, destination, frame_size, maxseqnum):
        self.fp = open(file, 'rb')
        self.destination = destination
        self.frame_size = frame_size
        self.maxseqnum = maxseqnum

        # transmission statistics
        self.frames_sent = 0
        self.frames_delivered = 0

        self.next_seqnum = 0
        self.seqnum = 0

    def get_next_frame(self):
        # read data from file
        data = self.fp.read(self.frame_size)

        # end of file, no more data available
        if len(data) == 0:
            return None

        # create a new frame object and advance sequence number
        self.seqnum = self.next_seqnum
        new_frame = Frame(self.seqnum, data)
        self.next_seqnum = (self.next_seqnum + self.frame_size) % self.maxseqnum

        # return the encapsulated Frame object
        return new_frame

    def sendfile(self):
        self.t_start = datetime.datetime.now()
        self._arqsend()
        self.t_finish = datetime.datetime.now()

    @abstractmethod
    def _arqsend(self):
        pass


    def __del__(self):
        if hasattr(self, "fp") and self.fp is not None:
            self.fp.close()
