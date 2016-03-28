#! /usr/bin/env python
# -*- coding: utf-8 -*-

import liblo

debug = True

class SpecialOscServer(liblo.Server):
    """docstring for OSCServer"""
    def __init__(self, port, parent):
        super(SpecialOscServer, self).__init__(port)
        self.parent = parent
        #self.daemon = True
        self.add_method(None, None, self.defaultMessageHandler)
        if debug:
            print('OSC Server started on port %i' % (self.port))
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
    
    def defaultMessageHandler(self, address, data, tags, client_address):
        """
        Default handler for the OSCServer.
        """
        client_address = client_address.hostname
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
            meth = getattr(self.parent, prop)
            if debug == 4:
                print('receive OSC -> method', prop)
            if data == []:
                # there is no arguments, so it's just a method to call
                meth()
            else:
                # this method has optional arguments, and some are presents. Please forward them
                meth(data)

    def answer(self, client_address, address, answer):
        if answer == True:
            answer = 1
        if answer == False:
            answer = 0
        target = liblo.Address(client_address, 33333)
        msg = liblo.Message(address)
        msg.add(answer)
        liblo.send(target, msg)


class OSCServer(object):
    """docstring for OSCServer"""
    def __init__(self, parent, port, name='no-name'):
        super(OSCServer, self).__init__()
        self.parent = parent
        self.port = port
        self.server = SpecialOscServer(self.getDefaultPort(), parent)

    def getDefaultPort(self):
        #Get the default port from the configuration file, or return 10000 if fail.
        if self.port:
            return self.port
        else:
            return 10000
