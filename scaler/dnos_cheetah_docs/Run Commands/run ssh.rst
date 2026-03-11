run ssh
-------

**Minimum user role:** viewer

The run ssh command enables to make a secure connection from the NCR to another device. This command is supported for default/non-default VRF interfaces and for mgmt0 out-of-band interfaces.

If you do not specify either an egress-interface or source-address, the SSH packets will be generated via the in-band management channel with a source IP address according to the default VRF routing table.

**Command syntax: run ssh [user-name]@[dest-ip]|[host-name]** {vrf [vrf-name] \| {egress-interface [egress-interface] | source-address [source-address] } }

**Command mode:** operation 

.. **Note**

	- ssh command is one-line format. meaning - all parameters can be entered on the same line

	- run ssh[dest-ip]egress-interface  `[egress-interface] <https://drivenets.atlassian.net/wiki/display/DV/source-ip>`__- defines source IP of the packet to IP address of the egress interface. If "egress-interface"=mgmt0, linux command "ssh [ip-address]" should be run in a context of default NS, i.e. SSH will run in out-of-band.

	- run ssh [dest-ip] source-address [source-address] - set source ip-address for SSH packets.

	- If neither egress-interface nor source-address parameter was set, SSH packets are generated via in-band management channel with source IP address according to default VRF routing table

    - If vrf is specified the connection will be established over the specified VRF, and the egress-interface will be allowed only from the selected VRF.

	- ability to specify host-name instead of dest-ip address is supported starting from v11.2 only

**Parameter table**

+---------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+---------+
| Parameter           | Description                                                                                                                                                                                                                                  | Range                                | Default |
+=====================+==============================================================================================================================================================================================================================================+======================================+=========+
| user-name@dest-ip   | The IPv4 or IPv6 host address of the device to which to connect. The user-name indicates the current user.                                                                                                                                   | A.B.C.D                              | \-      |
|                     |                                                                                                                                                                                                                                              | x:x::x:x                             |         |
+---------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+---------+
| user-name@host-name | The host-name of the device to which to connect. The user-name indicates the current user.                                                                                                                                                   | A partial or full domain name.       | \-      |
+---------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+---------+
| source-address      | Sends the SSH packets with the defined ip address as a source address.                                                                                                                                                                       | A.B.C.D                              | \-      |
|                     |                                                                                                                                                                                                                                              | xx:xx::xx:xx                         |         |
+---------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+---------+
| egress-interface    | Sets the IP address of the egress-interface as the source IP address of outgoing SSH packets. If the egress interface is mgmt0, the SSH packets are sent via the OOB management network (i.e. they are transmitted via the mgmt0 interface). | All default VRF interfaces and mgmt0 | \-      |
+---------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+---------+
| vrf-name            | The name of the VRF through which the connect will be established.                                                                                                                                                                           | The VRF name                         | \-      |
+---------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------------------------------+---------+

**Example**
::

	dnRouter# run ssh user@1.1.1.1
	dnRouter# run ssh user@1.1.1.1 egress-interface lo0
	dnRouter# run ssh user@1.1.1.1 source-address 5.5.5.5
	dnRouter# run ssh user@dnCoreRouter-2
	dnRouter# run ssh user@1.1.1.1 egress-interface irb4 vrf my-vrf
	

.. **Help line:** run ssh

**Command History**

+---------+---------------------------------------------------------+
| Release | Modification                                            |
+=========+=========================================================+
| 5.1.0   | Command introduced                                      |
+---------+---------------------------------------------------------+
| 11.5    | Added option to connect to a device using the host-name |
+---------+---------------------------------------------------------+
| 19.1    | Added non default inband management VRF support         |
+---------+---------------------------------------------------------+

