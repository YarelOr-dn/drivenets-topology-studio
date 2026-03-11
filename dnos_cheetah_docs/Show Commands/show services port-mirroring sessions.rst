show services port-mirroring sessions
-------------------------------------

**Minimum user role:** viewer

To display port-mirroring sessions configuration:



**Command syntax: show services port-mirroring sessions** [session-name]

**Command mode:** operational



..
	**Internal Note**

	- Port-mirroring session current configuration

**Parameter table**

The following is the displayed information from the command:

+-----------------------+--------------------------------------------------------+---------------------------------------------------+----------+
| Parameter             | Description                                            | Range                                             | Default  |
+=======================+========================================================+===================================================+==========+
| session-name          | The name of the port-mirroring session                 | String                                            | \-       |
+-----------------------+--------------------------------------------------------+---------------------------------------------------+----------+
| session-id            | The ID number of the session                           | 1..10                                             | \-       |
+-----------------------+--------------------------------------------------------+---------------------------------------------------+----------+
| admin-state           | The administrative state of the port-mirroring session | Enabled                                           | Disabled |
|                       |                                                        | Disabled                                          |          |
+-----------------------+--------------------------------------------------------+---------------------------------------------------+----------+
| destination-interface | The type of destination interface                      | ge<interface speed>-<A>/<B>/<C>                   | \-       |
|                       |                                                        | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>|          |
+-----------------------+--------------------------------------------------------+---------------------------------------------------+----------+
| source-interface      | The type of source interface                           | ge<interface speed>-<A>/<B>/<C>         \-        |          |
|                       |                                                        | ge<interface speed>-<A>/<B>/<C>.<sub-interface id>|          |
|                       |                                                        | bundle-<bundle id>                                |          |
|                       |                                                        | bundle-<bundle id>.<sub-interface id>             |          |
+-----------------------+--------------------------------------------------------+---------------------------------------------------+----------+
| direction             | The direction of the session                           | Ingress                                           | Both     |
|                       |                                                        | Egress                                            |          |
|                       |                                                        | Both                                              |          |
+-----------------------+--------------------------------------------------------+---------------------------------------------------+----------+

**Example**
::

	dnRouter# show services port-mirroring sessions IDS-Debug

	Session: IDS-Debug, Session ID: 1
		Description:
		Admin-state: Enabled
		Destination interface: ge100-1/0/25
		Source interfaces:
			ge100-1/0/20:
				Direction: Both
			ge100-1/0/21:
				Direction: Ingress

	dnRouter# show services port-mirroring sessions

	Session: IDS-Debug, Session ID: 1
		Description:
		Admin-state: Enabled
		Destination interface: ge100-1/0/25
		Source interfaces:
			ge100-1/0/20:
				Direction: Both
			ge100-1/0/21:
				Direction: Ingress

	Session: test, Session ID: 2
		Description: TokyoHQ_test1
		Admin-state: Disabled
		Destination interface: ge100-1/0/28
		Source interfaces:
			bundle-11177:
				Direction: Egress


.. **Help line:** Port-mirroring sessions current configuration

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+
