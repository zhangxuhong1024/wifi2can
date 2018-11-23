#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

#   import micropython
#   from micropython import const
#   @micropython.native
#   @micropython.viper   
#   加速效果不咋滴，不搞了。
#   XUHONG_20180915 
class CAN (object):
    def __init__(self, spi, cs):
        # 功能：MCP2515芯片初始化
        self.spi = spi
        self.cs = cs
        self._RxBuf = []

        self.cs.init(self.cs.OUT, value=1)
        try:
            master = self.spi.MASTER
        except AttributeError:
            # on ESP8266
            self.spi.init(baudrate=8000000, phase=0, polarity=0)
        else:
            # on pyboard
            self.spi.init(master, baudrate=8000000, phase=0, polarity=0)

        # 软件复位
        self._spi_Reset()
        # 能读到数据就认为是初始化没问题了。起码芯片给焊上去了。
        time.sleep(0.2)
        mode = self._spi_ReadReg(b'\x0E')
        if (mode == 0):
            raise OSError("MCP2515 init fail .")

    def SetINT(self, INT):
        pass #待补充。期待心情非常美好的那一天！

    def Stop(self):
        # 功能：停止MCP2515
        self._spi_WriteBit(b'\x0f',b'\xe0',b'\x20') # 休眠模式

    def Start(self, SpeedCfg, Filter=None, ListenOnly=False):
        # 功能：启动MCP2515
        # SpeedCfg：CAN通讯速率
        #   能支持的通讯速率，目前有如下：
        #   5K, 10K, 20K, 33K, 40K, 50K, 80K, 95K, 100K, 125K, 200K, 250K, 500K, 1000K
        #   对应的参数有效值为：
        #   5, 10, 20, 33, 40, 50, 80, 95, 100, 125, 200, 250, 500, 1000
        # Filter: 接收报文过滤模式
        #   待优化。
        # ListenOnly: 是否指定监听模式
        
        # 设置为配置模式
        self._spi_Reset()
        self._spi_WriteBit(b'\x0f',b'\xe0',b'\x80')
        # 设置通讯速率
        SpeedCfg_at_16M = { \
            1000: b'\x82\xD0\x00', \
            500 : b'\x86\xF0\x00', \
            250 : b'\x85\xF1\x41', \
            200 : b'\x87\xFA\x01', \
            125 : b'\x86\xF0\x03', \
            100 : b'\x87\xFA\x03', \
            95  : b'\x07\xAD\x03', \
            80  : b'\x87\xFF\x03', \
            50  : b'\x87\xFA\x07', \
            40  : b'\x87\xFF\x07', \
            33  : b'\x07\xBE\x09', \
            20  : b'\x87\xFF\x0F', \
            10  : b'\x87\xFF\x1F', \
            5   : b'\x87\xFF\x3F'  }
        cfg = SpeedCfg_at_16M.get(SpeedCfg,(b'\x00\x00\x00'))
        self._spi_WriteReg(b'\x28',cfg)
        del SpeedCfg_at_16M
        # 通道1报文过滤设置
        if (Filter==None):
            self._spi_WriteBit(b'\x60',b'\x64',b'\x64')
        else:
            self._spi_WriteBit(b'\x60',b'\x64',b'\x04')
            self._spi_WriteReg(b'\x00',Filter.get('F0'))
            self._spi_WriteReg(b'\x04',Filter.get('F1'))
            self._spi_WriteReg(b'\x20',Filter.get('M0'))
        # 禁用通道2报文接收
        self._spi_WriteBit(b'\x70',b'\x60',b'\x00')
        self._spi_WriteReg(b'\x08',b'\xff\xff\xff\xff')
        self._spi_WriteReg(b'\x10',b'\xff\xff\xff\xff')
        self._spi_WriteReg(b'\x14',b'\xff\xff\xff\xff')
        self._spi_WriteReg(b'\x18',b'\xff\xff\xff\xff')
        self._spi_WriteReg(b'\x24',b'\xff\xff\xff\xff')
        # 设置为正常模式或监听模式
        mode = b'\x00' if (ListenOnly==False) else b'\x60'
        self._spi_WriteBit(b'\x0f',b'\xe0', mode)

    def Send_msg(self, msg, sendchangel=None):
        # 功能：发送报文。
        # msg：
        #   msg['id']   :待发送报文的ID
        #   msg['ext']  :待发送报文是否是扩展帧
        #   msg['data'] :待发送报文的数据
        #   msg['dlc']  :待发送报文的长度
        #   msg['rtr']  :待发送报文是否是远程帧
        # sendchangel：
        #   指定发送报文的通道。有效值如下：
        #       0 :  通道0
        #       1 :  通道1
        #       2 :  通道2
        #   MCP2515提供三个发送通道，默认使用通道0。后续再实现自动寻找空闲通道，敬请期待。
        # 注意：若通道中存在待发送报文，则会停止此前的报文发送。
        #       然后用新报文替换，并再次进入待发送状态。
        if sendchangel==None:
            sendchangel = 0
        self._MsgVerificationCheck(msg) # msg check.
        # 停止此前寄存器里的报文发送
        ctl = (((sendchangel%3)+3)<<4).to_bytes(1,'big')
        self._spi_WriteBit(ctl,b'\x08',b'\x00')
        # 数据规整
        self.TxBuf = bytearray(13)
        if msg.get('ext'):
            self.TxBuf[0] = ((msg.get('id')) >> 21) & 0xFF
            id_buf  = ((msg.get('id')) >> 13) & 0xE0
            id_buf |= 0x08
            id_buf |= ((msg.get('id')) >> 16) & 0x03
            self.TxBuf[1] = id_buf
            self.TxBuf[2] = ((msg.get('id')) >> 8) & 0xFF
            self.TxBuf[3] = (msg.get('id')) & 0xFF
            if msg.get('rtr'):
                self.TxBuf[4] |= 0x40
        else:
            self.TxBuf[0] = ((msg.get('id')) >> 3) & 0xFF
            self.TxBuf[1] = ((msg.get('id')) << 5) & 0xE0
            if msg.get('rtr'):
                self.TxBuf[1] |= 0x10
        if msg.get('rtr')==False:
            self.TxBuf[4] |= msg.get('dlc') & 0x0F
            self.TxBuf[5:13] = msg.get('data')[:msg.get('dlc')]
        # 数据装载
        dat = ((((sendchangel%3)+3)<<4)+1).to_bytes(1,'big')
        self._spi_WriteReg(dat,self.TxBuf)
        # 发送
        self._spi_SendMsg(1<<sendchangel) # self._spi_WriteBit(ctl,b'\x08',b'\x08')

    def Recv_msg(self):
        # 功能：查询MCP2515是否有收到报文。若有则存入Buf。即调用了CheckRx。
        #       查询Buf是否有报文。若有，返回最早接收的一帧报文，否则返回None。
        # 返回Msg说明：
        #       msg['tm']    :接收报文的时间。Timer started at power on. unit=1ms。
        #       msg['id']    :接收的报文ID
        #       msg['ext']   :接收的报文是否是扩展帧
        #       msg['data']  :接收的报文数据
        #       msg['dlc']   :接收的报文长度
        #       msg['rtr']   :接收的报文是否是远程帧
        # 注意：每次仅仅返回一帧报文，一帧！
        self.CheckRx()
        if len(self._RxBuf) == 0: 
            return None
        dat = self._RxBuf.pop(0)
        msg = {}
        msg['tm'] = int.from_bytes(dat[-8:],'big')
        msg['dlc'] = int.from_bytes(dat[4:5],'big') & 0x0F
        msg['data'] = dat[5:13]
        ide = (int.from_bytes(dat[1:2],'big')>>3) & 0x01 # 0:标准帧  1:扩展帧
        msg['ext'] = True if ide==1 else False
        id_s0_s10 = int.from_bytes(dat[:2],'big') >> 5
        id_e16_e17 = int.from_bytes(dat[:2],'big') & 0x03
        id_e0_e15 = int.from_bytes(dat[2:4],'big')
        if msg['ext']:
            msg['id'] = (id_s0_s10<<18) + (id_e16_e17<<16) + id_e0_e15
            msg['rtr'] = True if (int.from_bytes(dat[4:5],'big') & 0x40)  else False
        else:
            msg['id'] = id_s0_s10
            msg['rtr'] = True if (int.from_bytes(dat[1:2],'big') & 0x10) else False
        return msg

    def CheckRx(self):
        # 功能：查询MCP2515是否有收到报文。若有，存入Buf并返回TRUE，否则返回False。
        # 注意：若不能及时将MCP内的报文存入Buf，可能会导致MCP无法接收新的报文。
        #       也就是说，可能会报文丢失。
        #       所以，尽量多调用此函数咯~~
        rx_flag = int.from_bytes(self._spi_ReadStatus(),'big')
        if (rx_flag&0x01):
            dat = self._spi_RecvMsg(0)
            tm = (time.ticks_ms()).to_bytes(8,'big')
            self._RxBuf.append(dat+tm)
        if (rx_flag&0x02):
            dat = self._spi_RecvMsg(1)
            tm = (time.ticks_ms()).to_bytes(8,'big')
            self._RxBuf.append(dat+tm)
        return True if (rx_flag&0b11000000) else False

    def Pin_RXxBF_as_Output(self, pin, value=None):
        # 功能：设置或获取RXxBF端口的输出状态。
        # pin：被设置的端口
        # value：
        #     空：返回端口的状态。1--高电平  0--低电平
        #     0 ：设置端口为低电平
        #     1 ：设置端口为高电平
        #     其他：无效
        # 注意：调用此方法后，即使原先此端口是否为接收报文中断模式，都会把端口设置为输出。
        self._spi_WriteBit(b'\x0c',b'\x0F',b'\x0C')
        if value==None:
            reg = self._spi_ReadReg(b'\x0c')
            v = int.from_bytes(reg,'big') & {0:0x10,1:0x20}.get(pin,0x00)
            return 1 if (v!=0) else 0
        p = {0:b'\x10', 1:b'\x20'}.get(pin,b'\x00')
        v = {'H':b'\x30', 'L':b'\x00'}.get(value,b'\x00')
        self._spi_WriteBit(b'\x0c',p,v)

    def Pin_TXxRTS_as_Input(self, pin):
        # 功能：设置并获取TXxRTS端口的输出状态。
        # pin：被设置的端口
        # value：
        #     空：返回端口的状态。1--高电平  0--低电平
        #     其他：无效
        # 注意：调用此方法后，即使原先此端口是否为发送报文中断模式，都会把端口设置为输入。
        p = {2:0x20, 1:0x10, 0:0x08}.get(pin) #端口无效咧？ 不管不顾咯！
        rst = self._spi_ReadReg(b'\x0d')
        return 1 if ((rst[0]&p) != 0) else 0

    def _MsgVerificationCheck(self, msg):
        # 功能：检查msg内容，是否为符合发送要求的CAN数据格式。
        #       若msg不符合格式，则抛出异常。
        if not (isinstance(msg.get('ext'),bool)):
            raise Exception('Msg格式错误：ext标识不是bool类型.')
        if not (isinstance(msg.get('id'),int)):
            raise Exception('Msg格式错误：id不是int类型.')
        if not (isinstance(msg.get('data'),bytes)):
            raise Exception('Msg格式错误：data不是bytes类型.')
        if not (isinstance(msg.get('dlc'),int)):
            raise Exception('Msg格式错误：dlc不是int类型.')
        if not (isinstance(msg.get('rtr'),bool)):
            raise Exception('Msg格式错误：rtr不是bool类型.')
        if ((msg.get('ext') == False) and (msg.get('id') > 0x7ff)):
            raise Exception('Msg格式错误：id超出标准帧最大值.')
        if ((msg.get('ext') == True) and (msg.get('id') > 0x1fffffff)):
            raise Exception('Msg格式错误：id超出扩展帧最大值.')
        if (len(msg.get('data', b'')) < msg.get('dlc')): 
            raise Exception('Msg格式错误：data比dlc定义的长度短.')
        if (msg.get('dlc') > 8): 
            raise Exception('Msg格式错误：dlc长度不能大于8.')

    def _spi_Reset(self):
        # 功能：MCP2515_SPI指令 - 复位
        self.cs.off()
        self.spi.write(b'\xc0')
        self.cs.on()
    
    def _spi_WriteReg(self, addr, value):
        # 功能：MCP2515_SPI指令 - 写寄存器
        self.cs.off()
        self.cs.off()
        self.spi.write(b'\x02')
        self.spi.write(addr)
        self.spi.write(value)
        self.cs.on()

    def _spi_ReadReg(self, addr, num=1):
        # 功能：MCP2515_SPI指令 - 读寄存器
        self.cs.off()
        self.spi.write(b'\x03')
        self.spi.write(addr)
        buf = self.spi.read(num)
        self.cs.on()
        return buf

    def _spi_WriteBit(self,addr, mask, value):
        # 功能：MCP2515_SPI指令 - 位修改
        self.cs.off()
        self.spi.write(b'\x05')
        self.spi.write(addr)
        self.spi.write(mask)
        self.spi.write(value)
        self.cs.on()

    def _spi_ReadStatus(self):
        # 功能：MCP2515_SPI指令 - 读状态
        self.cs.off()
        self.spi.write(b'\xa0')
        buf = self.spi.read(1)
        self.cs.on()
        return buf

    def _spi_RecvMsg(self, select):
        # 功能：MCP2515_SPI指令 - 读Rx缓冲区
        self.cs.off()
        if select==0:
            self.spi.write(b'\x90')
            buf = self.spi.read(13)
        if select==1:
            self.spi.write(b'\x94')
            buf = self.spi.read(13)
        self.cs.on()
        return buf

    def _spi_SendMsg(self, select):
        # 功能：MCP2515_SPI指令 - 请求发送报文
        self.cs.off()
        self.spi.write((0x80+(select&0x07)).to_bytes(1,'big'))
        self.cs.on()
