#! /usr/bin/env python
# -*- coding: utf-8 -*-

from liblo import *
import liblo
import sys

debug = True


class OSCServer(object):
    """
    This is the class you instanciate to create a server
    If you specify the word "thread", you will create a thread server
    r"""
    def __init__(self, parent, port, name='no-name', threading=False):
        super(OSCServer, self).__init__()
        self.parent = parent
        self.port = port
        self.name = name
        if threading == False:
            self.server = liblo.Server(self.getDefaultPort())
        else:
            self.server = ServerThread(self.getDefaultPort())
            self.server.start()
        if debug:
            print('OSC Server started on port %i' % (self.port))
        # add the default method for catching everything
        self.server.add_method(None, None, self.defaultMessageHandler)
        # make a list of all properties of 'parent'
        prop_list = [p for p in dir(parent.__class__) if isinstance(getattr(parent.__class__, p), property)]
        if debug == 1:
            for prop in prop_list:
                prop = prop.split('_')
                new = ''
                for item in prop:
                    new = new + '/'  + item
                    prop = new
                print('register osc address :' + str(prop))
        self.prop_list = prop_list

    def getDefaultPort(self):
        #Get the default port from the configuration file, or return 10000 if fail.
        if self.port:
            return self.port
        else:
            return 10000

    def defaultMessageHandler(self, address, data, tags, client_address):
        """
        Default handler for the OSCServer.
        """
        client_address = client_address.hostname
        if address == '/ping':
            self.answer(client_address, '/ping', True, 44444)
        else:
            if debug:
                dbg = 'receveived : {address} {data} (type={tags}) from {client_address}'
                print(dbg.format(address=address, data=data, tags=tags, client_address=client_address))
            addr = address.split('/')
            prop = ''
            for item in addr:
                if prop != '':
                    prop = prop + '_' + item
                else:
                    prop = item 
            if prop in self.prop_list:
                if isinstance(data, list):
                    if len(data) == 0:
                        # this is a query
                        answer = getattr(self.parent, prop)
                        self.answer(client_address, address, answer)
                    else:
                        if len(data) == 1:
                            data = data[0]
                        # this is setter
                        if debug == 4:
                            print('receive OSC -> property', prop, data)
                        setattr(self.parent, prop, data)
            else:
                if len(data) == 1:
                    data = data[0]
                try:
                    meth = getattr(self.parent, prop)
                    if debug == 4:
                        print('receive OSC -> method', prop)
                    if data == []:
                        # there is no arguments, so it's just a method to call
                        meth()
                    else:
                        # this method has optional arguments, and some are presents. Please forward them
                        meth(data)
                except AttributeError:
                    dbg = 'ERROR 111 - Invalid Method : {prop}'
                    print(dbg.format(prop=prop))

    def answer(self, client_address, address, answer, port=33333):
        if answer == True:
            answer = 1
        if answer == False:
            answer = 0
        target = liblo.Address(client_address, port)
        msg = liblo.Message(address)
        msg.add(answer)
        liblo.send(target, msg)
