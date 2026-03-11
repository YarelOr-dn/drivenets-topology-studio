system aaa-server tacacs timers retry-time
------------------------------------------

**Minimum user role:** operator

Prevents a failed TACACS server from being retried too soon. If an TACACS server is marked as failed, it will not be used for TACACS requests until the retry time has expired. Once the retry time has expired, the TACACS server may be marked as available to accept new TACACS requests

**Command syntax: retry-time [retry-time]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs timers

**Note**
- Notice the change in prompt.

.. - Retry-time -prevent a failed TACACS server from being retried too soon. If a TACACS server is marked as failed, it will not be used for TACACS requests until the retry time has expired. Once the retry time has expired, the TACACS server may be marked as available to accept TACACS new requests

    - If the delay is set to zero, the retry delay is disabled and TACACS server is always attempted

    - no command returns retry-timer to the default value


**Parameter table**

+------------+----------------------------------------------------------------------------------+----------+---------+
| Parameter  | Description                                                                      | Range    | Default |
+============+==================================================================================+==========+=========+
| retry-time | The time (in seconds) that the NCR waits after a server is marked as failed,     | 60..3600 | 1200    |
|            | before reattempting to connect to it.                                            |          |         |
|            | A value of zero disables the retry-time delay and all servers are always         |          |         |
|            | attempted.                                                                       |          |         |
+------------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# timers
    dnRouter(cfg-aaa-tacacs-timers)# retry-time 60


**Removing Configuration**

To revert the retry-time to the default:
::

    dnRouter(cfg-aaa-tacacs-timers)# no retry-time

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
