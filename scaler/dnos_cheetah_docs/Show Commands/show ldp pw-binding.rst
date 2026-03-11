show ldp pw-binding
-------------------

**Minimum user role:** viewer

To display the contents of the Label Information Base (LIB) supporting the pseudowire FEC.

.. neighbor - display brief view for binding matching neighbor address
.. fec-value - display brief view for binding matching fec-value

The output includes:

- Neighbor Address - The IPv4 address which sends /receives the FEC.
- Adv/Rec - If it is an advertised FEC or a received FEC.
- FEC-TYPE - The DNOS supported FEC types for L2VPN: FEC-128.
- FEC-Value - The Pseudowire-ID for FEC-128.
- PW-enc - The Pseudowire encapsulation, either ethernet (type 5) or VLAN (type 4).
- Label - Local label value (for Adv) or the remote label value (for Rec).
- Time - The time since this FEC was either advertised or received.

**Command syntax: show ldp pw-binding** neighbor-address [ipv4-address] fec-value [fec-value]

**Command mode:** operational

.. **Note**

**Parameter table**

+--------------+--------------------------------+---------------+---------+
| Parameter    | Description                    | Range         | Default |
+==============+================================+===============+=========+
| ipv4-address | The neighbors IP address.      | A.B.C.D       | \-      |
+--------------+--------------------------------+---------------+---------+
| fec-value    | The Pseudowire-ID for FEC-128. | 1..4294967295 | \-      |
+--------------+--------------------------------+---------------+---------+

**Example**
::

	dnRouter# show ldp pw-binding

	+------------------+---------+----------+-----------+------------+-------+------+--------+----------+----------+
	| Neighbor Address | Adv/Rec | FEC-Type | FEC-Value | PW-enc     | Label | MTU  | C Word | Group Id | Time     |
	+------------------+---------+----------+-----------+------------+-------+------+--------+----------+----------+
	| 2.2.2.2          | adv     | FEC-128  | 222       | Eth Tagged | 57222 | 1500 | 1      | 0        | 02w6d14h |
	| 2.2.2.2          | rec     | FEC-128  | 222       | Eth Tagged | 57226 | 1500 | 1      | 0        | 02w6d01h |
	| 4.4.4.4          | adv     | FEC-128  | 444       | Ethernet   | 57231 | 1500 | 1      | 0        | 01w3d14h |
	| 4.4.4.4          | rec     | FEC-128  | 444       | Ethernet   | 41579 | 1500 | 1      | 0        | 01w3d01h |
	+------------------+---------+----------+-----------+------------+-------+------+--------+----------+----------+

	dnRouter# show ldp pw-binding neighbor-address 2.2.2.2

	+------------------+---------+----------+-----------+------------+-------+------+--------+----------+----------+
	| Neighbor Address | Adv/Rec | FEC-Type | FEC-Value | PW-enc     | Label | MTU  | C Word | Group Id | Time     |
	+------------------+---------+----------+-----------+------------+-------+------+--------+----------+----------+
	| 2.2.2.2          | adv     | FEC-128  | 222       | Eth Tagged | 57222 | 1500 | 1      | 0        | 02w6d14h |
	| 2.2.2.2          | rec     | FEC-128  | 222       | Eth Tagged | 57226 | 1500 | 1      | 0        | 02w6d01h |
	+------------------+---------+----------+-----------+------------+-------+------+--------+----------+----------+

	dnRouter# show ldp pw-binding fec-value 444

	+------------------+---------+----------+-----------+------------+-------+------+--------+----------+----------+
	| Neighbor Address | Adv/Rec | FEC-Type | FEC-Value | PW-enc     | Label | MTU  | C Word | Group Id | Time     |
	+------------------+---------+----------+-----------+------------+-------+------+--------+----------+----------+
	| 4.4.4.4          | adv     | FEC-128  | 444       | Ethernet   | 57231 | 1500 | 1      | 0        | 01w3d14h |
	| 4.4.4.4          | rec     | FEC-128  | 444       | Ethernet   | 41579 | 1500 | 1      | 0        | 01w3d01h |
	+------------------+---------+----------+-----------+------------+-------+------+--------+----------+----------+

.. **Help line:** Displays the contents of the LIB

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
