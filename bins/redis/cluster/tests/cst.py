#!/usr/bin/python

from redis.sentinel import Sentinel
sentinel = Sentinel([('localhost', 16001), ("localhost", 16002), ("localhost", 16003)], socket_timeout=0.1)
master = sentinel.discover_master('redis-cluster')
slaves = sentinel.discover_slaves('redis-cluster')

print ""
print "Master(" + str(master) + ")"
print ""
print "Slaves(" + str(len(slaves)) + ") Nodes(" + str(slaves) + ")"
print ""
