interfaces urpf
---------------

**Minimum user role:** operator

Unicast Reverse Path Forwarding (uRPF) is a security mechanism that validates the source of a received IP packet. The uRPF validation aims to block any malicious flow that can be identified as a spoofed IP packet or invalid source IP.

Whenever an IP packet is received on a uRPF enabled interface, the packet source IP will be checked against the forwarding table to verify there is a matching entry in the routing table for the source IP address. If it doesn’t match, the packet will be discarded.

uRPF works in loose mode, where a match in the forwarding table is sufficient to pass the uRPF validity check (in the event of a match of the source IP on-route-to-black-hole, the packet will fail the validity check).

To enter uRPF configuration level on an interface:

**Command syntax: urpf**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Bundle
  - Bundle vlan
  - Physical
  - Physical vlan
  - IRB

- You can view the uRPF using the show interfaces detail command. See "show interfaces detail".

- To view uRPF counters, use the show interfaces counters command. See "show interfaces counters".

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# urpf
    dnRouter(cfg-if-bundle-1-urpf)#


**Removing Configuration**

To revert all urpf settings to their default values:
::

    dnRouter(cfg-if-bundle-1)# no urpf

**Command History**

+---------+--------------------------------------------------------------------+
| Release | Modification                                                       |
+=========+====================================================================+
| 5.1     | Command introduced                                                 |
+---------+--------------------------------------------------------------------+
| 6.0     | Changed syntax from interface to interfaces, applied new hierarchy |
+---------+--------------------------------------------------------------------+
| 9.0     | Not supported in this version                                      |
+---------+--------------------------------------------------------------------+
| 13.0    | Command re-introduced                                              |
+---------+--------------------------------------------------------------------+
