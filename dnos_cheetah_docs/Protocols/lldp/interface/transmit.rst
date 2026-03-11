protocols lldp interface transmit
---------------------------------

**Minimum user role:** operator

To configure lldp interface transmit capability.

By default, transmission of LLDP messages is available.

**Command syntax: transmit [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols lldp interface

**Parameter table**

+-------------+-----------------------------------------------+--------------+---------+
| Parameter   | Description                                   | Range        | Default |
+=============+===============================================+==============+=========+
| admin-state | Configures ability to transmit LLDP messages. | | enabled    | enabled |
|             |                                               | | disabled   |         |
+-------------+-----------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# interface ge100-2/4/1
    dnRouter(cfg-protocols-lldp-if)# transmit enabled

    dnRouter(cfg-protocols-lldp)# interface ge100-4/2/1
    dnRouter(cfg-protocols-lldp-if)# transmit disabled


**Removing Configuration**

To revert the transmit capability to the default value:
::

    dnRouter(cfg-protocols-lldp-if)# no transmit

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
