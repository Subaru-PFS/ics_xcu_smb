import logging
import socket
import threading
from SMB_Cmd_handler import SmbCmd
import time

class TcpServer(threading.Thread):
    def __init__(self,smbdb, qcommand, qtransmit):
        self.logger = logging.getLogger('smb')
        
        self.db = smbdb
        self.qcmd = qcommand
        self.qxmit = qtransmit
        threading.Thread.__init__(self)

    def run(self):
        host = ''  # Symbolic name meaning all available interfaces
        port = 1024  # Arbitrary non-privileged port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(2)
        conn, addr = s.accept()
        self.logger.info('command connection from %s, %s' % (conn, addr))
        
        while True:
            # See if data recieved via TCP.
            time.sleep(.1)
            data = conn.recv(1024)
            # Convert byte data to string
            strdata = "".join(map(chr, data))

            if data:
                # add recived cmd to the transmit queue to be echoed back

                # if not self.qxmit.full():
                #     output = strdata.rstrip() + '\n'
                #     self.qxmit.put(output.encode('utf-8'))

                self.__enqueue_cmd(strdata)

            # Transmit any data in the transmit queue
            try:
                data = self.qxmit.get(block=True)
                if data:
                    self.qxmit.task_done()
                    conn.sendall(data)
            except ValueError as err:
                print(err)

        conn.close()

    def __enqueue_cmd(self, strdata):
        smb_cmd = SmbCmd(self.db)
        cmd_dict = smb_cmd.parse_smb_cmd(strdata)
        self.logger.info('cmd %s, %s' % (strdata, smb_cmd))
        if not self.qcmd.full():
            self.qcmd.put(cmd_dict)
