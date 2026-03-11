interfaces urpf admin-state
---------------------------

**Minimum user role:** operator

To enable/disable uRPF for incoming packets on a specific interface. When enabled, uRPF validation will apply to both IPv4 and IPv6 unicast packets:

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces urpf

**Note**

- The command is applicable to the following interface types:

  - Bundle
  - Bundle vlan
  - Physical
  - Physical vlan
  - IRB

**Parameter table**

+-------------+---------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                   | Range        | Default  |
+=============+===============================================================+==============+==========+
| admin-state | Set the administrative state of the uRPF for incoming packets | | enabled    | disabled |
|             |                                                               | | disabled   |          |
+-------------+---------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# bundle-1
    dnRouter(cfg-if-bundle-1)# urpf
    dnRouter(cfg-if-bundle-1-urpf)# admin-state enabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-bundle-1-urpf)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
