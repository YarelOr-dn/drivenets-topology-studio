system ssh server class-of-service
----------------------------------

**Minimum user role:** operator

The DSCP value that is used in the IP header to classify the packet and give it a priority.

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- system ssh server

**Note**

- With class of service (CoS) you can classify traffic to provide different service levels to different traffic so that when congestion occurs, you are able to control which packets receive priority.

**Parameter table**

+------------------+------------------------------------------------------------+-------+---------+
| Parameter        | Description                                                | Range | Default |
+==================+============================================================+=======+=========+
| class-of-service | This parameter specifies the dscp of generated SSH packets | 0-56  | 16      |
+------------------+------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ssh
    dnRouter(cfg-system-ssh)# server
    dnRouter(cfg-system-ssh-server)# class-of-service 54


**Removing Configuration**

To revert the ssh server class-of-service to default: 
::

    dnRouter(cfg-system-netconf)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
