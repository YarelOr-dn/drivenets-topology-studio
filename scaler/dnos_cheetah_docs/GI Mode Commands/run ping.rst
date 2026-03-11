run ping
--------

**Minimum user role:** viewer

The ping command checks the accessibility of a destination interface. It uses a series of Internet Control Message Protocol (ICMP) Echo messages to determine whether or not the remote host is active, the round-trip delay in the communication with the host, and packet loss.

**Command syntax: run ping [dest-ip \| host-name]** source-interface [source-interface] interval [interval] size [size] count [count] df

**Command mode:** GI

**Note**

- The NCC handles ICMP packets. Therefore, ping to a remote host should be done from the NCC and not from the NCPs.

..
	- The ping command is one-line format. meaning - all parameters can be entered on the same line

		- The run ping command may include the source-interface. The source-interface must be of type mgmt-ncc-X.

		- Count - number or probe sequences per command

		- Size - ICMP payload

		- Interval - resolution of 0.001 seconds

		- Df - don't fragment - a flag which specifies that outgoing packet shouldn't be fragmented and should be sent as is with original size. by default, fragmentation is performed automatically. This option is only valid for IPv4 addresses.

.. **Help line:** run ICMP ping request


**Parameter table**

The following are the parameters that you can use for the ping command:

+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| Parameter        | Description                                                                                                                                                                                                  | Range                                               | Default |
+==================+==============================================================================================================================================================================================================+=====================================================+=========+
| dest-ip          | The IPv4/IPv6 address of the target host to ping                                                                                                                                                             | A.B.C.D                                             | \-      |
|                  |                                                                                                                                                                                                              | x:x::x:x                                            |         |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| host-name        | The name of the target host to ping                                                                                                                                                                          | String                                              | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| source-interface | Sends the ping packets with the defined IP address of the source interface                                                                                                                                   | mgmt-ncc-X                                          | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| interval         | Specifies the time in seconds between sending ping packets (resolution of 0.001 seconds)                                                                                                                     | 0.001..86,400                                       | 1       |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| size             | Specifies the number of data bytes to be added to the ping packet                                                                                                                                            | 1..65507                                            | 56      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| count            | Specifies the number of ping packets that will be sent                                                                                                                                                       | 1..1,000,000                                        | 5       |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+
| df               | Do not fragment - a flag specifying that outgoing packets must not be fragmented.                                                                                                                            | Boolean                                             | \-      |
+------------------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------------------------------------------------+---------+

The parameters can all be specified in the same command.

**Example**
::

	GI# run ping 1.1.1.1
	GI# run ping 2001:1234::1
	GI# run ping 10.0.0.1 source-interface mgmt-ncc-0
	GI# run ping 1.1.1.1 count 200
	GI# run ping 1.1.1.1 interval 2
	GI# run ping 1.1.1.1 size 1500
	GI# run ping 1.1.1.1 interval 2 size 1000


**Command History**

+---------+----------------------------------------------------------------------------------------+
| Release | Modification                                                                           |
+=========+========================================================================================+
| 18.3    | Command introduced                                                                     |
+---------+----------------------------------------------------------------------------------------+
