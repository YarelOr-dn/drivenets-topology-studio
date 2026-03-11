protocols pim class-of-service
------------------------------

**Minimum user role:** operator

To set the DSCP value for outgoing PIM packets:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- protocols pim

**Note**
- The IPP is set accordingly. I.e DSCP 48 is mapped to 6.

**Parameter table**

+------------------+------------------------------+-------+---------+
| Parameter        | Description                  | Range | Default |
+==================+==============================+=======+=========+
| class-of-service | PIM packets class of service | 0-56  | 48      |
+------------------+------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# pim
    dnRouter(cfg-protocols-pim)# class-of-service 48
    dnRouter(cfg-protocols-pim)#


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols-pim)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
