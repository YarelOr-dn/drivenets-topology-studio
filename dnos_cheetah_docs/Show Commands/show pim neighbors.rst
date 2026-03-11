show pim neighbors
------------------

**Minimum user role:** viewer

You can use this command to display the PIM neighbors information and status.



**Command syntax: show pim neighbors**

**Command mode:** operational


..
	**Internal Note**

	- In show pim neighbors the local loopback IP should also be presented.



**Example**
::

	dnRouter# show pim neighbors

	PIM neighbors:

	Flags: P - Proxy capable, DR - Designated Router.
	+-------------------+-----------------------------+----------+----------+
	| Neighbor Address  |Interface                    | Uptime   | Expires  |
	+-------------------+-----------------------------+----------+----------+
	| 12.1.6.1          | bundle-20.222               | 03:30:03 | 00:01:31 |
	| 12.2.6.21         | bundle-1                    | 03:29:56 | 00:01:21 |
	| 13.3.6.14         | ge100-1/1/0                 | 03:30:03 | 00:01:31 |
	| 15.1.7.33         | ge400-1/1/10.1              | 03:30:03 | 00:01:31 |
	+-------------------+-----------------------------+----------+----------+

.. **Help line:** Show PIM neighbors

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 12.0    | Command introduced |
+---------+--------------------+


