protocols ospf graceful-restart
-------------------------------

**Minimum user role:** operator

OSPF graceful restart enables a router undergoing a restart to inform its adjacent OSPF neighbors of its restarting condition. During a graceful restart period, the restarting device and its neighbors continue to forward packets without disrupting network performance. Because neighboring devices assist in the restart (these are helper routers), the restarting device can resume routing operation without impacting forwarding of packets in the data-path.

**Command syntax: graceful-restart**

**Command mode:** config

**Hierarchies**

- protocols ospf

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols ospf
    dnRouter(cfg-protocols-ospf)# graceful-restart
    dnRouter(cfg-protocols-ospf-gr)#


**Removing Configuration**

To reverts all ospf graceful restart parameters to their default values: 
::

    dnRouter(cfg-protocols-ospf)# no graceful-restart

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
