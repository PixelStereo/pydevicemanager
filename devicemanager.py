#! /usr/bin/env python
# -*- coding: utf-8 -*-
import threading
import socket
import select
from OSC import ThreadingOSCServer, OSCClient , OSCMessage
#import pybonjour
client = OSCClient()

debug = True

def run(parent, port=22222):
    OSCServer(parent, port)


class ServerThread(threading.Thread):
    """The thread that will run the server process."""
    def __init__(self, parent, ip, port):
        super(ServerThread, self).__init__()
        self.parent = parent
        self.ip = ip
        self.port = port
        self.daemon = True
        self.oscServer = ThreadingOSCServer((ip, port))
        self.oscServer.addMsgHandler('default', self.defaultMessageHandler)
        if debug:
            self.the_class = parent.__class__.__name__
            print('xxxxXXXXXXxxxxxx', self.the_class)
            print dir(self.the_class)

    def run(self):
        """ The actual worker part of the thread. """
        self.oscServer.serve_forever()

    def defaultMessageHandler(self, addr, tags, data, client_address):
        """ Default handler for the OSCServer. """
        if debug:
            dbg = 'receveived : {addr} {data} (type={tags}) from {client_address}'
            print(dbg.format(addr=addr, data=data, tags=tags, client_address=client_address))
        addr = addr.split('/')
        new = ''
        for item in addr:
            if new != '':
                new = new + '_' + item
            else:
                new = item 
        if len(data) == 1:
            data = data[0]
        prop_list=[p for p in dir(self.the_class) if isinstance(getattr(self.the_class, p),property)]
        print new, prop_list
        if new in prop_list:
            print 'propery'
            setattr(self.parent, new)
        else:
            print 'method'
            meth = getattr(self.parent, new)
            print meth, data
            meth(data)


class OSCServer(object):
    """docstring for OSCServer"""
    def __init__(self, parent, port, name='no-name'):
        super(OSCServer, self).__init__()
        self.parent = parent
        self.port = port
        # Set up threads.
        self.threadLock = threading.Lock()
        self.serverThread = None

        # Start the server.
        self.__startServer__(parent)
        info = self.serverThread.oscServer.address()
        print('OSC Server started on %s:%i' % (info[0], info[1]))
        #self.zeroconf()
    
    
    def register_callback(self,sdRef, flags, errorCode, name, regtype, domain):
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            print ('Registered zeroconf service' , name , regtype , domain)

    def zeroconf(self):
        hostname = socket.gethostname()
        hostname = hostname.split('.local')[0]
        name = hostname + 'lekture'
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
        print('FORCE TO 127.0.0.2 because BUG')
        ipAddress = '127.0.0.1'
        return ipAddress

    def getDefaultPort(self):
        #Get the default port from the configuration file, or return 10000 if fail.
        if self.port:
            return self.port
        else:
            return 10000

    def __startServer__(self, parent):
        #Start the server.
        # Check to see if there is already a thread and server running:
        if self.serverThread:
            if not self.serverThread.is_alive():
                self.serverThread = ServerThread(self.parent, self.getDefaultIPAddress(), self.getDefaultPort())
        else:
            self.serverThread = ServerThread(self.parent, self.getDefaultIPAddress(),self.getDefaultPort())
        self.serverThread.start()

    def __stopServer__(self):
        #Stop the server.
        self.serverThread.oscServer.close()    
        zeroconf.sdRef.close()
