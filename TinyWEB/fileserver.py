import http.server
import socketserver
import os
import ifaddr
import tkinter
import tkinter.messagebox
import pyperclip
import winreg as reg 


import socket
import sys

  
def AddToRegistry():
    # in python __file__ is the instant of
    # file path where it was executed 
    # so if it was executed from desktop,
    # then __file__ will be 
    # c:\users\current_user\desktop
    pth = os.path.dirname(os.path.realpath(__file__))
      
    # name of the python file with extension
    s_name="fileserver.py"     
      
    # joins the file name to end of path address
    address=os.path.join(pth,s_name) 
      
    # key we want to change is HKEY_CURRENT_USER 
    # key value is Software\Microsoft\Windows\CurrentVersion\Run
    key = reg.HKEY_CURRENT_USER
    key_value = "Software\Microsoft\Windows\CurrentVersion\Run"
      
    # open the key to make changes to
    open = reg.OpenKey(key,key_value,0,reg.KEY_ALL_ACCESS)
    
    try:
        print (reg.QueryValueEx(open,"TinyMRP FileServer"))
    except:
        # modifiy the opened key
        reg.SetValueEx(open,"TinyMRP FileServer",0,reg.REG_SZ,address)
          
    # now close the opened key
    reg.CloseKey(open)
  


#To get the local ip to send out in  a message
def get_local_ip():
    adapters = ifaddr.get_adapters()
    
    for adapter in adapters:
        # print ("IPs of network adapter " + adapter.nice_name)
        for ip in adapter.ips:
            # print ("   %s/%s" % (ip.ip, ip.network_prefix))
            if "192.168" in ip.ip: return (ip.ip)



if __name__=="__main__":
    AddToRegistry()
    
    
#Configure the server
PORT = 8000
web_dir='W:/Solidworks/'    
serverurl=get_local_ip() + ":"+str(PORT)
    
#Copy the url to clipboard
pyperclip.copy(serverurl)
    
#Find and display the local ip of the server
root=tkinter.Tk()
root.withdraw()
tkinter.messagebox.showinfo('File web server',"Address copied to clipboard \n for server running in \n"+ serverurl)
root.destroy()
    
    
#Start the server
web_dir = os.path.join(os.path.dirname(__file__), web_dir)
os.chdir(web_dir)
handler = http.server.SimpleHTTPRequestHandler
handler.send_header("Access-Control-Allow-Origin", "*")
    
    with socketserver.TCPServer(("0.0.0.0", PORT), handler) as httpd:
        #print(serverurl) 
        #print("Server started at localhost:" + str(PORT))
        httpd.serve_forever()


class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_my_headers(self):
        #print("This is working :/")
        self.send_header("Access-Control-Allow-Origin", "*")
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def end_headers(self):
        self.send_my_headers()