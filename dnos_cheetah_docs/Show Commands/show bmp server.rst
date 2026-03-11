show bmp server
---------------

**Minimum user role:** viewer

The following command displays detailed information of a bmp session:



**Command syntax: show bmp server** [server-id]

**Command mode:** operational



**Note**

- support auto-complete for configured server-id


**Parameter table**

+-----------+---------------------------------------------------------------------------------------------------------+-------+---------+
| Parameter | Description                                                                                             | Range | Default |
+===========+=========================================================================================================+=======+=========+
| server-id | The id of the bmp server.                                                                               | 1..5  | \-      |
|           | If a server-id is not specified, detailed information for all configured bmp servers will be displayed. |       |         |
+-----------+---------------------------------------------------------------------------------------------------------+-------+---------+

**Example**
::

	dnRouter# show bmp server

	BMP server-id: 1
		Host address: 100.64.0.163
		Host port: 5000
		Vrf: default
		State: Up,  Time: 45m18s
		Number of exported bgp neighbors: 4
		Class-of-Service: 16

		Route-monitoring:
			adj-in pre-policy
			adj-in post-policy

		Session Hold-down: inactive
			Initial backoff interval: 30 seconds
			Maximum backoff interval: 720 seconds

		Session dampening: in-active

		Message statistics:
			Initiation: 3
			Peer-up: 12
			Peer-down: 0
			Termination: 1
			Route-monitoring: 128
			Pending: 904


	BMP server-id: 1
		Host address: 202.202.88.8
		Host port: 5001
		Vrf: default
		State: Idle, reconnect is set to 31 seconds, remaining time: 29 seconds
		Number of exported bgp neighbors: 1
		Class-of-Service: 16
	
		Route-monitoring:
	
		Session Hold-down: active
			Initial backoff interval: 30 seconds
			Maximum backoff interval: 720 seconds

		Session dampening: in-active

		Message statistics:
			Initiation: 0
			Peer-up: 0
			Peer-down: 0
			Termination: 0
			Route-monitoring: 0
			Pending: 0

.. **Help line:** displays detailed bmp session information

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+

