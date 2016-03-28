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
        # make a list of all properties of 'parent'
        prop_list = [p for p in dir(parent.__class__) if isinstance(getattr(parent.__class__, p),property)]
        if debug == 4:
            for prop in prop_list:
                prop = prop.split('_')
                new = ''
                for item in prop:
                    new = new + '/'  + item
                    prop = new
                print('register osc address :', prop)
        self.prop_list = prop_list

    def run(self):
        """ The actual worker part of the thread. """
        self.oscServer.serve_forever()

    def defaultMessageHandler(self, addr, tags, data, client_address):
        """
        Default handler for the OSCServer.
        """
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
        if new in self.prop_list:
            if debug:
                print('receive OSC -> property', new, data)
            setattr(self.parent, new, data)
        else:
            meth = getattr(self.parent, new)
            if debug:
                print('receive OSC -> method', new)
            if data == []:
                # there is no arguments, so it's just a method to call
                meth()
            else:
                # this method has optional arguments, and some are presents. Please forward them
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
            print('Registered zeroconf service' , name , regtype , domain)

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
            #ipAddress = socket.gethostbyname(socket.gethostname())
	    ipAddress = [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0]
        except :
            ipAddress = '127.0.0.1'
            if debug:
		print('FORCE TO 127.0.0.2 because BUG')
	if debug:
		print('ip address :', ipAddress)
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
