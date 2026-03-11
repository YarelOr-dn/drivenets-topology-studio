system aaa-server radius server vrf
-----------------------------------

**Minimum user role:** operator

To configure the RADIUS server VRF:

**Command syntax: vrf [vrf-name]**

**Command mode:** config

**Hierarchies**

- system aaa-server radius server

**Note:**

-  Up to 5 in-band (vrf default) and 5 out-of-band (vrf mgmt0) RADIUS servers are supported

-  Out-of-band packets will be sent with mgmt0 ip address.

-  no command resets the vrf to default value

**Parameter table:**

+-----------+-----------------------------------+---------+---------------+
| Parameter |            Description            |  Values | Default value |
+===========+===================================+=========+===============+
| vrf-name  | The name of the RADIUS server VRF | default | \-            |
|           |                                   |         |               |
|           |                                   | mgmt0   |               |
+-----------+-----------------------------------+---------+---------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# aaa-server
	dnRouter(cfg-system-aaa)# radius
	dnRouter(cfg-system-aaa-radius)# server priority 1 address 192.168.1.1
	dnRouter(cfg-aaa-radius-server)# vrf default

	dnRouter(cfg-system-aaa-radius)# server priority 2 address 192.168.1.2
	dnRouter(cfg-aaa-radius-server)# vrf mgmt0

**Removing Configuration**

To reset the vrf to the default value: 
::

	dnRouter(cfg-aaa-radius-server)# no vrf mgmt0

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+



