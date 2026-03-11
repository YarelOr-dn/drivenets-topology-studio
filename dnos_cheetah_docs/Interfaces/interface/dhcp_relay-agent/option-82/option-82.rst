interfaces dhcp relay-agent option-82
-------------------------------------

**Minimum user role:** operator

To enter DHCP relay agent's Relay Agent Information Option configuration mode:

**Command syntax: option-82**

**Command mode:** config

**Hierarchies**

- interfaces dhcp relay-agent

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# dhcp relay-agent
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# option-82
    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay-option-82)#


**Removing Configuration**

To remove the DHCP relay agent's Relay Agent Information Option configuration:
::

    dnRouter(cfg-if-ge100-0/0/0-dhcp-relay)# no option-82

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
