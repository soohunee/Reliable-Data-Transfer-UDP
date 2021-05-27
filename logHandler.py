from multiprocessing import Process, Queue, Event
from queue import Empty
from time import time, sleep

def logFileWorker(q, e, filename):
    logFile = open(filename, 'w')

    while True:
        if e.is_set() and q.empty():
            break

        try:
            logFile.write(q.get(timeout=5))
        except Empty:
            sleep(0.1)

    logFile.close()
    return 0


class logHandler:
    def __init__(self):
        self.startflag = False
        self.logQueue = Queue()
        self.endEvent = Event()
        

    def startLogging(self, filename):
        self.filename = filename
        self.loggingProc = Process(target=logFileWorker, args=(self.logQueue, self.endEvent, self.filename))
        self.loggingProc.start()
        self.startTime = time()
        self.startflag = True
    
    def writePkt(self, pktNum, event):
        if self.startflag:
            strToWrite = '{:1.3f} pkt: {} | {}\n'.format(time()-self.startTime, pktNum, event)
            self.logQueue.put(strToWrite)
        else:
            print("WARNING : logging has not been started!")

    def writeAck(self, ackNum, event):
        if self.startflag:
            strToWrite = '{:1.3f} ACK: {} | {}\n'.format(time()-self.startTime, ackNum, event)
            self.logQueue.put(strToWrite)
        else:
            print("WARNING : logging has not been started!")

    def writeEnd(self, throughput, avgRTT=-1):
        if self.startflag:
            self.logQueue.put('File transfer is finished.\n')
            self.logQueue.put('Throughput : {:.2f} pkts/sec\n'.format(throughput))
            if avgRTT!=-1:
                self.logQueue.put('Average RTT : {:.1f} ms\n'.format(avgRTT))
            self.endEvent.set()
            self.loggingProc.join()
        else:
            print("WARNING : logging has not been started!")
