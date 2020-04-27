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

def receive_file(student_id, file_name, source_address, source_port, extra_args):
    ''' The counter keeps track of the number of segments the receiver receives from the sender and must be increased
    as the receiver continues to get more segments.'''
    segment_counter = 0

    ''' Part 1. Create a socket here by using your student_id as an input argument and change the source address 
    and port to the source_address and source_port that is passed as an argument to this function.'''

    ''' Your Code'''
    s = Socket(student_id)
    s.change_source_address(address=source_address, port=source_port)
    ''' Use this variable to keep track on how much data you have received so far.'''
    received_buffer = 0
    file_size = None

    while True:
        ''' Part 2. Use the Socket to receive data messages from the sender and reply with "ACK" if the size of the data 
            you received is more then zero bytes. if not, send a "NACK" and use the socket to receive the data again. You need 
            to repeat this step until you send an "ACK". You only exchange the file size in this step.'''

        ''' Your Code'''
        a,b = s.recvfrom()
        if b != '':
            s.sendto("ACK", dst_address = a[0], dst_port = a[1])
            file_size = int(b)
            break
        else:
            s.sendto("NACK", dst_address = a[0], dst_port = a[1])


    ''' This creates the destination file name to hold the senders data.'''
    fd = open(file_name, 'a+')
    while True:
        ''' Part 3. You need to compare the buffer_size with the actual file size as a condition to
         continue to receive the file chunks. 
         
        For each message you receive, send an "ACK" and write that chunk in the file you just created.
        You only need to send an "ACK" if the size of the data you received is larger than zero and if not, you will 
        send a "NACK". After sending a "NACK" you need to redo the same steps until you receive a file chunk which is
        more than zero bytes. Afterwards, you will send an "ACK" to the sender and you can pass to the next chunk.'''
        if received_buffer < file_size:
            ''' Your Code'''
            a,b = s.recvfrom()
            if b != '':
                s.sendto("ACK", dst_address = a[0], dst_port = a[1])
                received_buffer += len(b)
                fd.write(b)
                segment_counter+=1
            else:
                print("bad")
                s.sendto("NACK", dst_address = a[0], dst_port = a[1])


        else:
            ''' You need to close the file descriptor to empty out the output buffer on the disk.'''
            fd.close()
            break
    print('The file transmission is now completed!')
    extra_args.append(received_buffer)
    extra_args.append(segment_counter)


extra_arguments = []
''' Please replace the input arguments that start with Your_... with your information.'''
receive_file('1003824294', 'iso_copy.txt', 'host2', '20',
                   extra_arguments)

print(extra_arguments)


''' Important Information: An ACK or a NACK message is only a message with an ACK/NACK as its data. Therefore, it 
 cointains the actual message. See the exmaples below.'''

# sendto(application_data='ACK', dst_address=?, dst_port=?)
# sendto(application_data='NACK', dst_address=?, dst_port=?)
