import ssl
import socket
import struct
import email
import os.path

import transaction
import errors


class TaskdConnection(object):

    def __init__(self):
        self.port = 53589

    def from_taskrc(self):
        conf = dict([x.replace("\\/", "/").strip().split('=') for x in open(
            os.path.expanduser("~/.taskrc")).readlines() if '=' in x and x[0] != "#"])
        self.client_cert = conf['taskd.certificate']
        self.client_key = conf['taskd.key']
        self.server = conf['taskd.server'].split(":")[0]
        self.port = int(conf['taskd.server'].split(":")[1])
        self.cacert = conf['taskd.ca'] if 'taskd.ca' in conf else None
        self.group, self.username, self.uuid = conf['taskd.credentials'].split("/")

    def connect(self):
        c = ssl.create_default_context()
        c.load_cert_chain(self.client_cert, self.client_key)
        if self.cacert:
            c.load_verify_locations(self.cacert)
        # enable for non-selfsigned certs
        # print conn.getpeercert()
        c.check_hostname = False
        self.conn = c.wrap_socket(socket.socket(socket.AF_INET))
        self.conn.connect((self.server, self.port))

    def recv(self):
        a = self.conn.recv(4096)
        print struct.unpack('>L', a[:4])[0], "Byte Response"
        resp = email.message_from_string(a[4:])

        if 'code' in resp:
            # print errors.Status(resp['code'])
            if int(resp['code']) >= 400:
                raise errors.Error(resp['code'])
            if int(resp['code']) == 200:
                print "Status Good!"
        return resp

    def stats(self):
        msg = transaction.mk_message(self.group, self.username, self.uuid)
        msg['type'] = "statistics"
        self.conn.sendall(transaction.prep_message(msg))
        return self.recv()

    def pull(self):
        msg = transaction.mk_message(self.group, self.username, self.uuid)
        msg['type'] = "sync"
        self.conn.sendall(transaction.prep_message(msg))
        return self.recv()

def manual():
    # Task 2.3.0 doesn't let you have a cacert if you enable trust
    tc = TaskdConnection()
    tc.client_cert = "/home/jack/.task/jacklaxson.cert.pem"
    tc.client_key = "/home/jack/.task/jacklaxson.key.pem"
    tc.cacert = "/home/jack/.task/ca.cert.pem"
    tc.server = "192.168.1.110"
    tc.group = "Public"
    tc.username = "Jack Laxson"
    tc.uuid = "f60bfcb9-b7b8-4466-b4c1-7276b8afe609"
    return tc

# from IPython import embed
# embed()
if __name__ == '__main__':
    taskd = manual()
    taskd.connect()
    print taskd.pull()