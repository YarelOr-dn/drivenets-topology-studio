system netconf max-sessions
---------------------------

**Minimum user role:** operator

To configure the maximum number of concurrent Netconf sessions to a Netconf server:

**Command syntax: max-sessions [max-sessions]**

**Command mode:** config

**Hierarchies**

- system netconf

**Note**

- The no command returns the number of maximum sessions to default.

- If client 13 will try to connect - it will be automatically blocked and an event will be generated.

- Decreasing the max-sessions configuration will not affect existing established sessions.

**Parameter table**

+--------------+---------------------------------------------------------------------------+-------+---------+
| Parameter    | Description                                                               | Range | Default |
+==============+===========================================================================+=======+=========+
| max-sessions | configure maximum number of concurrent NETCONF sessions to NETCONF server | 1-12  | 6       |
+--------------+---------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# netconf
    dnRouter(cfg-system-netconf)# max-sessions 5


**Removing Configuration**

To revert the max-sessions to default:
::

    dnRouter(cfg-system-netconf)# no max-sessions

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
