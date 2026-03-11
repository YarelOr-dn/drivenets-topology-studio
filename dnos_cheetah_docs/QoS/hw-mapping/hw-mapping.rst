qos hw-mapping
--------------

**Minimum user role:** operator

To configure rules for mapping QoS policy to hardware settings:


**Command syntax: hw-mapping**

**Command mode:** config

**Hierarchies**

- qos

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# hw-mapping
    dnRouter(cfg-qos-hw-map)#


**Removing Configuration**

To remove the configuration:
::

    dnRouter(cfg-qos)# no hw-mapping

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
