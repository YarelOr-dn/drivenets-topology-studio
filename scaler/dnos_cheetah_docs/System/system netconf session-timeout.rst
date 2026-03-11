system netconf session-timeout
------------------------------

**Minimum user role:** operator

To configure the maximum time (in minutes) allowed for Netconf sessions to be idle before they are disconnected. Idle is a session with no input from the client:

**Command syntax: session-timeout [session-timeout]**

**Command mode:** config

**Hierarchies**

- system netconf

**Note**

- The no command sets the values to default.

- An interval=0 means no timeout (inifinite session).

**Parameter table**

+-----------------+-------------------------------------------------------------------------------+-------+---------+
| Parameter       | Description                                                                   | Range | Default |
+=================+===============================================================================+=======+=========+
| session-timeout | maximum time allowed for NETCONF session to be idle before it is disconnected | 0-90  | 30      |
+-----------------+-------------------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# netconf
    dnRouter(cfg-system-netconf)# session-timeout 60


**Removing Configuration**

To revert the value to the default:
::

    dnRouter(cfg-system-netconf)# no session-timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.6    | Command introduced |
+---------+--------------------+
