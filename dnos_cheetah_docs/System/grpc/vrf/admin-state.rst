system grpc vrf admin-state
---------------------------

**Minimum user role:** operator

To enable/disable gRPC server per VRF.

**Command syntax: admin-state [admin-state]**

**Command mode:** config

**Hierarchies**

- system grpc vrf

**Note**

- The admin-state can only be enabled on one in-band management non-default VRF.

**Parameter table**

+-------------+-----------------------------------------+--------------+---------+
| Parameter   | Description                             | Range        | Default |
+=============+=========================================+==============+=========+
| admin-state | gRPC server admin-state enable/disabled | | enabled    | enabled |
|             |                                         | | disabled   |         |
+-------------+-----------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc vrf default
    dnRouter(cfg-system-grpc-vrf)# admin-state disabled
    dnRouter(cfg-system)# grpc vrf mgmt0
    dnRouter(cfg-system-grpc-vrf)# admin-state enabled
    dnRouter(cfg-system)# grpc vrf my_vrf
    dnRouter(cfg-system-grpc-vrf)# admin-state enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-system-grpc-vrf)# no admin-state

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
