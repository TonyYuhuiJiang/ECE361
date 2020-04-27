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
import datetime
from ece361.lab2.frame import Frame

class SenderBase(ABC):
    ENABLE_DEBUG = False

    def __init__(self, file, destination, frame_size, timeout, maxseqnum):
        self.fp = open(file, 'rb')
        self.destination = destination
        self.frame_size = frame_size
        self.timeout = timeout

        # transmission statistics
        self.frames_sent = 0
        self.frames_delivered = 0

        # sequence numbers are between 0 and maxseqnum inclusive
        self.seqnumpool = cycle(range(maxseqnum + 1))
        self.seqnum = next(self.seqnumpool)

    def get_next_frame(self):
        # read data from file
        data = self.fp.read(self.frame_size)

        # create a new frame object and advance sequence number
        # note: the order of the next 3 lines is important
        nextseqnum = next(self.seqnumpool)
        new_frame = Frame(self.seqnum, data, self.destination, expected_ack=nextseqnum, timeout=self.timeout)
        self.seqnum = nextseqnum

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
        self.fp.close()
