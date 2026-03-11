system ntp server
-----------------

**Minimum user role:** operator

To configure remote NTP server:

**Command syntax: server [server-address] vrf [vrf-name]** key [key-id] \| prefer \| iburst

**Command mode:** configuration

**Hierarchies**

- system ntp


**Note**

- Make sure that system timing mode is set to "ntp". If set to "manual" the NTP functionality is disabled. See system timing-mode.

- Up to 5 in-band (vrf default) and 5 out-of-band (vrf mgmt0) NTP servers are supported.

.. - no command removes the ntp server configuration

	- Prefer parameter can be configured on only one NTP server. Prefer parameter indicates the preferred NTP server.

	- When iburst parameter is set, a series of NTP packets are sent instead of a single packet within the initial synchronization interval to achieve faster initial synchronization.

	- Up to 5 in-band (vrf default) and 5 out-of-band (vrf mgmt0) NTP servers are supported.

	- Validation: 0nly one VRF at the same time can have configured administratively enabled NTP servers.


**Parameter table**

+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------+
| Parameter      | Description                                                                                                                                                              | Range                                           | Default |
+================+==========================================================================================================================================================================+=================================================+=========+
| server-address | Enter the IPv4 or IPv6 address of the NTP server                                                                                                                         | A.B.C.D                                         | \-      |
|                |                                                                                                                                                                          | xx:xx::xx:xx                                    |         |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------+
| key-id         | Optional. Attach an existing authentication key to the NTP server. See system ntp authentication key.                                                                    | Any configured authentication key in the system | \-      |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------+
| prefer         | Optional. When configuring multiple NTP servers, add this attribute to indicate the preferred server. Only one NTP server can be configured with the "prefer" attribute. | \-                                              | \-      |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------+
| iburst         | Sends a series of NTP packets within the initial synchronization interval to achieve faster initial synchronization.                                                     | \-                                              | \-      |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------+
| vrf-name       | Allows to define separate NTP servers per VRF (in-band and out-of-band).                                                                                                 | default - in-band, mgmt0 - out-of-band          | \-      |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------+
| admin-state    | Enable/disable NTP server admin-state.                                                                                                                                   | Enabled / Disabled                              | Enabled |
+----------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------------------------------------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ntp
	dnRouter(cfg-system-ntp)# server 200.24.34.1 vrf default
	dnRouter(cfg-system-ntp-server)# admin-state enabled
	dnRouter(cfg-system-ntp-server)# iburst

	dnRouter(cfg-system-ntp)# server 111.200.55.6 vrf mgmt0 key 3
	dnRouter(cfg-system-ntp)# server 111.200.55.6 vrf mgmt0
	dnRouter(cfg-system-ntp-server)# admin-state disabled

	dnRouter(cfg-system-ntp)# server 154.89.12.9 vrf default
	dnRouter(cfg-system-ntp-server)# admin-state enabled
	dnRouter(cfg-system-ntp-server)# iburst
	dnRouter(cfg-system-ntp-server)# prefer

	dnRouter(cfg-system-ntp)# server 2001:ab12::1 vrf mgmt0
	dnRouter(cfg-system-ntp-server)# admin-state disabled
	dnRouter(cfg-system-ntp-server)# iburst


**Removing Configuration**

To remove the remote NTP server:
::

	dnRouter(cfg-system-ntp)# no server 200.24.34.1 vrf default
	dnRouter(cfg-system-ntp)# no server 111.200.55.6 mgmt0 key 3
	dnRouter(cfg-system-ntp)# no server 154.89.12.9 vrf default prefer
	dnRouter(cfg-system-ntp)# no server 2001:ab12::1 vrf mgmt0 iburst

.. **Help line:** Configure system's NTP servers

**Command History**

+---------+-----------------------+
| Release | Modification          |
+=========+=======================+
| 5.1.0   | Command introduced    |
+---------+-----------------------+
| 6.0     | Applied new hierarchy |
+---------+-----------------------+
| 15.2    | Added VRF             |
+---------+-----------------------+
