import board

board.cp(20)
board.led_sys(1)

def test():
    import time
    board.init()
    board.can.Start(250)
    msg = {'ext':True,  \
        'id':0x18ff50e5, \
        'data':b'\x12\x34\x56\x78\x90\xab\xcd\xef', \
        'dlc':8,\
        'rtr':False}
    while(True):
        board.can.Send_msg(msg)
        board.led_dat(1)
        board.led_err(0)
        time.sleep(0.1)
        board.led_dat(0)
        board.led_err(1)
        time.sleep(0.9)

#while (True):
#    if board.ai()>1.5:
#        test()

