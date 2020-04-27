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
import os


def send_file(student_id, file_name, source_address, source_port, destination_address, destination_port, extra_args):
    ''' The counter keeps track of the number of segments transmitted to the receiver.'''
    segment_counter = 0
    ''' The maximum size of each message data.'''
    buffer_size = 100

    ''' Part 1. Create a socket here by using your student_id 
    as an input argument and change the source address 
    and port to the source_address and source_port 
    that is passed as an argument to this function.'''

    ''' Your Code'''
    s = Socket(student_id)
    s.change_source_address(address=source_address, port=source_port)

    ''' Part 2. Use the socket you just created to 
    send the size of the <file_name> to the receiver.'''
    
    ''' Your Code'''
    file_size = os.path.getsize(file_name)
    s.sendto(str(file_size), dst_address = destination_address, 
            dst_port = destination_port)

    while True:
        ''' Part 3. Use the socket you created to listen for 
        incoming Acknowledgement message. The ACK will confirm
        the receipt of the file size by the receiver.'''
        ''' Your Code'''
        a, b = s.recvfrom()
        ''' Part 4. You need to implement a mechanism to check 
        if the incoming message is an "ACK" or a "NACK" and
        resend the data if it is a NACK. After resending, 
        you need to check again for the acknowledgement. You can
        only go to the next part of the code if you 
        receive an ACK message.'''
                 
        if b == "ACK":
            break
        else:
            s.sendto(str(file_size), dst_address = destination_address, dst_port = destination_port)
           

    fd = open(file_name, 'r')
    while True:
        ''' Part 5. You need to implement a mechanism that read chunks of the data from the file that is equivalent 
        to the size of the <buffer_size> variable. 
        After reading from the file, you need to send the file chunk to the specified destination and wait 
        to receive the "ACK" message. If it is a NACK, you need to resend the message and wait again for the "ACK" 
        message. The code moves on only if it receives the "ACK" message.'''

        ''' Your Code'''
        content = fd.read(buffer_size)
        if content=='':
        	break
        segment_counter+=1
        s.sendto(content, dst_address = destination_address, dst_port = destination_port)
        
        ''' Hint: You may need to implement a loop that handles the ACK messages.'''
        while True:
            a, b = s.recvfrom()
            if b == "ACK":
                break
            else:
                s.sendto(content, dst_address = destination_address, dst_port = destination_port)


    ''' The file descriptor must be closed after the transfer is completed.'''
    fd.close()
    print('File transmission is completed!')
    extra_args.append(file_size)
    extra_args.append(segment_counter)

extra_arguments = []
''' Please replace the input arguments that start with Your_... with your information.'''

send_file('1003824294', 'iso.txt', 'host1', '10', 'host2',
          '20', extra_arguments)


print(extra_arguments)


''' Important Information: An ACK or a NACK message is only a message with an ACK/NACK as its data. Therefore, it 
 cointains the actual message. See the exmaples below.'''

# sendto(application_data='ACK', dst_address=?, dst_port=?)
# sendto(application_data='NACK', dst_address=?, dst_port=?)



