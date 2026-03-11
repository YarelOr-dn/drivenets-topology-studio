run ping multicast
------------------

**Minimum user role:** operator

You can use the command to ping a multicast destination IP address. If the source IP or source interface is not specified the an arbitrary IP address of one of the router interfaces is selected by default.

**Command syntax:run ping multicast [group-ip-address]**  {source-interface [source-interface] \| source-ip [source-address]} interval [interval] ttl [ttl] size [size] count [count] dscp [dscp] df

**Command mode:** operation

**Note**

- The ping command must be in one-line format where all parameter are entered on the same line.

- The run ping [group-ip-address] source-interface[source-interface] command - the ping packet must be sent with the indicated source interface IPv4 address.

.. - ping command is one-line format. meaning - all parameters can be entered on the same line

	- run ping [group-ip-address] source-interface [source-interface] - The ping packet should be sent with the indicated source interface IPv4 address.

	- ttl - the initial value of the IP header TTL.

	- Count - number or probe sequences per command

	- dscp - DSCP value

	- Size - ICMP payload

	- Df - don't fragment - flag which specifies that outgoing packet shouldn't be fragmented and should be sent as is with original size. If size exceeds the egress interface mtu, then the packet will be dropped, by default, fragmentation is performed automatically

**Parameter table**

The following are the parameters for this command:

+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| Parameter        | Description                                                                                                                                                                                                                                                                 | Range                                              | Default |
+==================+=============================================================================================================================================================================================================================================================================+====================================================+=========+
| group-ip-address | IPv4-multicast-address                                                                                                                                                                                                                                                      | A.B.C.D                                            | \-      |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| source-interface | ge<interface speed>-<A>/<B>/<C>                                                                                                                                                                                                                                             | ge<interface speed>-<A>/<B>/<C>                    | \-      |
|                  | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>                                                                                                                                                                                                                          | ge<interface speed>-<A>/<B>/<C>.<sub-interface id> |         |
|                  | bundle-<bundle id>                                                                                                                                                                                                                                                          | bundle-<bundle id>                                 |         |
|                  | bundle-<bundle id>.<sub-interface id>                                                                                                                                                                                                                                       | bundle-<bundle id>.<sub-interface id>              |         |
|                  | lo<lo-interface id>                                                                                                                                                                                                                                                         | lo<lo-interface id>                                |         |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| source-address   | Source IPv4 address                                                                                                                                                                                                                                                         | A.B.C.D                                            | \-      |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| interval         | The wait time between sending packets                                                                                                                                                                                                                                       | 1-86,400 (seconds)                                 | 1       |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| ttl              | The initial value of the IP header TTL                                                                                                                                                                                                                                      | 1-255                                              | 30      |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| size             | The ICMP payload                                                                                                                                                                                                                                                            | 1-65507                                            | 56      |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| count            | Number or probe sequences per command                                                                                                                                                                                                                                       | 1-1,000,000                                        | 5       |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| dscp             | DSCP value                                                                                                                                                                                                                                                                  | 0-56                                               | 0       |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+
| df               | Don't fragment - use this flag to specify that the outgoing packet shouldn't be fragmented and should be sent as is with its original size. If the size exceeds the egress interface MTU, the packet will be dropped. By default, fragmentation is performed automatically. | Boolean                                            | \-      |
+------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+----------------------------------------------------+---------+

**Example**
::

	dnRouter# run ping multicast 224.1.1.20 source-interface lo0 ttl 30 size 1000 count 5

	Type escape sequence to abort.
	Sending 5, 100-byte ICMP Echos to 224.1.1.20, timeout is 2 seconds:
	Packet sent with a source address of 1.1.1.1

	 [<- 10.0.48.1]224.1.1.20 : [0], 1028 bytes, 0.34 ms (0.34 avg, 0% loss)
	 [<- 10.0.57.1]224.1.1.20 : [0], 1028 bytes, 0.35 ms (0.34 avg, 0% loss)
	 [<- 10.0.48.1]224.1.1.20 : [1], 1028 bytes, 0.30 ms (0.32 avg, 0% loss)
	 [<- 10.0.57.1]224.1.1.20 : [1], 1028 bytes, 0.30 ms (0.32 avg, 0% loss)
	 [<- 10.0.48.1]224.1.1.20 : [2], 1028 bytes, 0.39 ms (0.34 avg, 0% loss)
	 [<- 10.0.57.1]224.1.1.20 : [2], 1028 bytes, 0.39 ms (0.34 avg, 0% loss)
	 [<- 10.0.48.1]224.1.1.20 : [3], 1028 bytes, 0.38 ms (0.35 avg, 0% loss)
	 [<- 10.0.57.1]224.1.1.20 : [3], 1028 bytes, 0.38 ms (0.35 avg, 0% loss)
	 [<- 10.0.48.1]224.1.1.20 : [4], 1028 bytes, 0.40 ms (0.36 avg, 0% loss)

	 224.1.1.20 : xmt/rcv/%loss = 5/5/0%, min/avg/max = 0.30/0.36/0.40

	dnRouter# run ping multicast 227.1.1.1 source-ip 12.1.21.1 ttl 30 size 1000 count 5

	Type escape sequence to abort.
	Sending 5, 100-byte ICMP Echos to 224.1.1.20, timeout is 2 seconds:
	Packet sent with a source address of 12.1.21.1

	 [<- 10.0.48.1]224.1.1.20 : [0], 1028 bytes, 0.34 ms (0.34 avg, 0% loss)
	 [<- 10.0.57.1]224.1.1.20 : [0], 1028 bytes, 0.35 ms (0.34 avg, 0% loss)
	 [<- 10.0.48.1]224.1.1.20 : [1], 1028 bytes, 0.30 ms (0.32 avg, 0% loss)
	 [<- 10.0.57.1]224.1.1.20 : [1], 1028 bytes, 0.30 ms (0.32 avg, 0% loss)
	 [<- 10.0.48.1]224.1.1.20 : [2], 1028 bytes, 0.39 ms (0.34 avg, 0% loss)
	 [<- 10.0.57.1]224.1.1.20 : [2], 1028 bytes, 0.39 ms (0.34 avg, 0% loss)
	 [<- 10.0.48.1]224.1.1.20 : [3], 1028 bytes, 0.38 ms (0.35 avg, 0% loss)
	 [<- 10.0.57.1]224.1.1.20 : [3], 1028 bytes, 0.38 ms (0.35 avg, 0% loss)
	 [<- 10.0.48.1]224.1.1.20 : [4], 1028 bytes, 0.40 ms (0.36 avg, 0% loss)

	 224.1.1.20 : xmt/rcv/%loss = 5/5/0%, min/avg/max = 0.30/0.36/0.40

.. **Help line:** run ping for multicast

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+
