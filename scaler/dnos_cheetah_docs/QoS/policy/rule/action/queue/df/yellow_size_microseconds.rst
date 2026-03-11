qos policy rule action queue forwarding-class df yellow-size
------------------------------------------------------------

**Minimum user role:** operator

The configured size of the queue determines when packets (marked as either green or yellow) are tail-dropped once the queue reaches the configured queue size.

You can optionally set a smaller tail-drop threshold for yellow packets.

The queue size is configured in either milliseconds or microseconds.

To configure the queue size for the rule, use the following command:

**Command syntax: yellow-size [yellow-tail-drop-threshold-microseconds] [units]**

**Command mode:** config

**Hierarchies**

- qos policy rule action queue forwarding-class df

**Note**

- If not explicitly set, the yellow-size tail-drop threshold is equal to total queue size.

**Parameter table**

+-----------------------------------------+---------------------------------------+------------------+--------------+
| Parameter                               | Description                           | Range            | Default      |
+=========================================+=======================================+==================+==============+
| yellow-tail-drop-threshold-microseconds | yellow drop threshold in microseconds | 1-80000          | \-           |
+-----------------------------------------+---------------------------------------+------------------+--------------+
| units                                   |                                       | | microseconds   | microseconds |
|                                         |                                       | | milliseconds   |              |
+-----------------------------------------+---------------------------------------+------------------+--------------+

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
    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# yellow-size 500 milliseconds


**Removing Configuration**

To revert ot the default value:
::

    dnRouter(cfg-myPolicy1-rule-1-action-queue-af)# no yellow-size

**Command History**

+---------+-------------------------------------------------------+
| Release | Modification                                          |
+=========+=======================================================+
| 11.2    | Command introduced                                    |
+---------+-------------------------------------------------------+
| 15.1    | Added support for hp (high-priority) forwarding class |
+---------+-------------------------------------------------------+
