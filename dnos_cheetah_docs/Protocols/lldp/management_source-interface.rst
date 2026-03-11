protocols lldp management source-interface
------------------------------------------

**Minimum user role:** operator

To configure source interface from which management address will be taken for lldp management tlv advertisements

**Command syntax: management source-interface [management source-address]**

**Command mode:** config

**Hierarchies**

- protocols lldp

**Note**

- source-interface can belong to any vrf in system

- In case source-interface has no ip address, or in state down, lldp will fallback to advertise mac address of the provided interface.'

**Parameter table**

+---------------------------+--------------------------------------------------------------------------------+------------------+---------+
| Parameter                 | Description                                                                    | Range            | Default |
+===========================+================================================================================+==================+=========+
| management source-address | source interface for management address to be advertised under management tlv. | | string         | \-      |
|                           |                                                                                | | length 1-255   |         |
+---------------------------+--------------------------------------------------------------------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# management-source-interface bundle-1.127

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# management-source-interface irb5


**Removing Configuration**

To revert to default management address behavior:
::

    dnRouter(cfg-protocols-lldp-if)# no management-source-interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
