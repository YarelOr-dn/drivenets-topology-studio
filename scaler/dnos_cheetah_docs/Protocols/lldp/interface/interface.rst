protocols lldp interface
------------------------

**Minimum user role:** operator

Use this command to configure LLDP on an interface. To enter LLDP interface configuration mode:

**Command syntax: interface [interface-name]**

**Command mode:** config

**Hierarchies**

- protocols lldp

**Note**

- Notice the change in prompt from dnRouter(cfg-protocols-lldp)# to dnRouter(cfg-protocols-lldp-if)# (LLDP interface configuration mode).

- Once LLDP is enabled on the interface, transmission and reception of LLDP messages are both available. To change this behavior, see "lldp interface receive" and "lldp interface transmit" commands.

**Parameter table**

+----------------+----------------------------------------------------------------+--------------------------+---------+
| Parameter      | Description                                                    | Range                    | Default |
+================+================================================================+==========================+=========+
| interface-name | The physical interface on which to configure the LLDP protocol | Physical interfaces only | \-      |
+----------------+----------------------------------------------------------------+--------------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# interface ge100-2/4/1
    dnRouter(cfg-protocols-lldp-if)#


**Removing Configuration**

To remove lldp configuration from the interface:
::

    dnRouter(cfg-protocols-lldp)# no interface ge100-2/4/1

**Command History**

+---------+-------------------------------+
| Release | Modification                  |
+=========+===============================+
| 7.0     | Command introduced            |
+---------+-------------------------------+
| 9.0     | Not supported in this version |
+---------+-------------------------------+
| 10.0    | Command reintroduced          |
+---------+-------------------------------+
