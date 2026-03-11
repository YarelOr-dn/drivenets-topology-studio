run traceroute
--------------

**Minimum user role:** viewer

The run traceroute command displays the route that packets take to the specified destination address. When enabled, the router sends out a number of probes (UDP packets) set by the count parameter to the destination IP. This command is useful to locate points of failure in the network.

**Command syntax: run traceroute [dest-ip \| host-name]** source-interface [source-interface] max-hops [max-hops] df

**Command mode:** GI

**Note**

- The NCC handles ICMP packets. Therefore, traceroute to a remote host should be done from the NCC and not from the NCPs.

.. - The traceroute command is one-line format. meaning - all parameters can be entered on the same line

	 - run traceroute [dest-ip]source-interface [source-interface] - The traceroute packet should be sent with the defined ip address of the source interface.

	 - The run traceroute command may include the source-interface. The source-interface must be of type mgmt-ncc-X.

**Parameter table**

The following are the parameters for this command:

+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| Parameter        | Description                                                                                                                                                                                                  | Range                                              | Default |
+==================+==============================================================================================================================================================================================================+====================================================+=========+
| dest-ip          | The IPv4 or IPv6 address of the remote host to trace                                                                                                                                                         | x.x.x.x                                            | \-      |
|                  |                                                                                                                                                                                                              | x:x::x:x                                           |         |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| host-name        | The name of the target host to trace                                                                                                                                                                         | String                                             | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| source-interface | Sends the ping packets with the defined IP address of the source interface                                                                                                                                   | mgmt-ncc-X                                         | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| max-hops         | The maximum number of hops that the trace packet should cross before timeout                                                                                                                                 | 1..255                                             | 30      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| df               | Do not fragment - a flag specifying that outgoing packets must not be fragmented.                                                                                                                            | Boolean                                            | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+

The parameters can all be specified in the same command.

**Example**
::

	GI# run traceroute 1.1.1.1
	GI# run traceroute 2001:1234::1
	GI# run traceroute source-interface mgmt-ncc-1
	GI# run traceroute 1.1.1.1 max-hops 2

.. **Help line:** run traceroute request

**Command History**

+---------+------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                               |
+=========+============================================================================================================+
| 18.3    | Command introduced                                                                                         |
+---------+------------------------------------------------------------------------------------------------------------+
