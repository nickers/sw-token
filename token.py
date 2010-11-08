#!/usr/bin/env python
import pickle, sys, socket, time, random

PORT = 12351	# why not? :D
HOST = ''		# '' means "wait on all interfaces"
BUF_SIZE = 4096 # socket receive buffer in bytes
WAIT_TIME = 1.0 # in seconds


__author__ = 'nickers'

def ring_send(msg, destination):
	"""
		Pack & send message to ring.
	"""
	if random.randint(1,100)>20:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setblocking(0)
		data = pickle.dumps(msg)
		sock.sendto(data, destination)
		sock.close()
	else:
		print "!"


class Token(object):
	def __init__(self, c, owner, sender_id):
		self.color = c
		self.owner = owner
		self.sender_id = sender_id

	def execute(self, node):
		if self.color!=node.token_in.color:
			print " -- received token #%d, c:%s, out:%s"%(node.id, self.color, node.token_out.color)
			node.token_in = self
			node.token_out.color = not node.token_out.color
			node.ack_received = False

			self.__send_ack(node.next_node)
			return True
		return False

	def __send_ack(self, next_node):
		print "  +- sending ACK to %s"%(next_node,)
		ack = TokenACK(self.color, self.owner, self.sender_id)
		ring_send(ack, next_node)


class TokenACK(Token):
	def __init__(self, c, owner, sender_id):
		super(TokenACK,self).__init__(c,owner,0)
		self.sender_id = sender_id

	def execute(self, node):
		if node.id==self.sender_id:
			if self.color==node.token_out.color:
				print " -- received ACK : %s"%self.color
				node.ack_received = True
				return False
			else:
				print "! ACK with invalid color!"
			return True
		else:
			# todo i should send this to next hop
			## print "# I Should send this further:(c:%s,dst:%s)"%(self.color,self.sender_id)
#			print "@ack resending"
			ring_send(self, node.next_node)
		return True


class Node(object):
	def __init__(self, id, c, owner, next):
		self.id = id
		self.token_in = Token(False, owner, self.id)
		self.token_out = Token(c, owner, self.id)
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

#		print " -- sending token src:#%d, c:%s, dest:%s"%(self.id, msg.color, self.next_node)
		ring_send(msg, self.next_node)


	def e_timeout(self):
		if not self.ack_received:
			self.e_send(self.token_out)
		self.next_timeout = time.time() + WAIT_TIME




def main(id, port, next):
	node = Node(id, id==0, (HOST, port), next)
	node.e_init()

	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.bind((HOST, port))
	s.setblocking(1)

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
				print " $token step"
				node.e_send(node.token_out)
		except:
			print " -- timeout: #%d: ack_state:%s"%(id, node.ack_received)
			node.e_timeout()
#		except socket.error:
#			None #print " ~~ socket error, skipping..."

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
