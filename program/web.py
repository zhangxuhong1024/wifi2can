import socket
from machine import Timer

_skt = None
_timer = None

def Start(addr=None):
    global _skt
    global _timer
    if addr == None:
        addr=('192.168.4.1',80)
    try: 
        _skt = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        _skt.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        _skt.setblocking(False)
        _skt.bind(addr)
        _skt.listen(1)
    except Exception as e:
        print('wa ...\r\n')
    try: 
        if _timer==None:
            _timer = Timer(-1)
            s = _WebServer()
            _timer.init(period=100, mode=Timer.PERIODIC, callback=next(s))
    except Exception as e:
        print('wa ...\r\n')

def Stop():
    if not _timer:
        _timer.deinit()

def _WebServer(argv):
    conn = None
    request = None
    while True:
        try:
            yield
            conn,_ = _skt.accept()
            break # 能执行到这里，那就是已经建立socket了。
        except Exception as e:
            pass
    while True:
        try:
            yield
            request = conn.recv(256)
            break
        except Exception as e:
            pass
    while True:
        try:
            rst = _msg_head + 'abc12345678' + '\r\n\r\n'
            conn.sendall(rst.encode())#发送中途,发生了异常，咋办？
            break
        except Exception as e:
            pass
    try:
        yield
        conn.close()
    finally:
        return

_msg_head = 'HTTP/1.1 200 CP{}CP_AI{}AI\r\nContent-Type:text/html\r\n\r\n'
_index_html = '''
<!DOCTYPE html>
<html lang="en-us">
<head>
<meta charset="UTF-8">
<meta name="renderer" content="webkit">
<meta http-equiv="Content-Type" content="multipart/form-data; charset=utf-8" />
<meta name="viewport" content="width=device-width, user-scalable=no, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0">
<title>Web Control</title>
<style type="text/css" id="style">
    .b{
        width: 50px;
        height: 25px;
    }
</style>
</head>
<body>
    <h1>Web Control</h1>
    <div>
        CP (%) :
        <input class="b" id="cpval" type="text" value=123 maxlength=3 ></input>
        <input class="b" id="cpset" type="button" value=设置></input>
    </div>
    <div>
        Realy :
        <input class="b" id="relayClone" type="button" value=闭合></input>
        <input class="b" id="relayOpen"  type="button" value=断开></input>
    </div>
    <div>
        Ai (v) :
        <input class="b" id="aival" type="text" disabled=ture value="0xff" ></input>
    </div>
</body>
<script>
function transfer(msg) 
{
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = () => 
    {
        if (xhr.status == 200 && xhr.readyState == 4)
        {
            // update all value.
            cpval.value = xhr.statusText.match(/CP.*CP/)[0].slice(2,-2)
            aival.value = xhr.statusText.match(/AI.*AI/)[0].slice(2,-2)
        }
    }
    xhr.open('GET', msg, true);
    xhr.send()
}
var cpval      = document.getElementById('cpval')
var cpset      = document.getElementById('cpset')
var relayClone = document.getElementById('relayClone')
var relayOpen  = document.getElementById('relayOpen')
var aival      = document.getElementById('aival')
cpset.onclick = function(event) 
{
    transfer('WebCtrl_SET_CP_' + cpval.value)
}
relayOpen.onclick = function(event) 
{
    transfer('WebCtrl_SET_RELAY_0')
}
relayClone.onclick = function(event) 
{
    transfer('WebCtrl_SET_RELAY_1')
}
function reflesh ()
{
    transfer('WebCtrl_REFLESH')
}
setInterval(reflesh,3000);
</script>
</html>
\r\n\r\n
'''
