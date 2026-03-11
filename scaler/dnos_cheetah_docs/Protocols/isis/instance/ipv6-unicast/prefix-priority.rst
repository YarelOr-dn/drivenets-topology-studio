protocols isis instance address-family ipv6-unicast prefix-priority tag
-----------------------------------------------------------------------

**Minimum user role:** operator

Assign a tag value to the prefix-priority, to ensure that prefixes with this tag are handled with the given priority

**Command syntax: prefix-priority [prefix-priority] tag [tag]**

**Command mode:** config

**Hierarchies**

- protocols isis instance address-family ipv6-unicast

**Parameter table**

+-----------------+--------------------------------------------------------------------------------+--------------+---------+
| Parameter       | Description                                                                    | Range        | Default |
+=================+================================================================================+==============+=========+
| prefix-priority | The priority - low, mediumm or high                                            | | low        | \-      |
|                 |                                                                                | | medium     |         |
|                 |                                                                                | | high       |         |
+-----------------+--------------------------------------------------------------------------------+--------------+---------+
| tag             | Tag value, that if associated with a prefix will be given the defined priority | 1-4294967295 | \-      |
+-----------------+--------------------------------------------------------------------------------+--------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# instance ISIS_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-unicast
    dnRouter(cfg-isis-inst-afi)# prefix-priority high tag 100
    dnRouter(cfg-isis-inst-afi)#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# instance ISIS_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv6-unicast
    dnRouter(cfg-isis-inst-afi)# prefix-priority high tag 100
    dnRouter(cfg-isis-inst-afi)#
    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# isis
    dnRouter(cfg-protocols-isis)# instance ISIS_1
    dnRouter(cfg-protocols-isis-inst)# address-family ipv4-multicast
    dnRouter(cfg-isis-inst-afi)# prefix-priority high tag 100
    dnRouter(cfg-isis-inst-afi)#


**Removing Configuration**

To remove tag:
::

    dnRouter(cfg-inst-protocols-static)# no prefix-priority high

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
