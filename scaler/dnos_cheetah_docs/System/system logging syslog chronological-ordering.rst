system logging syslog chronological-ordering
--------------------------------------------
**Minimum user role:** operator

control chronological message ordering.

Syslog messages relayed to upstream servers from the various Syslog producers within the cluster are not guaranteed to arrive in chronological order. If chronological ordering is enabled, the relay will attempt to reorder the events according to the Syslog message timestamps.

Chronological ordering requires the relay to delay certain messages to ensure that the earlier messages are sent first. The maximum delay an event may experience before being logged and prepared for transmission to external servers, including the delay at the relay's queue and at the producer's queue, is controlled through the **max-delay** parameters.

The relay does not drop Syslog messages, and does not modify the timestamp, even if it fails to reorder them chronologically. For example, if due to temporary failure a producer does not succeed in sending its message for a period of time longer than the max delay, the event will be relayed to upstream servers even though a Syslog message with a later timestamp has already been sent.

Events kept in the relay's reordering queue may be lost if the relay is reset.

**Command syntax: chronological-ordering reorder <reorder>** max-delay <max-delay>

**Command mode:** config

**Note:**

- The 'no' command returns all chronological ordering configuration to their default settings.

- Setting to disable does not return the max-delay settings to their default settings.


**Parameter table:**

+------------------+--------------------+---------------+
| Parameter        | Values             | Default value |
+==================+====================+===============+
| reorder          | enabled / disabled | disabled      |
+------------------+--------------------+---------------+
| max-delay        | 1..30  seconds     | 5 seconds     |
+------------------+--------------------+---------------+

**Example:**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# logging
	dnRouter(cfg-system-logging)# syslog
	dnRouter(cfg-system-logging-syslog)# chronological-ordering reorder enabled
	dnRouter(cfg-system-logging-syslog)# chronological-ordering reorder enabled max-delay 3

	dnRouter(cfg-system-logging-syslog)# no chronological-ordering

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+