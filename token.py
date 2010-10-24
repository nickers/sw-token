#!/usr/bin/env python
import pickle, sys, socket, time

PORT = 12351	# why not? :D
HOST = ''		# '' means "wait on all interfaces"
BUF_SIZE = 4096 # socket receive buffer in bytes
WAIT_TIME = 1.0 # in seconds


__author__ = 'nickers'

class Token(object):
	def __init__(self, c):
		self.color = c

class TokenACK(object):
	def __init__(self):
		None

class Node(object):
	def __init__(self, id, c, next):
		self.id = id
		self.token_in = Token(False)
		self.token_out = Token(c)
		self.receive_time = None
		self.next_timeout = time.time() + WAIT_TIME
		self.next_node = next

	def e_init(self):
		print "#%d: Init: in: %s, out: %s"%(self.id, self.token_in.color, self.token_out.color)

	def e_receive(self, msg):
		if msg.color!=self.token_in.color:
			print "#%d: received token with: '%s', actual '%s'"%(self.id, msg.color, self.token_out.color)
			self.token_in = msg
			self.token_out.color = not self.token_out.color

	def e_send(self, msg):
		self.next_timeout = time.time() + WAIT_TIME

		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		data = pickle.dumps(msg)
		print "#%d: sending %s to %s"%(self.id, msg.color, self.next_node)
		s.sendto(data, self.next_node)

	def e_timeout(self):
		self.e_send(self.token_out)


def main(id, port, next):
	node = Node(id, id==0, next)
	node.e_init()

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind((HOST, port))

	print "#%d: New client at %s" %(id,(HOST, port))

	while True:
		try:
			to = node.next_timeout
			if to!=None:
				to = max(0, to-time.time())
			s.settimeout(to)

			data = s.recv(BUF_SIZE)
			data = pickle.loads(data)
			node.e_receive(data)

			node.e_send(node.token_out)
		except socket.timeout:
			print "#%d: Timeout!"%id
			node.e_timeout()

if __name__=="__main__":
	if len(sys.argv)!=5:
		print "Usage:", sys.argv[0], " <node_id> <port> <next_host> <next_host_port>"
		sys.exit(-1)

	id = int(sys.argv[1])
	port = int(sys.argv[2])
	next_host = sys.argv[3]
	next_port = int(sys.argv[4])

	main(id, port, (next_host, next_port))
	print "#%d Finished"%id
