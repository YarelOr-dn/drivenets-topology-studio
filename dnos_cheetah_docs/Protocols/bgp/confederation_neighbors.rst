protocols bgp confederation neighbors
-------------------------------------

**Minimum user role:** operator

When operating in a confederation AS split into multiple sub-ASs, you need to configure the neighbor sub-ASs on the sub-AS border. eBGP sessions will run between the sub-ASs.

To configure the neighbor sub-ASs in the BGP confederation:

**Command syntax: confederation neighbors [neighbors-as]** [, neighbors-as, neighbors-as]

**Command mode:** config

**Hierarchies**

- protocols bgp

**Note**

- This command is available to the default VRF instance only.

- If run another command with different AS-numbers, the new AS-numbers will be added as confederation neighbors. The command does not override existing neighbors.

**Parameter table**

+--------------+------------------------------------+--------------+---------+
| Parameter    | Description                        | Range        | Default |
+==============+====================================+==============+=========+
| neighbors-as | neighbors ASs in BGP confederation | 1-4294967295 | \-      |
+--------------+------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp 65000
    dnRouter(cfg-protocols-bgp)# confederation neighbors 8001, 8002, 8003
    dnRouter(cfg-protocols-bgp)# confederation neighbors 8004, 8005


**Removing Configuration**

To remove all confederation neighbor configuration:
::

    dnRouter(cfg-protocols-bgp)# no confederation neighbors

To remove specific neighbors from the confederation group:
::

    dnRouter(cfg-protocols-bgp)# no confederation neighbors 8002

::

    dnRouter(cfg-protocols-bgp)# no confederation neighbors 8001, 8005

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
