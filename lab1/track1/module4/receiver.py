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
from ece361.network.socket import Socket


''' Please replace <your_student_number> with your student number to avoid conflict with other students experiments.'''

s = Socket('1003824294')
s.change_source_address(address='ece362', port='app2')

a, b = s.recvfrom()
print('The received message data:', b)
print('The message source address:', a)

s.sendto('Hi Back!', dst_address=a[0], dst_port=a[1])

print('The Header of the last sent message: ', s.last_header)
print('Last sent message: ', s.last_segment)

