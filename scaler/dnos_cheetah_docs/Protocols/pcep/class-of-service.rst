protocols segment-routing pcep class-of-service
-----------------------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.

To configure a CoS for outgoing PCEP packets:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols segment-routing pcep

**Parameter table**

+------------------+------------------------------------------+-------+---------+
| Parameter        | Description                              | Range | Default |
+==================+==========================================+=======+=========+
| class-of-service | set dscp value for outgoing PCEP packets | 0-56  | 48      |
+------------------+------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# segment-routing
    dnRouter(cfg-protocols-sr)# pcep
    dnRouter(cfg-protocols-sr-pcep)# class-of-service 48


**Removing Configuration**

To revert class-of-service to its default value:
::

    dnRouter(cfg-protocols-sr-pcep)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 10.0    | Command introduced |
+---------+--------------------+
