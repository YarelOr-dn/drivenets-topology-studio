protocols ospf instance class-of-service
----------------------------------------

**Minimum user role:** operator

Set dscp value for outgoing OSPF packets. 
IPP is set accordingly. i.e DSCP 48 is mapped to 6.

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols ospf instance

**Note**

- No command returns dscp-value to default

**Parameter table**

+------------------+--------------------------------------+-------+---------+
| Parameter        | Description                          | Range | Default |
+==================+======================================+=======+=========+
| class-of-service | dscp value for outgoing OSPF packets | 0-56  | 48      |
+------------------+--------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ospf
    dnRouter(cfg-protocols-ospf)# class-of-service 48


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-ospf)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
