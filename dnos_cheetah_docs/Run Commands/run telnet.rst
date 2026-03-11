run telnet
-----------

**Minimum user role:** viewer

The run telnet command checks the accessibility of a destination interface.

**Command syntax: run telnet [dest-ip]|[host-name]** {egress-interface [egress-interface] \| source-address [source-address]}

**Command mode:** operation 

**Note**

- The command is supported only for default VRF interfaces and for mgmt0 out-of-band interface.

- The parameters can all be specified in the same command.

.. - telnet command is one-line format. meaning - all parameters can be entered on the same line

	- run telnet [dest-ip] egress-interface - defines source IP of the packet to IP address of the egress interface. If "egress-interface"=mgmt0, linux command "telnet [ip-address]" should be run in a context of default NS, i.e. Telnet will run in out-of-band.

	- run telnet [dest-ip] source-address [source-address] - set source ip-address for Telnet packets.

	- If neither egress-interface nor source-address parameter was set, Telnet packets are generated via in-band management channel with source IP address according to default VRF routing table

	- ability to specify host-name instead of dest-ip address is supported 

	- in case telnet client disable - shall print error msg: please activate telnet client ...

**Parameter table**

The following are the parameters that you can use for the telnet command:

+------------------+--------------------------------------------------------+------------------------------------------------+
| Parameter        | Description                                            | Range                                          |
+==================+========================================================+================================================+
| dest-ip          | The IP address of the target host.                     | A.B.C.D                                        |
|                  |                                                        | x:x::x:x                                       |
+------------------+--------------------------------------------------------+------------------------------------------------+
| host-name        | The full or partial name of the target host to telnet. | String                                         |
+------------------+--------------------------------------------------------+------------------------------------------------+
| egress-interface | The name of the interface                              | All default VRF interfaces and mgmt0 interface |
+------------------+--------------------------------------------------------+------------------------------------------------+
| source-address   | IP address of the source                               | A.B.C.D                                        |
|                  |                                                        | x:x::x:x                                       |
+------------------+--------------------------------------------------------+------------------------------------------------+

**Example**
::

	dnRouter# run telnet 1.1.1.1
	dnRouter# run telnet 1.1.1.1 egress-interface lo0
	dnRouter# run telnet 1.1.1.1 source-address 5.5.5.5
	dnRouter# run telnet dnCoreRouter-2
	

.. **Help line:** run telnet

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+


