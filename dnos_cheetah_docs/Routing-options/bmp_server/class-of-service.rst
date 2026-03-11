routing-options bmp server class-of-service
-------------------------------------------

**Minimum user role:** operator

To set the DSCP value for outgoing BMP packets.

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- routing-options bmp server

**Parameter table**

+------------------+-------------------------------------+-------+---------+
| Parameter        | Description                         | Range | Default |
+==================+=====================================+=======+=========+
| class-of-service | dscp value for outgoing BMP packets | 0-56  | 16      |
+------------------+-------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# routing-options
    dnRouter(cfg-routing-option)# bmp server 1
    dnRouter(cfg-routing-option-bmp)# class-of-service 48


**Removing Configuration**

To return the DSCP value to the default value:
::

    dnRouter(cfg-routing-option-bmp)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
