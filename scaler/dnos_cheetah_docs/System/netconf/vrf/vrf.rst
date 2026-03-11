system netconf vrf
------------------

**Minimum user role:** operator

To configure a Netconf server per VRF:

**Command syntax: vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system netconf

**Note**

- The VRF "default" represents in-band management, while VRF "mgmt0" represents out-of-band management.

- Netconf can be configured on up to 3 non-default inband management VRF contexts in general.

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
    dnRouter(cfg-system)# netconf vrf default
    dnRouter(cfg-system-netconf-vrf)#
    dnRouter(cfg-system)# netconf vrf mgmt0
    dnRouter(cfg-system-netconf-vrf)#
    dnRouter(cfg-system)# netconf vrf my_vrf
    dnRouter(cfg-system-netconf-vrf)#


**Removing Configuration**

To delete the configuration under the non-default specific vrf:
::

    dnRouter(cfg-system-netconf)# no vrf my_vrf

For VRF default and mgmt0 no command will rest the configuration:
::

    dnRouter(cfg-system-netconf)# no vrf default

**Command History**

+---------+--------------------------------------------+
| Release | Modification                               |
+=========+============================================+
| 13.1    | Command introduced                         |
+---------+--------------------------------------------+
| 17.0    | non-default in-band management VRF support |
+---------+--------------------------------------------+
