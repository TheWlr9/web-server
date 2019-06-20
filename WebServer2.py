#!/usr/bin/python

import sys
import os
import subprocess
import socket

PORT = 15010
address = ("", PORT) #"""" defaults to "this" machine's hostname
requestSocket, socketFile = None, None

mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print ""
print "Setting up socket"
mySocket.bind(address)
mySocket.listen(socket.SOMAXCONN)

def safeTerminateCon():
    global socketFile, requestSocket

    print ""
    print "Terminating connection gracefully"

    if socketFile is not None:
        print "Closing temp conn file"
        socketFile.close()
    if requestSocket is not None:
        print "Closing new socket"
        requestSocket.close()

def getResource(path, contentType):
    resource = None

    try:
        page = open(path, 'r')

        resource = "Content-Type: " + contentType + "\r\n\r\n"
        resource += page.read()
        page.close()
    except IOError:
        pass
    
    return resource

def handleReq(uri, body):
    print "Handling URI"

    data = None
    path, params = "", ""
    if "?" in uri:
        (path, params) = uri.split('?', 1)
    else:
        path = uri
    
    if params != "":
        os.environ['QUERY_STRING'] = params

    if path.endswith("/"):
        #Directory
        print "Directory"

        path += "index.html"
    
    if path.endswith(".cgi"):
        #Common gateway interface file
        print "CGI"

        try:
            tempFile = open(path, 'r')
            (head, shebang, shePath) = tempFile.readline().strip().partition("!")
            tempFile.close()

            dirPath = os.path.dirname(os.path.abspath(__file__))

            if body is None:
                #GET method
                procOut = subprocess.check_output([shePath, dirPath + '/' + path], cwd=dirPath)
            else:
                #POST method
                processObj = subprocess.Popen([shePath, dirPath + '/' + path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=dirPath)
                (procOut, procErr) = processObj.communicate(input=body)

            data = procOut
        except IOError:
            data = None
    elif path.endswith(".html"):
        #Hypertext markup language
        print "HTML"

        data = getResource(path, "text/html")
    elif path.endswith(".txt"):
        #Text
        print "Text"
        
        data = getResource(path, "text/plain")
    elif path.endswith(".csv"):
        #Comma separated values
        print "Comma separated values"
        
        data = getResource(path, "text/csv")
    elif path.endswith(".js"):
        #Javascript
        print "Javascript"
        
        data = getResource(path, "text/javascript")
    elif path.endswith(".json"):
        #Java structured object notation
        print "Java structured object notation"
        
        data = getResource(path, "application/json")
    else:
        #Assume static file
        print "Static file"

        data = getResource(path, "application/octet-stream")
    
    return data

try:
    while True:
	valid = True
        print ""
        print "Listening for connection..."
        requestSocket, addr = mySocket.accept()
	requestSocket.settimeout(1.0)
	
        print "Connection made with " + str(addr) + "!"

        #Get the request
	#This try-catch block handles weird glitch with duplicate HTTP requests
	try:
            req = requestSocket.recv(4096)
	except socket.timeout:
	    valid = False
	
	if valid:
            os.environ['REQUEST_METHOD'] = req.split(" ", 1)[0]
            
            if "\r\nCookie: " in req:
                os.environ['HTTP_COOKIE'] = req.split("\r\nCookie: ", 1)[1].split("\r\n", 1)[0]
    
            if os.environ['REQUEST_METHOD'] == "POST":
	        os.environ['CONTENT_LENGTH'] = str(len(req.split("\r\n\r\n", 1)[1].encode("utf-8")))
                resource = handleReq("./" + req.split('/', 1)[1].split(' ')[0], req.split("\r\n\r\n", 1)[1])
            else:
                resource = handleReq("./" + req.split('/', 1)[1].split(' ')[0], None)
    
            socketFile = requestSocket.makefile()
    
            print "Sending resource"
            if resource is not None:
                #Resource found
                socketFile.write("HTTP/1.0 200 OK\r\n")
                socketFile.write(resource)
            else:
                #Resource not found
                socketFile.write("HTTP/1.0 404 NOT FOUND\r\n")
                socketFile.write("\r\n")
                socketFile.write("Web page not found")
            
            socketFile.flush()
    
        safeTerminateCon()
except BaseException as exc:
    print ""
    print "ERROR"
    print str(exc)
finally:
    print ""
    print "Ending server"

    safeTerminateCon()

    if mySocket is not None:
        print "Closing connection listener"
        mySocket.close()
