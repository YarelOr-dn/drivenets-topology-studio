network-services vrf instance protocols bgp neighbor-group
----------------------------------------------------------

**Minimum user role:** operator

Groups allow you to share configuration among the group members. Some neighbor configuration may override the group configuration.

Once the neighbor group is created, assign neighbors to the group. See \"bgp neighbor\". To override the group configuration for a neighbor, configure the neighbor in the group.

To create a neighbor group:

**Command syntax: neighbor-group [peer-group]**

**Command mode:** config

**Hierarchies**

- network-services vrf instance protocols bgp
- protocols bgp

**Note**

- Notice the change in prompt.

**Parameter table**

+------------+------------------------+------------------+---------+
| Parameter  | Description            | Range            | Default |
+============+========================+==================+=========+
| peer-group | peer-group unique name | | string         | \-      |
|            |                        | | length 1-255   |         |
+------------+------------------------+------------------+---------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group BGP:pe2ce:internet
    dnRouter(cfg-protocols-bgp-group)#

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# neighbor-group IBGP:pe2core
    dnRouter(cfg-protocols-bgp-group)#


**Removing Configuration**

To delete a BGP group:
::

    dnRouter(cfg-protocols-bgp)# no neighbor-group IBGP:pe2core

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 6.0     | Command introduced |
+---------+--------------------+
