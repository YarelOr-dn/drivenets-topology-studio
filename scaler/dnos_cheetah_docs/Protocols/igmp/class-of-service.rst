protocols igmp class-of-service
-------------------------------

**Minimum user role:** operator

You can use the following command to set the DSCP value for outgoing IGMP Mtrace packets class of service.

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols igmp

**Note**
- IPP is set according to the DSCP value for outgoing packets, for example, DSCP 48 is mapped to 6.

**Parameter table**

+------------------+-------------------------------+-------+---------+
| Parameter        | Description                   | Range | Default |
+==================+===============================+=======+=========+
| class-of-service | IGMP packets class of service | 0-56  | 48      |
+------------------+-------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# igmp
    dnRouter(cfg-protocols-igmp)# class-of-service 50


**Removing Configuration**

To return the dscp-value to the default:
::

    dnRouter(cfg-protocols-igmp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
