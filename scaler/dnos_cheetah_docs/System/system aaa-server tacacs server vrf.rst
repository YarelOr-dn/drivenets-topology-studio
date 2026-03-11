system aaa-server tacacs server priority address vrf
----------------------------------------------------

**Minimum user role:** operator

To configure the TACACS server VRF:

**Command syntax: vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs server priority address

**Note**
-  Out-of-band packets will be sent with mgmt0 ip address.

-  The no command resets the vrf to default value.

-  Validation: is required to fail the commit if more than 3 non-default VRFs are configured in general.

-  Validation: fail the commit if more than one in-band management non-default VRF is configured with admin-state “enabled” knob.


**Parameter table**

+-----------+-----------------------------------+---------------------+---------+
| Parameter | Description                       | Range               | Default |
+===========+===================================+=====================+=========+
| vrf-name  | The name of the TACACS server VRF | | default           | \-      |
|           |                                   | | non-default-vrf   |         |
|           |                                   | | mgmt0             |         |
+-----------+-----------------------------------+---------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# server priority 1 address 1.1.1.1
    dnRouter(cfg-aaa-tacacs-server)# vrf mgmt0


**Removing Configuration**

To reset the vrf to the default value:
::

    dnRouter(cfg-aaa-tacacs-server)# no vrf

**Command History**

+---------+---------------------+
| Release | Modification        |
+=========+=====================+
| 13.0    | Command introduced  |
+---------+---------------------+
| 19.1    | Added NDVRF Support |
+---------+---------------------+
