#!/usr/bin/env python
import pickle, sys, socket, time

PORT = 12351	# why not? :D
HOST = ''		# '' means "wait on all interfaces"
BUF_SIZE = 4096 # socket receive buffer in bytes
WAIT_TIME = 1.0 # in seconds


__author__ = 'nickers'

class Token(object):
	def __init__(self, c, owner):
		self.color = c
		self.owner = owner

	def execute(self, node):
		if self.color!=node.token_in.color:
			print "#%d: received token with: '%s', actual '%s'"%(node.id, self.color, node.token_out.color)
			node.token_in = self
			node.token_out.color = not node.token_out.color
			node.ack_received = False

			self.__send_ack()
			return True
		return False

	def __send_ack(self):
		ack = TokenACK()
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		data = pickle.dumps(ack)
		print " @ACK to %s"%(self.owner,)
		s.sendto(data, self.owner)
		s.close()


class TokenACK(object):
	def __init__(self):
		None

	def execute(self, node):
		print " @ACK received"
		node.ack_received = True
		return False

class Node(object):
	def __init__(self, id, c, owner, next):
		self.id = id
		self.token_in = Token(False, owner)
		self.token_out = Token(c, owner)
		self.receive_time = None
		self.next_timeout = time.time() + WAIT_TIME
		self.next_node = next
		self.ack_received = False

	def e_init(self):
		print "#%d: Init: in: %s, out: %s"%(self.id, self.token_in.color, self.token_out.color)

	def e_receive(self, msg):
		return msg.execute(self)

	def e_send(self, msg):
		self.next_timeout = time.time() + WAIT_TIME

		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		data = pickle.dumps(msg)
		print "#%d: sending %s to %s"%(self.id, msg.color, self.next_node)
		s.sendto(data, self.next_node)
		s.close()


	def e_timeout(self):
		if not self.ack_received:
			self.e_send(self.token_out)
		self.next_timeout = time.time() + WAIT_TIME


def main(id, port, next):
	node = Node(id, id==0, (HOST, port), next)
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
			if node.e_receive(data):
				node.e_send(node.token_out)
		except socket.timeout:
			print "#%d: Timeout! ACK:%s"%(id, node.ack_received)
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
	print "#%d Finished!?"%id
