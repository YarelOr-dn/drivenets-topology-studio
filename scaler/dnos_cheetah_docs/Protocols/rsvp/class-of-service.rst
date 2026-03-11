protocols rsvp class-of-service
-------------------------------

**Minimum user role:** operator

With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you can control which packets receive priority.
To configure a CoS for all outgoing RSVP packets:

**Command syntax: class-of-service [class-of-service-dscp]**

**Command mode:** config

**Hierarchies**

- protocols rsvp

**Parameter table**

+-----------------------+------------------------------------------+-------+---------+
| Parameter             | Description                              | Range | Default |
+=======================+==========================================+=======+=========+
| class-of-service-dscp | set dscp value for outgoing RSVP packets | 0-56  | 48      |
+-----------------------+------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# class-of-service 48


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-rsvp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
