protocols msdp class-of-service
-------------------------------

**Minimum user role:** operator

You can use the following command to set the DSCP value for outgoing MSDP Mtrace packets class of service.

The class-of-service set for the packet determines how the packet is treated through the network.

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols msdp

**Note**
IPP is set accordingly. i.e DSCP 48 is mapped to 6.

**Parameter table**

+------------------+-------------------------------+-------+---------+
| Parameter        | Description                   | Range | Default |
+==================+===============================+=======+=========+
| class-of-service | MSDP packets class of service | 0-56  | 48      |
+------------------+-------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# msdp
    dnRouter(cfg-protocols-msdp)# class-of-service 50


**Removing Configuration**

To return the dscp-value to the default:
::

    dnRouter(cfg-protocols-msdp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
