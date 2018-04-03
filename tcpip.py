import socket
import threading
from SMB_Cmd_handler import SmbCmd


class TcpServer(threading.Thread):
    def __init__(self, qcommand, qtransmit):
        self.qcmd = qcommand
        self.qxmit = qtransmit
        threading.Thread.__init__(self)

    def run(self):
        HOST = ''  # Symbolic name meaning all available interfaces
        PORT = 1024  # Arbitrary non-privileged port

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        smb_cmd = SmbCmd()
        while True:
            """ see if data recieved via TCP """
            data = conn.recv(1024)
            """ Convert byte data to string """
            strdata = "".join(map(chr, data))

            if data:
                """ add recived cmd to the transmit queue to be echoed back """
                if self.qxmit.empty() is not True:
                    output = strdata.rstrip() + '\n'
                    self.qxmit.put(output.encode('utf-8'))

                """ Parse command """
                cmd_dict = smb_cmd.parse_smb_cmd(strdata)

                """ Add command to the comand queue """
                if self.qcmd.full() is not True:
                    self.qcmd.put(cmd_dict)

            while self.qxmit.empty() is not True:
                """ Transmit any data in the transmit queue """
                if self.qxmit.empty() is not True:
                    data = self.qxmit.get()
                    self.qxmit.task_done()
                    conn.sendall(data)

        conn.close()
