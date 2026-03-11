bfd interface min-rx
--------------------

**Minimum user role:** operator

The desired minimum receive interval is the time-frame in which a BFD packet is expected to arrive. 
If a BFD packet is not received within the configured interval, the uBFD session will go down.
The min-rx together with the multiplier, defines the detection time. 
The Local Detection timeout = negotiated Rx interval * remote_multiplier (the multiplier value received on the BFD packet).
The Remote Detection timeout = negotiated Tx interval * local_multiplier (the multiplier value configured locally for the session).

To configure the minimum receive interval:

**Command syntax: min-rx [min-rx]**

**Command mode:** config

**Hierarchies**

- protocols bfd  

**Note**

- All micro BFD sessions for the given bundle member will use the same session parameters

.. - the no command returns to default values

**Parameter table**

+---------------+-------------------------------------------------------------------------------------------------+------------+-------------+
|               |                                                                                                 |            |             |
| Parameter     | Description                                                                                     | Range      | Default     |
+===============+=================================================================================================+============+=============+
|               |                                                                                                 |            |             |
| min-rx        | The interval (in msec) in which a BFD packet is expected to arrive from the remote neighbor.    | 5..1700    | 300         |
+---------------+-------------------------------------------------------------------------------------------------+------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# interface bundle-1
	dnRouter(cfg-protocols-bfd-if)# min-rx 100


**Removing Configuration**

To return to the default value: 
::

	dnRouter(cfg-protocols-bfd-if)# no min-rx

**Command History**

+-------------+-------------------------------------+
|             |                                     |
| Release     | Modification                        |
+=============+=====================================+
|             |                                     |
| 11.2        | Command introduced                  |
+-------------+-------------------------------------+
|             |                                     |
| 15.1        | Added support for 5msec interval    |
+-------------+-------------------------------------+