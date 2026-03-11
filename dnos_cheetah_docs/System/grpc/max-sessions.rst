system grpc max-sessions
------------------------

**Minimum user role:** operator

To configure the maximum number of concurrent active gRPC sessions per system.

**Command syntax: max-sessions [max-sessions]**

**Command mode:** config

**Hierarchies**

- system grpc

**Note**

- If a client tries to connect which exceeds the maximum sessions configuration, the connection will be blocked.

- Decreasing the max-sessions configuration does not affect existing established sessions.

**Parameter table**

+--------------+--------------------------------------------------------------------+-------+---------+
| Parameter    | Description                                                        | Range | Default |
+==============+====================================================================+=======+=========+
| max-sessions | maximum number of supported concurrent gRPC sessions by the system | 1-20  | 20      |
+--------------+--------------------------------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc
    dnRouter(cfg-system-grpc)# max-sessions 3


**Removing Configuration**

To revert max-sessions to default:
::

    dnRouter(cfg-system-grpc)# no max-sessions

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.3    | Command introduced |
+---------+--------------------+
