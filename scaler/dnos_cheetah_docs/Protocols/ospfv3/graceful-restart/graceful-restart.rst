protocols ospfv3 graceful-restart
---------------------------------

**Minimum user role:** operator

OSPFV3 graceful restart enables a router undergoing a restart to inform its adjacent OSPFV3 neighbors of its restarting condition. During a graceful restart period, the restarting device and its neighbors continue to forward packets without disrupting network performance. Because neighboring devices assist in the restart (these are helper routers), the restarting device can resume routing operation without impacting forwarding of packets in the data-path.
To enable OSPFV3 graceful restart:

**Command syntax: graceful-restart**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospfv3
    dnRouter(cfg-protocols-ospfv3)# graceful-restart
    dnRouter(cfg-protocols-ospfv3-gr)#


**Removing Configuration**

To reverts all ospfv3 graceful restart parameters to thier default values:
::

    dnRouter(cfg-protocols-ospfv3)# no graceful-restart

**Command History**

+---------+--------------------------+
| Release | Modification             |
+=========+==========================+
| 11.6    | Command introduced       |
+---------+--------------------------+
| 13.1    | Added support for OSPFv3 |
+---------+--------------------------+
