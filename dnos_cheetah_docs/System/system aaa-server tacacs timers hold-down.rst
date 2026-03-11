system aaa-server tacacs timers hold-down
-----------------------------------------

**Minimum user role:** operator

Hold-down prevents all requests from being sent to any AAA servers. It is triggered when all the TACACS authentication, or all TACACS authorization, or all TACACS accounting servers with admin-state 'enabled' are in unavailable state: requests are suppressed for a period of time in order to avoid a connection timeout.

If the delay is set to zero, the hold-down delay is disabled ans all TACACS servers are attempted.

For TACACS+, the timer is triggered when all the servers of a specific type are unavailable (e.g. all authentication servers, all authorization servers, or all accounting servers).

If a RADIUS server is used for authentication, the RADIUS hold-down timer is configured separately. The purpose of this state is to prevent unnecessary delays due to AAA requests being sent to unavailable servers incurring the connection timeout.

To configure the TACACS+ hold-down timer:


**Command syntax: hold-down [hold-down]**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs timers

**Note**
- Notice the change in prompt.

.. -  Hold-down - prevent all AAA requests from being sent to any AAA servers. The TACACS hold-down timer is triggered when all the TACACS authentication, or all the TACACS authorization, or all the TACACS accounting servers are found to be in an unavailable state. If a RADIUS authentication is used, the RADIUS hold-down timer is configured separately. The purpose of this state is to prevent unnecessary delays due to AAA requests being sent to unavailable servers incurring the connection timeout.

    - If the delay is set to zero, the hold down delay is disabled and all TACACS servers are attempted.

    - The no command returns hold-down timers to their default values.


**Parameter table**

+-----------+----------------------------------------------------------------------------------+----------+---------+
| Parameter | Description                                                                      | Range    | Default |
+===========+==================================================================================+==========+=========+
| hold-down | The time (in seconds) that the system suppresses any AAA requests to any AAA     | 60..1200 | 600     |
|           | servers.                                                                         |          |         |
|           | A value of zero disables the hold-down delay and all servers are attempted.      |          |         |
+-----------+----------------------------------------------------------------------------------+----------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# timers
    dnRouter(cfg-aaa-tacacs-timers)# hold-down 60


**Removing Configuration**

To revert the hold-time to the default value:
::

    dnRouter(cfg-aaa-tacacs-timers)# no hold-down

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
