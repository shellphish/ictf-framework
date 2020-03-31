
port_setter = "-A FORWARD -s 172.31.128.0/19 -p tcp -m tcp --dport {} -m state --state NEW -m recent " + \
                " --set --name {} --mask 255.255.255.255 --rsource "

port_counter = "-A FORWARD -s 172.31.128.0/19 -p tcp -m tcp --dport {} -m state --state NEW -m recent " + \
                    " --update --seconds 1 --hitcount 255 --name {} --mask 255.255.255.255 " + \
                    " --rsource -j REJECT --reject-with tcp-reset "
print("#"*60)
print("#"*60)
print("# port catch all")
print(port_setter.format("1:20000", "portcatchall"))
print(port_setter.format("20100:65535", "portcatchall"))
print(port_counter.format("1:65535", "portcatchall"))

print("# service port rules ")
port = 20000
for i in range(1, 101):
    port+=1
    port_cap_name = "port{}".format(port)
    print(port_setter.format(port, port_cap_name))
    print(port_counter.format(port, port_cap_name))

print("#"*60)
print("# Lock down rules")
# Allow incoming ssh only
print("-A INPUT -p tcp -s 0/0 --sport 513:65535 --dport 22 -m state --state NEW,ESTABLISHED -j ACCEPT")
# make sure nothing comes or goes out of this box
print("-A INPUT -j DROP")
print("-A OUTPUT -j ACCEPT")

print("#"*60)
print("COMMIT")
