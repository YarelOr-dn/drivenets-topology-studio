system netconf vrf admin-state
------------------------------

**Minimum user role:** operator

To enable/disable netconf server per VRF.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system netconf vrf

**Note**

- The admin-state can only be enabled on one in-band management non-default VRF.

**Parameter table**

+-------------+-----------------------------------------+--------------+---------+
| Parameter   | Description                             | Range        | Default |
+=============+=========================================+==============+=========+
| admin-state | The desired state of the NETCONF server | | enabled    | enabled |
|             |                                         | | disabled   |         |
+-------------+-----------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# netconf vrf default
    dnRouter(cfg-system-netconf-vrf)# admin-state disabled
    dnRouter(cfg-system)# netconf vrf mgmt0
    dnRouter(cfg-system-netconf-vrf)# admin-state enabled
    dnRouter(cfg-system)# netconf vrf my_vrf
    dnRouter(cfg-system-netconf-vrf)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-system-netconf-vrf)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.0    | Command introduced |
+---------+--------------------+
