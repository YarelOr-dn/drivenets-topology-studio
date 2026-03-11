show system grpc subscriptions history
---------------------------------------

**Minimum user role:** viewer

To display subscribed paths for the last 100 terminated gRPC sessions per system:



**Command syntax: show system grpc subscriptions history** [id]

**Command mode:** operational



.. 
	**Internal Note**

	- command without secpecified session-id will output subscriptions for all 100 terminated gRPC sessions

**Parameter table**

+-----------+-------------------------------------------------------------+-------+
| Parameter | Description                                                 | Range |
+===========+=============================================================+=======+
| id        | Optionally filter the output for a specific session history | 0..99 |
+-----------+-------------------------------------------------------------+-------+

For each session, the following information is displayed:

+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Parameter  | Description                                                      | Range                                                                                                                                                                                                                                                             |
+============+==================================================================+===================================================================================================================================================================================================================================================================+
| Session-ID | The socket ID                                                    | 1..65535                                                                                                                                                                                                                                                          |
+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| User       | The gRPC user name                                               | String                                                                                                                                                                                                                                                            |
+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Request    | The type of session request                                      | SUBSCRIBE                                                                                                                                                                                                                                                         |
|            |                                                                  | GET                                                                                                                                                                                                                                                               |
+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Path       | The YANG path                                                    | -                                                                                                                                                                                                                                                                 |
+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Mode       | The subscription mode.                                           | Sample - upon subscription, the session will remain open forever and DNOS will stream UPDATES to the client periodically according to the requested configured sample interval. The sample rate is defined by the client as part of the SubscribeRequest message. |
|            | gNMI allows SAMPLE, ONCHANGE, POLL, ONCE                         |                                                                                                                                                                                                                                                                   |
+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Interval   | The intervals (in ns) in which DNOS sends updates to the client. | 5,000,000,000..3,600,000,000,000                                                                                                                                                                                                                                  |
+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show system grpc subscriptions history
	
	ID: 3
	Session-ID: 776
	User: test
	Request: SUBSCRIBE
	Mode: STREAM
	Subscriptions:
	
	Path: /drivenets-top/interfaces/interface[name='*']/oper-items/counters/ethernet-counters
	Mode: SAMPLE
	Interval: 5,000,000,000 ns
	
	Path: /drivenets-top/system/ncps/ncp[ncp-id='*']/oper-items/oper-status
	Mode: ON-CHANGE
	
	ID: 2
	Session-ID: 806
	User: test2
	Request: SUBSCRIBE
	Mode: STREAM
	Subscriptions:
	
	Path: /drivenets-top/system/cprl/is-is/oper-state/policer-drop-counter
	Mode: SAMPLE
	Interval: 5,000,000,000 ns
	

	ID: 65
	Session-ID: 684
	User: test3
	Request: SUBSCRIBE
	Mode: POLL
	
	Path: /drivenets-top/interfaces/interface[name='ge*']/oper-items/oper-status
	Path: /drivenets-top/interfaces/interface[name='ge*']/oper-items/admin-state

	ID: 32
	Session-ID: 722
	User: test5
	Request: SUBSCRIBE
	Mode: ONCE
	
	Path: /drivenets-top/interfaces/interface[name='ge*']/oper-items/description
	Path: /drivenets-top/interfaces/interface[name='fab-ncp*']/oper-items/description

	ID: 23
	Session-ID: 891
	User: test2
	Request: GET
	
	Path: /drivenets-top/system/oper-items/system-version
	Path: /drivenets-top/system/oper-items/system-uptime
	
	
	dnRouter# show system grpc subscriptions history 3 
	
	ID: 3
	Session-ID: 776
	User: test
	Subscriptions: 
	
	Path: /drivenets-top/interfaces/interface[name='*']/oper-items/counters/ethernet-counters
	Mode: SAMPLE
	Interval: 5,000,000,000 ns
	
	Path: /drivenets-top/system/ncps/ncp[ncp-id='*']/oper-items/oper-status
	Mode: ON-CHANGE
	
	

.. **Help line:** displays subscribed paths for last 100 terminated grpc sessions per system.

**Command History**

+---------+--------------------------------------------------------------------------------------------------------------+
| Release | Modification                                                                                                 |
+=========+==============================================================================================================+
| 13.0    | Command introduced                                                                                           |
+---------+--------------------------------------------------------------------------------------------------------------+
| 15.0    | Updated command syntax (session-id to id) and updated the 'Mode' parameter to support ONCHAGE, POLL and ONCE |
+---------+--------------------------------------------------------------------------------------------------------------+


