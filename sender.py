import sys
from logHandler import logHandler
import socket
import pickle
import threading
import time
import logging
import traceback


def ErrorLog(error: str):
    current_time = time.strftime("%Y.%m.%d/%H:%M:%S", time.localtime(time.time()))
    with open("re.txt", "w") as f:
        f.write(f"[{current_time}] - {error}\n") 

def receiveAck(s):   
    global packets
    global windowSize
    acks = dict()
    expected = 0
    while True:
        data, recvAddr = s.recvfrom(2048)
        pkt = pickle.loads(data)
        ack_num = pkt.get_seq()
        logProc.writeAck(ack_num,'received')
        if ack_num in acks.keys():
            acks[ack_num] += 1
        else:
            
            windowSize += 1
            if windowSize < len(packets):
                s.sendto(pickle.dumps(packets[windowSize]), recvAddr)
                logProc.writePkt(packets[windowSize].get_seq(), "sent")
            acks[ack_num] = 1
        if acks[ack_num] == 3:
            s.sendto(pickle.dumps(packets[ack_num+1]), recvAddr)
            logProc.writePkt(ack_num,'3 duplicated ACKs')
            logProc.writePkt(ack_num+1,'retransmitted')
            acks[ack_num] = 0
            
        if ack_num == len(packets)-1:
            break
        
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
        
def fileSender():
    print('sender program starts...')#remove this
    
    global windowSize
    throughput = 0.0
    avgRTT = 10.0
    logProc.startLogging(srcFilename + "_sending_log.txt")
    sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    sendSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sendSocket.bind(('', 0))
    addr = (recvAddr, 10080)
    ssize = 1024
    global packets
    packets = list()
    #file open
    try:
        file = open(srcFilename, 'rb')
    except:
        print('file not found')
        exit(1)
      
    #first packet = file name        
    pkt = packet(0,dstFilename.encode())
    packets.append(pkt)
    logProc.writePkt(0, pkt.get_seq())  
    #appending packets
    seq = 1
    #splitting into packets(1024)
    while True:
        data = file.read(ssize)
        if len(data) == 0:
            break
        pkt = packet(seq,data)
        packets.append(pkt)    
        seq += 1
    
    
    windowSize -= 1    
    thread = threading.Thread(target=receiveAck, args = (sendSocket, ))
    thread.start()
    
    #sending by packets
    for idx in range(windowSize+1):
        packets[idx].set_length(len(packets))
        sendSocket.sendto(pickle.dumps(packets[idx]), addr)
        logProc.writePkt(packets[idx].get_seq(), "sent")
        
    
        
    thread.join()
    logProc.writeEnd(throughput, avgRTT)
    sendSocket.close()
        
    

if __name__=='__main__':
    try:
        recvAddr = sys.argv[1]  #receiver IP address
        windowSize = int(sys.argv[2])   #window size
        srcFilename = sys.argv[3]   #source file name
        dstFilename = sys.argv[4]   #result file name
        logProc = logHandler()
        fileSender()
        
    except Exception:
        err = traceback.format_exc()
        ErrorLog(str(err))
