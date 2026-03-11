system grpc vrf
---------------

**Minimum user role:** operator

To configure a gRPC server per client list per VRF:

**Command syntax: vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system grpc

**Note**

- The VRF "default" represents in-band management, while VRF "mgmt0" represents out-of-band management.

- Up to 3 non-default inband management VRF contexts can be configured in general.

**Parameter table**

+-----------+----------------------+------------------+---------+
| Parameter | Description          | Range            | Default |
+===========+======================+==================+=========+
| vrf-name  | The name of the vrf. | | string         | \-      |
|           |                      | | length 1-255   |         |
+-----------+----------------------+------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc vrf default
    dnRouter(cfg-system-grpc-vrf)#
    dnRouter(cfg-system)# grpc vrf mgmt0
    dnRouter(cfg-system-grpc-vrf)#
    dnRouter(cfg-system)# grpc vrf my_vrf
    dnRouter(cfg-system-grpc-vrf)#


**Removing Configuration**

To delete the configuration under the non-default specific vrf:
::

    dnRouter(cfg-system-grpc)# no vrf default

For VRF default and mgmt0 no command will reset the configuration:
::

    dnRouter(cfg-system-grpc)# no vrf default

**Command History**

+---------+--------------------------------------------+
| Release | Modification                               |
+=========+============================================+
| 13.1    | Command introduced                         |
+---------+--------------------------------------------+
| 16.2    | non-default in-band management VRF support |
+---------+--------------------------------------------+
