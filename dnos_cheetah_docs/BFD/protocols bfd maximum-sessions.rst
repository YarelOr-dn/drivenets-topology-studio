protocols bfd maximum-sessions
------------------------------

**Minimum user role:** operator

You can control the number of concurrent BFD sessions by setting thresholds to generate system event notifications. 
Only established sessions are counted. When a threshold is crossed, a system-event notification is generated allowing you to take action, if necessary. 
Micro-BFD sessions are excluded from this count. System supports micro-BFD sessions on every system port.
Once the threshold is crossed, a warning system-event will be sent (every 30 seconds).

To configure thresholds for BFD sessions:


**Command syntax: maximum-sessions [max-sessions] threshold [threshold]**

**Command mode:** config

**Hierarchies**

- protocols bfd  

.. **Note**

.. - the no command returns to default values

**Parameter table**

+-----------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                 |                                                                                                                                           |             |             |
| Parameter       | Description                                                                                                                               | Range       | Default     |
+=================+===========================================================================================================================================+=============+=============+
|                 |                                                                                                                                           |             |             |
| max-sessions    | The maximum number of concurrent BFD sessions. When this threshold is crossed, a system-event notification is generated every 30 seconds. | 0..65535    | 2000        |
|                 |                                                                                                                                           |             |             |
|                 | A value of 0 means no limit.                                                                                                              |             |             |
+-----------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
|                 |                                                                                                                                           |             |             |
| threshold       | A percentage (%) of max-sessions to give you advance notice that the number of BFD sessions is reaching the maximum level.                | 1..100      | 75          |
|                 |                                                                                                                                           |             |             |
|                 | When this threshold is crossed, a system event notification is generated.                                                                 |             |             |
+-----------------+-------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+


**Example**
::

	dnRouter# configure
	dnRouter(cfg)# protocols
	dnRouter(cfg-protocols)# bfd
	dnRouter(cfg-protocols-bfd)# maximum-sessions 500 threshold 75

In the above example, the maximum number of sessions is set to 500 and the threshold is set to 75%. This means that when the number of sessions reaches 375 (500x75%), a system-event notification will be generated that the 75% threshold has been crossed. If you do nothing, you will not receive another notification until the number of sessions reaches 500.

**Removing Configuration**

To return to the default value: 
::

	dnRouter(cfg-protocols)# no maximum-sessions



**Command History**

+-------------+--------------------------------------------+
|             |                                            |
| Release     | Modification                               |
+=============+============================================+
|             |                                            |
| 11.2        | Command introduced                         |
+-------------+--------------------------------------------+
|             |                                            |
| 15.1        | Added support for 2000 maximum sessions    |
+-------------+--------------------------------------------+