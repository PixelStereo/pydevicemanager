from thread import allocate_lock
import threading
import socket
import select
from OSC import ThreadingOSCServer, OSCClient , OSCMessage
import pybonjour
import serial
import sys


debug = True

class Serial(object):
    def __init__(self):
        self.mutex = allocate_lock()
        self.port=None

    def open(self,portname):
        self.mutex.acquire()
        self.portname=portname
        if (self.port == None):
            try:
                self.port = serial.Serial(self.portname,9600,timeout=2,stopbits=1,bytesize=8,rtscts=False, dsrdtr=False)
                self.port.flushInput()
            except Exception as e:
                pass
                #raise e
                self.port = None
        self.mutex.release()    

    def recv_packet(self,extra_title=None):
        if self.port:
            # read up to 16 bytes until 0xff
            packet=''
            count=0
            while count<16:
                s=self.port.read(1)
                if s:
                    byte = ord(s)
                    count+=1
                    packet=packet+chr(byte)
                else:
                    print "ERROR: Timeout waiting for reply"
                    break
                if byte==0xff:
                    break
            return packet
        print 'no reply from serial because there is no connexion'

    def _write_packet(self,packet):
        if self.port:
            if not self.port.isOpen():
                pass
                #sys.exit(1)

            # lets see if a completion message or someting
            # else waits in the buffer. If yes dump it.
            if self.port.inWaiting():
                self.recv_packet("ignored")

            self.port.write(packet)
            #self.dump(packet,"sent")
        else:
            print("message hasn't be send because no serial port is open")


class ServerThread(threading.Thread):
    """The thread that will run the server process."""
    def __init__(self, ip, port):
        super(ServerThread, self).__init__()
        self.ip = ip
        self.port = port
        self.daemon = True
        self.oscServer = ThreadingOSCServer((ip, port))

    def run(self):
        """ The actual worker part of the thread. """
        self.oscServer.serve_forever()
        print '---------OSC server is running on ',ip+port,'------------'

class OSC(object):
    """docstring for OSCServer"""
    def __init__(self, port,name='span'):
        super(OSC, self).__init__()
        self.port = port
        # Set up threads.
        self.threadLock = threading.Lock()
        self.serverThread = None
        client = OSCClient()

        # Start the server.
        self.__startServer__()
        info = self.serverThread.oscServer.address()
        print('OSC Server started on %s:%i' % (info[0], info[1]))
        self.zeroconf(name)
    
    def register_callback(self,sdRef, flags, errorCode, name, regtype, domain):
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            print '-----------------------------------'
            print 'registered zeroconf service : ' , name
            print  'regtype', regtype
            print 'domain' , domain

    def zeroconf(self,name):
        hostname = socket.gethostname()
        hostname = hostname.split('.local')[0]
        name = name + ' on ' + hostname 
        regtype = '_osc._udp'
        sdRef = pybonjour.DNSServiceRegister(name = name,
                                         regtype = regtype,
                                         port = self.port,
                                         callBack = self.register_callback)

        ready = select.select([sdRef], [], [])
        if sdRef in ready[0]:
            pybonjour.DNSServiceProcessResult(sdRef)

    def getDefaultIPAddress(self):
        #Attempts to resolve an IP address from the current hostname. If not possible, returns 127.0.0.1
        try :
            ipAddress = socket.gethostbyname(socket.gethostname())
        except :
            ipAddress = '127.0.0.1'
        print 'FORCE TO 127.0.0.2 because BUG'
        ipAddress = '127.0.0.1'
        return ipAddress

    def getDefaultPort(self):
        #Get the default port from the configuration file, or return 10000 if fail.
        if self.port:
            return self.port
        else:
            return 10000

    def __startServer__(self):
        #Start the server.
        # Check to see if there is already a thread and server running:
        if self.serverThread:
            if not self.serverThread.is_alive():
                self.serverThread = ServerThread(self.getDefaultIPAddress(),
                    self.getDefaultPort())
        else:
            self.serverThread = ServerThread(self.getDefaultIPAddress(),self.getDefaultPort())
        self.serverThread.start()

    def __stopServer__(self):
        #Stop the server.
        self.serverThread.oscServer.close()    
        zeroconf.sdRef.close()
