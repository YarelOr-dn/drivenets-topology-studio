system dns server priority ip-address vrf
-----------------------------------------

**Minimum user role:** operator

To configure the DNS server VRF:

**Command syntax: vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system dns server priority ip-address

**Note**
-  Out-of-band packets will be sent with mgmt0 ip address.

-  The no command resets the vrf to its default value.

-  DNS quarries will be resolved in the same VRF they where issued, if there in no configured DNS server, the quarries will be dropped.

-  Validation: is required to fail the commit if more than 3 non-default VRFs are configured in general.

-  Validation: fail the commit if more than one in-band management non-default VRF is configured with an admin-state “enabled” knob.

**Parameter table**

+-----------+--------------------------------+---------------------+---------+
| Parameter | Description                    | Range               | Default |
+===========+================================+=====================+=========+
| vrf-name  | The name of the DNS server VRF | | default           | default |
|           |                                | | non-default-vrf   |         |
|           |                                | | mgmt0             |         |
+-----------+--------------------------------+---------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# dns
    dnRouter(cfg-system-dns)# server priority 1 ip-address 12.127.17.83
    dnRouter(cfg-system-dns-server)# vrf default
    dnRouter(cfg-system-dns)# server priority 7 ip-address 12.127.16.83
    dnRouter(cfg-system-dns-server)# vrf mgmt0
    dnRouter(cfg-system-dns)# server priority 3 ip-address 12.33.16.22
    dnRouter(cfg-system-dns-server)# vrf non-default-vrf


**Removing Configuration**

To revert the VRF to default value:
::

    dnRouter(cfg-system-dns-server)# no vrf

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.1    | Command introduced |
+---------+--------------------+
