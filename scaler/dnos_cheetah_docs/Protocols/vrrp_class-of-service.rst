protocols vrrp class-of-service
-------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure a CoS for all outgoing VRRP packets:

**Command syntax: vrrp class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The class-of-service configuration is global and applies to all VRRP instances in any VRF.

**Parameter table**

+------------------+--------------------------------------+-------+---------+
| Parameter        | Description                          | Range | Default |
+==================+======================================+=======+=========+
| class-of-service | DSCP value for outgoing VRRP packets | 0-56  | 48      |
+------------------+--------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp class-of-service 48


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols)# no vrrp class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
