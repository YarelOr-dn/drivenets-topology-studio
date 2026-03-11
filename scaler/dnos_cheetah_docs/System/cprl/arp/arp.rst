system cprl arp
---------------

**Minimum user role:** operator

Use the following command to enter the CPRL configuration mode for the ARP protocol:

**Command syntax: arp**

**Command mode:** config

**Hierarchies**

- system cprl

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# cprl
    dnRouter(cfg-system-cprl)# arp
    dnRouter(cfg-system-cprl-arp)#


**Removing Configuration**

To revert to the default CPRL rate and burst values for the ARP protocol:
::

    dnRouter(cfg-system-cprl)# no arp

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
