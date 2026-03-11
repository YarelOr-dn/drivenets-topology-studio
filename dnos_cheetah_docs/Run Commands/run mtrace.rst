run mtrace
----------

**Minimum user role:** operator

You can use the command to run Mtrace to trace the route from a destination IP address to the root.

**Command syntax: run mtrace source-ip [source-ip] dest-host-ip [dest-host-ip] dest-ip-group [dest-ip-group]** response-ip [response-ip] ttl [ttl]

**Command mode:** operation 

**Note**

- The mtrace command must be in one-line format where all parameter are entered on the same line.

- The run mtrace source-ip [source-ip] dest-host-ip [dest-host-ip] dest-ip-group [dest-ip-group] runs the mtrace from [source-ip] to [dest-host-ip] via group dest-ip-group.

- The run mtrace source-ip [source-ip] dest-host-ip [dest-host-ip] dest-ip-group [dest-ip-group] response-ip [response-ip] runs the mtrace from [source-ip] to [dest-ip] via group dest-ip-group response to response-ip address.

.. - mtrace command is one-line format. meaning - all parameters should be entered on the same line

	- run mtrace source-ip [source-ip] dest-host-ip [dest-host-ip] dest-ip-group [dest-ip-group] - Run mtrace from [source-ip] to [dest-host-ip] via group dest-ip-group

	- run mtrace source-ip [source-ip] dest-host-ip [dest-host-ip] dest-ip-group [dest-ip-group] response-ip [response-ip] - Run mtrace from [source-ip] to [dest-host-ip] via group dest-ip-group respond to response-ip address

**Parameter table**

+---------------+-----------------------------------------+--------------------------------------------------------+---------+
| Parameter     | Description                             | Range                                                  | Default |
+===============+=========================================+========================================================+=========+
| source-ip     | The IP address of the source            | IPv4-host-address                                      |         |
+---------------+-----------------------------------------+--------------------------------------------------------+---------+
| dest-host-ip  | The IP address of the destination host  | IPv4-host-address                                      |         |
+---------------+-----------------------------------------+--------------------------------------------------------+---------+
| dest-ip-group | The IP address of the destination group | IPv4-multicast-group-address 224.0.1.0-239.255.255.255 |         |
+---------------+-----------------------------------------+--------------------------------------------------------+---------+
| response-ip   | The IP address of the response host     | IPv4-host-address                                      |         |
+---------------+-----------------------------------------+--------------------------------------------------------+---------+
| ttl           | The initial value of the IP header TTL  | 1-255                                                  | 127     |
+---------------+-----------------------------------------+--------------------------------------------------------+---------+

**Example**
::

	dnRouter# run mtrace source-ip 10.0.0.1 dest-host-ip 20.0.0.1 dest-ip-group 239.1.1.1

    Type escape sequence to abort.
	Mtrace from 10.0.0.1 to 20.0.0.1 via group 239.1.1.1
	From source (?) to destination (?)
	Querying full reverse path…

	0  20.0.0.1
	-1  192.168.24.5 PIM  [10.0.0.0/24]
	-2  192.168.24.6 PIM  [10.0.0.0/24]
	-3  192.168.52.5 PIM  [10.0.0.0/24]
	-4  192.168.15.6 PIM  [10.0.0.0/24]
	-5  10.0.0.1

	dnRouter# run mtrace source-ip 12.100.100.1 dest-host-ip 17.17.17.1 dest-ip-group 227.2.2.2 response-ip 12.24.24.1 ttl 4

    Type escape sequence to abort.
	Mtrace from 12.100.100.1 to 17.17.17.1 via group 227.2.2.2
	From source (?) to destination (?)
	Querying full reverse path…

	0  17.17.17.1
	-1  12.62.63.1 PIM  [12.100.100.0/24]
	-2  0.0.0.0 PIM  [12.100.100.0/24]
	-3  12.61.65.1 PIM  [12.100.100.0/24]
	-4  12.100.100.1 PIM  [12.100.100.1/32]

.. **Help line:** Run mtrace

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+


