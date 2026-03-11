routing-options throttle-link-state-changes
-------------------------------------------

**Minimum user role:** operator

Use this command to aggregate multiple different interface state-changes to a single event. The routing protocols will treat all state changes as if they occurred at once.

**Command syntax: throttle-link-state-changes min-delay [min-delay] max-delay [max-delay]**

**Command mode:** config

**Hierarchies**

- routing-options

.. **Note**

	- Require max-delay > min-delay

	- Reconfiguring throttle-link-state-changes timers will immediately invoke any aggregated events. Any following interface state change will be delayed and aggregated according to new timers.

	- no command min-delay & max-delay to their default values

**Parameter table**

+-----------+------------------------------------------------------------------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                                                                                  | Range    | Default |
+===========+==============================================================================================================================+==========+=========+
| min-delay | The minimal delay to be added for any interface state-change.                                                                | 0..5000  | 0       |
|           | A value of 0 will result in no aggregation taking place and the protocol will react immediately upon interface state change. |          |         |
+-----------+------------------------------------------------------------------------------------------------------------------------------+----------+---------+
| max-delay | The maximum delay allowed for any interface state change.                                                                    | 1..60000 | 2000    |
+-----------+------------------------------------------------------------------------------------------------------------------------------+----------+---------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# throttle-link-state-changes min-delay 100 max-delay 2000


**Removing Configuration**

To revert min-delay and max-delay to their default value:
::

	dnRouter(cfg-routing-option)# no throttle-link-state-changes

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 15.1    | Command introduced |
+---------+--------------------+


