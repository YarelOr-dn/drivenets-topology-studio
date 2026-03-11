system aaa-server tacacs server priority address
------------------------------------------------

**Minimum user role:** operator

To define a remote TACACS+ server:


**Command syntax: server priority [priority] address [address]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs

**Note**
- Notice the change in prompt.

- Supporting up to 5 TACACS remote servers configurations over in-band (vrf default and non-default-vrf) and out-of-band (vrf mgmt0).

    - Validation: the commit is required to fail if more than 3 non-default VRFs are configured in general.

..  - Out-of-band packets will be sent with an mgmt0 ip address.

    - The IP source address family must match the destination IP address family, both IPv6 or IPv4.

    - Changing the address per specific priority changes only the address configuration, all other configurations remain intact.

    - "no tacacs priority [priority]" removes the tacacs server configuration.

In-band management applications (e.g. SSH, NETCONF, gRPC, FTP) that require authentication, use in-band TACACS servers only. If no in-band TACACS server is configured or available, the in-band management applications will use DNOS local users for authentication.

Out-of-band management applications (e.g. SSH, NETCONF) that require authentication, use out-of-band TACACS servers only. If no out-of-band TACACS server is configured or available, the out-of-band management applications will use DNOS local users for authentication.

A management application is considered out-of-band when:

- A session is established via the mgmt0, mgmt-ncc-0, or mgmt-ncc-1 interface.

- Login to the DNOS CLI is done via the serial console interface on the active NCC.

- Login to the DNOS CLI is done via the Serial-on-LAN (SoL) IPMI interface.

- Login via the the serial console interface of NCP, NCF, or stand-by NCC to the hostOS shell does not support TACACS authentication and uses hostOS local users.


**Parameter table**

+-----------+----------------------------------------------------------------------------------+--------------+---------+
| Parameter | Description                                                                      | Range        | Default |
+===========+==================================================================================+==============+=========+
| priority  | Sets the priority of the TACACS+ server. When multiple servers are configured,   | 1..255       | \-      |
|           | the server with the higher priority (lower configured number) will be attempted  |              |         |
|           | first.                                                                           |              |         |
+-----------+----------------------------------------------------------------------------------+--------------+---------+
| address   | The IPv4/IPv6 address of the server.                                             | | A.B.C.D    | \-      |
|           | Changing the address for a specific priority, changes only the address           | | x:x::x:x   |         |
|           | configuration. All other configurations remain intact.                           |              |         |
+-----------+----------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 192.168.1.1
    dnRouter(cfg-aaa-tacacs-server)# vrf default
    dnRouter(cfg-aaa-tacacs-server)# password enc-!@#$%
    dnRouter(cfg-aaa-tacacs-server)# port 100
    dnRouter(cfg-aaa-tacacs-server)# timeout 20
    dnRouter(cfg-system-aaa-tacacs)# server priority 2 address 192.168.1.2
    dnRouter(cfg-aaa-tacacs-server)# vrf default
    dnRouter(cfg-aaa-tacacs-server)# password enc-!@#$%
    dnRouter(cfg-aaa-tacacs-server)# port 100
    dnRouter(cfg-aaa-tacacs-server)# timeout 20
    dnRouter(cfg-system-aaa-tacacs)# server priority 3 address 192.168.1.3
    dnRouter(cfg-aaa-tacacs-server)# vrf my_vrf
    dnRouter(cfg-aaa-tacacs-server)# password enc-!@#$%
    dnRouter(cfg-aaa-tacacs-server)# port 100
    dnRouter(cfg-aaa-tacacs-server)# timeout 20
    dnRouter(cfg-system-aaa-tacacs)# server priority 5 address 1134:1134::1
    dnRouter(cfg-aaa-tacacs-server)# vrf mgmt0
    dnRouter(cfg-aaa-tacacs-server)# password enc-!@#$%
    dnRouter(cfg-aaa-tacacs-server)# port 100
    dnRouter(cfg-aaa-tacacs-server)# timeout 20


**Removing Configuration**

To delete the radius server configuration:
::

    dnRouter(cfg-system-aaa-tacacs)# no server

**Command History**

+---------+----------------------------------------------+
| Release | Modification                                 |
+=========+==============================================+
| 11.0    | Command introduced                           |
+---------+----------------------------------------------+
| 13.1    | Added support for OOB management (VRF mgmt0) |
+---------+----------------------------------------------+
| 15.1    | Added support for IPv6 address format        |
+---------+----------------------------------------------+
