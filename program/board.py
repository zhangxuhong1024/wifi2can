can = None

def init():
    try:
        global can
        import mcp2515
        from machine import SPI
        from machine import Pin
        can = mcp2515.CAN(SPI(1), cs=Pin(5))
        print ('MCP2515 init OK !')
    except Exception as e:
        raise e
    try:
        import os
        import sdcard as SD
        sd = SD.SDCard(SPI(1), Pin(16))
        os.umount('/')
        os.mount(sd, '/')
        print ('SDcard init OK !')
    except Exception as e:
        print ('SDcard init FAILURE !')
def ai():
#    ''' 
#        返回Ai的电压值。
#        注意：Ai测量范围是：0~18V。过压会烧板，没加足够的保护哦！
#        '''
    from machine import ADC
    adc = ADC(0).read()
    adc = adc / 1024 * 21    #10位AD精度，采样电阻与分压电阻比例是 1::20
    adc = adc * 0.98 - 0.02  #简单的修正
    return adc if (adc > 0.05) else 0

def cp(pwm=None):
#    '''
#        无参数：返回继电器状态的电压值。
#        pwm：设置CP的占空比值。 0~100 
#        '''
    from machine import Pin
    from machine import PWM
    cp = PWM(Pin(0)) 
    cp.freq(1000)
    if pwm!=None: 
        cp.duty(int((100-pwm)/100*1024))
    else:
        return int(100 - (cp.duty() * 100 / 1024))

def relay(status=None):
#     '''
#         无参数：返回继电器状态的电压值。
#         status=0：断开继电器。
#         status=1：吸合继电器。
# '''
    from machine import Pin
    relay = Pin(15,Pin.OUT)
    if status==None: 
        return relay.value()
    elif status == 0:
        relay.off()
    else:
        relay.on()

def led_sys(status=None):
#''' 
#         无参数：返回LED状态的电压值。
#         status=0：LED灭
#         status=1：LED亮
# '''
    from machine import Pin
    led = Pin(2,Pin.OUT)
    if status==None: 
        return led.value()
    elif status == 0:
        led.on()   #LED灭
    else:
        led.off()  #LED亮

def led_dat(status=None):
#''' 
#         无参数：返回LED状态的电压值。
#         status=0：LED灭
#         status=1：LED亮
# '''
    global can
    if can==None: 
        raise Exception('Please call init() before use this funtion.') 
    if status==None: 
        return can.Pin_RXxBF_as_Output(0)
    can.Pin_RXxBF_as_Output(0, {1:'H',0:'L'}.get(status,'L'))

def led_err(status=None):
#''' 
#         无参数：返回LED状态的电压值。
#         status=0：LED灭
#         status=1：LED亮
# '''
    global can
    if can==None: 
        raise Exception('Please call init() before use this funtion.') 
    if status==None: 
        return can.Pin_RXxBF_as_Output(1)
    can.Pin_RXxBF_as_Output(1, {1:'H',0:'L'}.get(status,'L'))

def wifi(en=None,essid=None,password=None):
#''' 
#         en=None : 返回AP状态
#         en=True : 设置AP为启用状态
#         en=False: 设置AP为关闭状态态
#         essid    : AP配置，热点名称：
#         password : AP配置，热点密码：
# '''
    import network
    ap = network.WLAN(network.AP_IF)
    if en==None and essid==None and password==None:
        if not ap.active():
            return None
        else:
            return ap.ifconfig()
    if en==True:
        ap.active(True)
    elif en==False:
        ap.active(False)
    if not essid==None:
        if not ap.active():
            raise Exception('Please active the AP first.')
        ap.config(essid=essid)
    if not password==None:
        if not ap.active():
            raise Exception('Please active the AP first.')
        ap.config(password=password)
    

def web(en=None):
    import web
    if en==True:
        web.Start()
    elif en==False:
        web.Stop()
