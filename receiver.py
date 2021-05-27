import sys
from logHandler import logHandler
import socket
import pickle
import time
import logging
import traceback


def ErrorLog(error: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("re.txt", "a") as f:
        f.write(f"[{current_time}] - {error}\n") 

class packet:
    def __init__(self, seq, data):
        self.seq = seq
        self.data = data
        self.sent_time = time.time()
        self.length = 0
        
    def get_seq(self):
        return self.seq
    def get_data(self):
        return self.data
    def get_sent_time(self):
        return self.sent_time
    def get_length(self):
        return self.length
    def set_length(self, length):
        self.length = length
        
def buffer_arrange():
    global expected
    global dstFile
    global count
    while True:
        flag = True
        if len(temp_buffer) == 0:
            break
        else:
            idx = 0
            for i in range(len(temp_buffer)):
                seq=temp_buffer[idx].get_seq()
                data=temp_buffer[idx].get_data()
                if seq == expected:
                    dstFile.write(data)
                    count += 1
                    expected += 1
                    del temp_buffer[idx]
                    idx -= 1
                    flag = False
                idx += 1
                
            if flag == True:
                break
                
def fileReceiver():
    print('receiver program starts...')
    
    recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    addr = ("", 10080)
    recvSocket.bind(addr)
    rsize = 2048
    global expected
    global dstFile
    global count
    #receiving by packets
    count = 0
    while True:
        data, senderAddr = recvSocket.recvfrom(rsize)
        pkt = pickle.loads(data)
        seq = pkt.get_seq()
        data = pkt.get_data()
        length = pkt.get_length()
        logProc.writePkt(seq, 'received')
        
        if seq == 0:
            file_name = data.decode()
            dstFile = open(file_name,'wb')
            count += 1
            logProc.startLogging(file_name+ "_receiving_log.txt")
            expected += 1
            temp = packet(seq, None)
            recvSocket.sendto(pickle.dumps(temp), senderAddr)
            logProc.writeAck(seq, 'sent')
        else:
            if seq == expected:
                dstFile.write(data)
                count += 1
                expected += 1
                
                if len(temp_buffer) > 0:
                    buffer_arrange()
                    temp = packet(expected-1, None)
                    recvSocket.sendto(pickle.dumps(temp), senderAddr)
                    logProc.writeAck(expected-1, 'sent')
                else:
                    temp = packet(seq, None)
                    recvSocket.sendto(pickle.dumps(temp), senderAddr)
                    logProc.writeAck(seq, 'sent')
            else:
                temp_buffer.append(pkt)
                temp = packet(expected-1, None)
                recvSocket.sendto(pickle.dumps(temp), senderAddr)
                logProc.writeAck(expected-1, 'sent')
                
        if count == length:
            break
    
    logProc.writeEnd(throughput)
    recvSocket.close()

if __name__=='__main__':
    try:
        throughput = 0.0
        expected = 0
        dstFile = None
        temp_buffer = list()
        logProc = logHandler()
        fileReceiver()
    
    except Exception:
        err = traceback.format_exc()
        ErrorLog(str(err))
