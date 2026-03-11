show system grpc subscriptions
------------------------------

**Minimum user role:** viewer

To display subscribed paths for active gRPC sessions:



**Command syntax: show system grpc subscriptions** [session-id]

**Command mode:** operational



.. 
	**Internal Note**

	- command without secpecified session-id will output subscriptions for all active gRPC sessions

**Parameter table**

+------------+----------------------------------------------------------------------------------+----------+
| Parameter  | Description                                                                      | Range    |
+============+==================================================================================+==========+
| session-id | Optionally filter the output for a specific session (according to the socket-id) | 1..65535 |
+------------+----------------------------------------------------------------------------------+----------+

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
| Path       | The YANG path                                                    | \-                                                                                                                                                                                                                                                                |
+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Mode       | The subscription mode.                                           | Sample - upon subscription, the session will remain open forever and DNOS will stream UPDATES to the client periodically according to the requested configured sample interval. The sample rate is defined by the client as part of the SubscribeRequest message. |
|            | gNMI allows SAMPLE, ONCHANGE, POLL, ONCE                         |                                                                                                                                                                                                                                                                   |
+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Interval   | The intervals (in ns) in which DNOS sends updates to the client. | 5,000,000,000..3,600,000,000,000                                                                                                                                                                                                                                  |
+------------+------------------------------------------------------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**Example**
::

	dnRouter# show system grpc subscriptions
	
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
	
	
	Session-ID: 806
	User: test2
	Request: SUBSCRIBE
	Mode: STREAM
	Subscriptions:
	
	Path: /drivenets-top/system/cprl/is-is/oper-state/policer-drop-counter
	Mode: SAMPLE
	Interval: 5,000,000,000 ns

	Session-ID: 684
	User: test3
	Request: SUBSCRIBE
	Mode: POLL
	Subscriptions:
	
	Path: /drivenets-top/interfaces/interface[name='ge*']/oper-items/oper-status
	Path: /drivenets-top/interfaces/interface[name='ge*']/oper-items/admin-state

	Session-ID: 324
	User: test5
	Request: SUBSCRIBE
	Mode: ONCE
	Subscriptions:
	
	Path: /drivenets-top/interfaces/interface[name='ge*']/oper-items/description
	Path: /drivenets-top/interfaces/interface[name='fab-ncp*']/oper-items/description
	
	
	
	dnRouter# show system grpc subscriptions 776 
	
	Session-ID: 776
	User: test
	Subscriptions: 
	
	Path: /drivenets-top/interfaces/interface[name='*']/oper-items/counters/ethernet-counters
	Mode: SAMPLE
	Interval: 5,000,000,000 ns
	
	Path: /drivenets-top/interfaces/interface[name='*']/oper-items/counters/fabric-counters
	Mode: SAMPLE
	Interval: 5,000,000,000 ns
	
	

.. **Help line:** displays subscribed paths for active grpc sessions per system.

**Command History**

+---------+-----------------------------------------------------------------+
| Release | Modification                                                    |
+=========+=================================================================+
| 11.0    | Command introduced                                              |
+---------+-----------------------------------------------------------------+
| 15.0    | Updated the 'Mode' parameter to support ONCHANGE, POLL and ONCE |
+---------+-----------------------------------------------------------------+


