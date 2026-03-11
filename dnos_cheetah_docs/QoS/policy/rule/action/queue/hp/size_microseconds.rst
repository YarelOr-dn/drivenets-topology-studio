qos policy rule action queue forwarding-class hp size
-----------------------------------------------------

**Minimum user role:** operator

The configured size of the queue determines when packets (marked as either green or yellow) are tail-dropped once the queue reaches the configured queue size.

You can optionally set a smaller tail-drop threshold for yellow packets.

The queue size is configured in either milliseconds or microseconds. The actual size of the queue is measured in bytes. The conversion is calculated as follows:

For af/df forwarding classes: - according to port speed

[(port speed x queue-size) x (knob-unit)]/8

Example 1 - for milliseconds:

port speed = 100 Gbps

queue-size = 20 milliseconds => knob-unit 1/1000

[(100 Gbps x 20 ms) x 1/1000] / 8 = 0.25 GB (= 250 MB)

Example 2 - for microseconds:

port speed = 100 Gbps

queue-size = 20,000 microseconds => knob-unit 1/1,000,000

[(100 Gbps x 20 s) x 1/1,000,000] / 8 = 0.25 GB (= 250 MB)

For sef/ef forwarding classes: - according to max bandwidth

Same calculation as for af/df queues, multiplied by the shaper value (max-bandwidth).

port speed = 100 Gbps

queue-size = 20 milliseconds => knob-unit 1/1000

max-bandwidth = 25%

[(100 Gbps x 2 ms) x 1/1000] / 8 = 0.025 GB (= 25 MB) x 25% = 6.25 MB

To configure the queue size for the rule, use the following command:

**Command syntax: size [queue-size-microseconds] [units]**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue forwarding-class hp

**Note**

- If not explicitly set, the yellow-size tail-drop threshold is equal to total queue size.

**Parameter table**

+-------------------------+----------------------------+------------------+--------------+
| Parameter               | Description                | Range            | Default      |
+=========================+============================+==================+==============+
| queue-size-microseconds | queue size in microseconds | 1-80000          | 10000        |
+-------------------------+----------------------------+------------------+--------------+
| units                   |                            | | microseconds   | microseconds |
|                         |                            | | milliseconds   |              |
+-------------------------+----------------------------+------------------+--------------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# qos
    dnRouter(cfg-qos)# policy myPolicy1
    dnRouter(cfg-qos-policy-myPolicy1)# rule 1
    dnRouter(cfg-policy-myPolicy1-rule-1)# match traffic-class myTrafficClassMap1
    dnRouter(cfg-policy-myPolicy1-rule-1)# action
    dnRouter(cfg-myPolicy1-rule-1-action)# queue forwarding-class
    dnRouter(cfg-myPolicy1-rule-1-action-queue)# af
    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# size 500 milliseconds


**Removing Configuration**

To revert ot the default value:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# no size

**Command History**

+---------+-------------------------------------------------------+
| Release | Modification                                          |
+=========+=======================================================+
| 11.2    | Command introduced                                    |
+---------+-------------------------------------------------------+
| 15.1    | Added support for hp (high-priority) forwarding class |
+---------+-------------------------------------------------------+
