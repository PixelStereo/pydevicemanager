import OSC
import sys

# PREPARE TO SEND MESSAGES TO MILLUMIN
# BE SURE OSC IS ACTIVATED IN MILLUMIN : from the menubar, click on 'Devices' then 'Setup OSC...'
oscClient = OSC.OSCClient()
oscClient.connect(  ('127.0.0.1',5000)  )

# EXECUTE OSC
msg = OSC.OSCMessage('/millumin/action/launchColumn')
data = float(2)
msg.append(data)
oscClient.send(msg)