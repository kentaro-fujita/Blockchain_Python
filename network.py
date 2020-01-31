import json
import socket
import pickle
import threading
import requests
import configparser

class Peers(object):
    def __init__(self):
        self.peers = {}
        self.id = 0
    
    def add(self, host, port):
        self.peers[self.id] = {"host": host, "port": port}
        self.id += 1
    
    def peers(self):
        return self.peers

class Sender(threading.Thread):
    def __init__(self, host, port, peers):
        threading.Thread.__init__(self, name="sender")
        self.host = host
        self.port = port
        self.peers = peers
        self.msgs = []
    
    def run(self):
        while True:
            if len(self.msgs) != 0:
              msg = self.msgs[0]
              for peer in self.peers:
                  host, port = peer.values()
                  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                      sock.settimeout(0.1)
                      try:
                          print("send : {}".format(msg))
                          sock.connect((host, port))
                          sock.sendall(msg.encode("utf-8"))
                          sock.shutdown(2)
                      except:
                          # print("disconnect",host)
                          pass
                      finally:
                          sock.close()
              self.msgs.remove(msg)
    
    def send_msg(self, msg):
        self.msgs.append(msg)

class Receiver(threading.Thread):
    def __init__(self, host, port, peers):
        threading.Thread.__init__(self, name="receiver")
        self.host = host
        self.port = port
        self.peers = peers
        self.BUFFER_SIZE = 4096
        self.msgs = []

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, self.port))
            sock.listen(20)
            while True:
                (conn, addr) = sock.accept()
                while True:
                    data = conn.recv(self.BUFFER_SIZE).decode('utf-8')
                    if data:
                        print('recieve : {}'.format(data))
                        self.msgs.append(data)
                    else:
                        break

class P2PNetwork(object):
    def __init__(self, offline=False, node_num=1):
        if offline:
            self.host, self.port, self.peers = self.set_peers(node_num)
        else:
            self.host, self.port, self.peers = self.get_peers()
        print({"host": self.host, "port": self.port})
        
        self.sender = Sender(self.host, self.port, self.peers)
        self.receiver = Receiver(self.host, self.port, self.peers)
        threads = [self.receiver.start(), self.sender.start()]
    
    def regist(self):
        config = configparser.ConfigParser()
        config.read('./config.ini','UTF-8')
        headers = {"content-type": "application/json"}
        url = "http://" + config.get('server', 'host') + ":" + \
        config.get('server', 'port') + "/cgi-bin/register_ip_addr.py"
        
        try:
            r = requests.get(url, headers=headers)
            return r
        except:
            print("Network Failure")

    def get_peers(self):
        config = configparser.ConfigParser()
        config.read('./config.ini', 'UTF-8')
        
        headers = {"content-type": "application/json"}
        url = "http://" + config.get('server', 'host') + ":" + \
        config.get('server', 'port') + "/cgi-bin/get_ip_addr.py"
        
        peers = Peers()

        host = socket.gethostbyname(socket.gethostname())
        port = int(config.get('settings', 'port'))
        
        ip_addrs = requests.get(url, headers=headers).json()
        [peers.add(ip_addr["ip_addr"], port) for ip_addr in ip_addrs if not host == ip_addr["ip_addr"]]

        return host, port, peers.peers.values()
    
    def set_peers(self, node_num):
        host = socket.gethostbyname(socket.gethostname())
        # port = int(config.get('settings', 'port'))
        # host = '163.221.126.155'
        port = int('888'+node_num)
        
        peers = []
        for i in range(1,3):
            if str(i) != node_num:
                peers.append({'host':host,'port':int('888'+str(i))})

        return host, port, peers