protocols bgp class-of-service
------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure a CoS for all outgoing BGP packets:

**Command syntax: bgp class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols

**Parameter table**

+------------------+-------------------------------------+-------+---------+
| Parameter        | Description                         | Range | Default |
+==================+=====================================+=======+=========+
| class-of-service | dscp value for outgoing BGP packets | 0-56  | 48      |
+------------------+-------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# bgp class-of-service 48


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols)# no bgp class-of-service 48

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
