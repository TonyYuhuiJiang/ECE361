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

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info


def ece361_lab5_net():
    "Create the network and add nodes to it."

    net = Mininet(controller=Controller)

    info('*** Adding controller\n')
    c0 = RemoteController('c0', ip='127.0.0.1', port=6653)
    net.addController(c0)

    info('*** Adding hosts\n')
    h1 = net.addHost('h1', ip='10.0.1.11/24', mac='00:00:00:00:00:01', defaultRoute="via 10.0.1.1")
    h2 = net.addHost('h2', ip='10.0.1.12/24', mac='00:00:00:00:00:02', defaultRoute="via 10.0.1.1")
    h3 = net.addHost('h3', ip='10.0.1.13/24', mac='00:00:00:00:00:03', defaultRoute="via 10.0.1.1")
    h4 = net.addHost('h4', ip='10.0.1.14/24', mac='00:00:00:00:00:04', defaultRoute="via 10.0.1.1")
    h5 = net.addHost('h5', ip='10.0.2.11/24', mac='00:00:00:00:00:05', defaultRoute="via 10.0.2.1")
    h6 = net.addHost('h6', ip='10.0.2.12/24', mac='00:00:00:00:00:06', defaultRoute="via 10.0.2.1")
    h7 = net.addHost('h7', ip='10.0.2.13/24', mac='00:00:00:00:00:07', defaultRoute="via 10.0.2.1")
    h8 = net.addHost('h8', ip='10.0.3.11/24', mac='00:00:00:00:00:08', defaultRoute="via 10.0.3.1")
    h9 = net.addHost('h9', ip='10.0.3.12/24', mac='00:00:00:00:00:09', defaultRoute="via 10.0.3.1")
    h10 = net.addHost('h10', ip='10.0.3.13/24', mac='00:00:00:00:00:10', defaultRoute="via 10.0.3.1")

    info('*** Adding Routers\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow10,OpenFlow12', dpid='1')
    s2 = net.addSwitch('s2', protocols='OpenFlow10,OpenFlow12', dpid='2')
    s3 = net.addSwitch('s3', protocols='OpenFlow10,OpenFlow12', dpid='3')
    r4 = net.addSwitch('r4', protocols='OpenFlow10,OpenFlow12', dpid='4')

    info('*** Creating links\n')
    net.addLink(h1, s1, port1=1, port2=1)
    net.addLink(h2, s1, port1=1, port2=2)
    net.addLink(h3, s1, port1=1, port2=3)
    net.addLink(h4, s1, port1=1, port2=4)
    net.addLink(h5, s2, port1=1, port2=1)
    net.addLink(h6, s2, port1=1, port2=2)
    net.addLink(h7, s2, port1=1, port2=3)
    net.addLink(h8, s3, port1=1, port2=1)
    net.addLink(h9, s3, port1=1, port2=2)
    net.addLink(h10, s3, port1=1, port2=3)
    net.addLink(s1, r4, port1=5, port2=1)
    net.addLink(s2, r4, port1=4, port2=2)
    net.addLink(s3, r4, port1=4, port2=3)

    info('*** Starting network\n')
    net.start()

    info('*** Running CLI\n')
    CLI(net)

    info('*** Stopping network')
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    ece361_lab5_net()
