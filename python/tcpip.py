import logging
import queue
import socket
import select
import threading
from SMB_Cmd_handler import SmbCmd

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
        conn = None
        
        while True:
            sockets = [s]
            if conn is not None:
                sockets.append(conn)

            # self.logger.info('listening: %s', sockets)
            readable, writable, errored = select.select(sockets, [], [], 1.0)
                
            if s in readable:
                conn, addr = s.accept()
                self.logger.info('command connection from %s, %s' % (conn, addr))
                continue
                
            if conn in readable:
                data = conn.recv(1024)
                # Convert byte data to string
                data = data.decode('latin-1')
                
                if not data:
                    self.logger.warn('socket %s closed', conn)
                    conn = None
                    continue
                data = data.strip()
                if not data:
                    self.logger.warn('ignoring empty command')
                    continue
                    
                # add recived cmd to the transmit queue to be echoed back
                reply = data + '\n'
                # conn.sendall(reply.encode('latin-1'))
                self.__enqueue_cmd(data)

                try:
                    data = self.qxmit.get(block=True, timeout=3.0)
                except queue.Empty:
                    self.logger.warn('no reply to command!')
                    continue
                if data:
                    data = data + '\n'
                    conn.sendall(data.encode('latin-1'))

    def __enqueue_cmd(self, strdata):
        smb_cmd = SmbCmd(self.db)
        cmd_dict = smb_cmd.parse_smb_cmd(strdata)
        self.logger.info('cmd %s, %s' % (strdata, smb_cmd))
        if not self.qcmd.full():
            self.qcmd.put(cmd_dict)
