#!/usr/bin/python

import jenkins

l_jenkins = jenkins.Jenkins("http://localhost:8080/")

if l_jenkins.node_exists("test"):
    print "Node exists"
    l_jenkins.delete_node("test")
else:
	print "Node does not exist"
    
l_jenkins.create_node("test",4,"Test",labels="nothing")

if l_jenkins.node_exists("test"):
	print "Node exists"
else:
	print "Node does not exist"

if l_jenkins.node_exists("negtest"):
    print "Node exists"
else:
    print "Node does not exist"
    
#l_jenkins.delete_node("test")
