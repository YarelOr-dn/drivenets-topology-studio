protocols vrrp startup-delay
----------------------------

**Minimum user role:** operator

To set the startup delay to wait before a backup router will attempt preempting the master for the VRRP groups after an interface becomes operational:

**Command syntax: vrrp startup-delay [startup-delay]**

**Command mode:** config

**Hierarchies**

- protocols

**Note**

- The startup-delay configuration is global and applies to all VRRP instances in any VRF.

**Parameter table**

+---------------+----------------------------------------------------------------------------------+--------+---------+
| Parameter     | Description                                                                      | Range  | Default |
+===============+==================================================================================+========+=========+
| startup-delay | Set the delay the higher priority backup router waits before preempting the      | 0-3600 | 30      |
|               | master router after the interfaces becomes operational                           |        |         |
+---------------+----------------------------------------------------------------------------------+--------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# vrrp startup-delay 600


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-protocols)# no vrrp startup-delay

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.1    | Command introduced |
+---------+--------------------+
