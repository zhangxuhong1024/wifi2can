#import esp
#esp.osdebug(None)

import machine
machine.freq(160000000)
del machine

import gc
gc.collect()

#import webrepl
#webrepl.start()

