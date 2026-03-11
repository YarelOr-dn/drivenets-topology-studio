show mpls traffic-engineering pcep
----------------------------------

**Minimum user role:** viewer

The Path Computation Element Protocol (PCEP) is a TCP-based protocol that enables communication with a PCE server. PCEP defines a set of messages and objects used to manage PCEP sessions and to request and send paths for traffic-engineered LSPs.

**Command syntax: show mpls traffic-engineering pcep** peer [ipv4-address]

**Command mode:** operational



**Note**

- A PCE peer is marked as "delegated" if at least one tunnel is delegated to it.

..
 	-  a PCE peer will be marked as delegated if at least one tunnel is delegated to that PCE

	- set peer address to display detailed information for a specific pce


**Parameter table**

+--------------+----------------------------------------------------------------------------------------+---------+
| Parameter    | Description                                                                            | Range   |
+==============+========================================================================================+=========+
| ipv4-address | The IPv4 address of the PCE server. Detailed information will be displayed on the PCE. | A.B.C.D |
+--------------+----------------------------------------------------------------------------------------+---------+

**Example**
::

    dnRouter# show mpls traffic-engineering pcep

    | Address         | Priority        | Delegated       | State                   | Last-Error      |
    |-----------------+-----------------+-----------------+-------------------------+-----------------|
    | 192.168.168.7   | 5               | no              | idle                    | tcpFail         |
    | 10.10.75.188    | 10              | yes             | established             | tcpFail         |
    | 10.10.75.17     | 20              | no              | idle                    | tcpFail         |


	CL-203B(cfg)# show mpls traffic-engineering pcep peer 100.64.0.239
	PCE: 10 delegated
	server: 100.64.0.239
	source interface: lo0
	state: established
	last Error: tcpClosed
	lsp-state time: 60
	redelegation time: 30
	session id: 4
	sent keepalive time: 10
	received keepalive time: 30
	operational keepalive time: 10
	sent dead time: 40
	received dead time: 120
	operational dead time: 120
	up time: 3:08:29
	open: RX 2 TX 3
	keep-alive: RX 377 TX 1132
	report: RX 0 TX 109
	update: RX 0 TX 0
	error: RX 0 TX 0
	close: RX 0 TX 1

.. **Help line:**

**Command History**

+---------+----------------------------------------+
| Release | Modification                           |
+=========+========================================+
| 10.0    | Command introduced                     |
+---------+----------------------------------------+
| 11.5    | Changed the peer parameter to optional |
+---------+----------------------------------------+
| 19.0    | Fixed RST formatting and example table |
+---------+----------------------------------------+
