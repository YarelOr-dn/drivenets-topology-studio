interfaces qppb
---------------

**Minimum user role:** operator


Enables or disables QPPB policy enforcement on traffic received from the interface.

**Command syntax: qppb [admin-state]**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- The command is applicable to the following interface types:

  - Physical
  - Physical vlan
  - Bundle
  - Bundle vlan.

- To apply the qppb policy to a BGP installation on RIB, see the "protocols bgp address-family ipv4-unicast rib-install policy" command in this publication.
- To configure the QoS qppb policy rules and actions, see the "routing-policy qppb-policy" set of commands in this publication. 

**Parameter table**

+-------------+----------------------------------------------------------------------------------+--------------+----------+
| Parameter   | Description                                                                      | Range        | Default  |
+=============+==================================================================================+==============+==========+
| admin-state | When enabled, VRF QPPB policy is enforced on traffic received through this       | | enabled    | disabled |
|             | interface.                                                                       | | disabled   |          |
+-------------+----------------------------------------------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# interfaces
    dnRouter(cfg-if)# ge100-0/0/0
    dnRouter(cfg-if-ge100-0/0/0)# qppb enabled
    dnRouter(cfg-if-ge100-0/0/0)# qppb disabled


**Removing Configuration**

To revert to the default value:
::

    dnRouter(cfg-if-ge100-0/0/0)# no qppb

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.1    | Command introduced |
+---------+--------------------+
