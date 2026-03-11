system netconf class-of-service
-------------------------------

**Minimum user role:** operator

To configure a CoS for all the outgoing NETCONF sessions:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- system netconf

**Note**
With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you are able to control which packets receive priority.

**Parameter table**

+------------------+-------------------------------------------------+-------+---------+
| Parameter        | Description                                     | Range | Default |
+==================+=================================================+=======+=========+
| class-of-service | dscp marking for class-of-service configuration | 0-56  | 0       |
+------------------+-------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# netconf
    dnRouter(cfg-system-netconf)# class-of-service 54


**Removing Configuration**

To revert the router-id to default:
::

    dnRouter(cfg-system-netconf)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
