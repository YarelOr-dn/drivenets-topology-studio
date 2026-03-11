protocols ospfv3 router-id
--------------------------

**Minimum user role:** operator

Use the following command to set the OSPFV3 router-id as the network unique router ID:

**Command syntax: router-id [router-id]**

**Command mode:** config

**Hierarchies**

- protocols ospfv3

**Note**

- The 'no router-id' command will restore the ospfv3 router-id to its default value.

- When changing the router-id, the OSPFv3 process will restart with the current configuration.

**Parameter table**

+-----------+----------------------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                                      | Range   | Default |
+===========+==================================================================================+=========+=========+
| router-id | A 32-bit number represented as a dotted quad assigned to each router running the | A.B.C.D | \-      |
|           | OSPFv2 protocol. This number should be unique within the autonomous system. the  |         |         |
|           | default value should be the highest IP address on the lowest routers Loopback    |         |         |
|           | Interfaces. If there is no Loopback Interfaces configured, then highest IP       |         |         |
|           | address on its active interfaces                                                 |         |         |
+-----------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospfv3
    dnRouter(cfg-protocols-ospfv3)# router-id 100.70.1.45


**Removing Configuration**

To restore the ospfv3 router-id to its default value:
::

    no router-id

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
