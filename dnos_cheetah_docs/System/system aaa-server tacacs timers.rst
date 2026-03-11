system aaa-server tacacs timers
-------------------------------

**Minimum user role:** operator

TACACS+ servers have two timers that can be configured individually:

Retry-time – prevents a failed server from being retried too soon. If a server is marked as "failed", it will not be used for requests until the retry time has expired. Once the retry time expires, the server may be marked as available to accept new requests.

Hold-down - prevents all requests from being sent to any AAA servers. It is triggered when all the TACACS authentication, or all TACACS authorization, or all TACACS accounting servers are in unavailable state: requests are suppressed for a period of time in order to avoid a connection timeout.

If the delay is set to zero, the hold-down delay is disabled ans all TACACS servers are attempted.

To configure the TACACS+ timers, enter timers configuration mode:


**Command syntax: timers**

**Command mode:** config

**Hierarchies**

- system aaa-server tacacs

**Note**
- Notice the change in prompt.

.. - Retry-time -prevent a failed TACACS server from being retried too soon. If a TACACS server is marked as failed, it will not be used for TACACS requests until the retry time has expired. Once the retry time has expired, the TACACS server may be marked as available to accept TACACS new requests.

    - If the delay is set to zero, the retry delay is disabled and TACACS server is always attempted

    - Hold-down - prevent all TACACS requests from being sent to any TACACS servers. The hold-down delay is triggered when all the TACACS authentication, or all the TACACS authorization, or all the TACACS accounting servers are found to be in an unavailable state. The purpose of this delay is to limit unnecessary delays due to TACACS requests being sent to unavailable servers incurring the connection timeout.

    - If the delay is set to zero, the hold down delay is disabled and all TACACS servers are attempted

    - Retry-time and hold-down can be set individually, together and in any order.

    - no command returns timers to their default values


**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# aaa-server
    dnRouter(cfg-system-aaa)# tacacs
    dnRouter(cfg-system-aaa-tacacs)# timers
    dnRouter(cfg-aaa-tacacs-timers)#


**Removing Configuration**

To revert TACACS timers to default:
::

    dnRouter(cfg-aaa-tacacs-timers)# no timers

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 11.0    | Command introduced |
+---------+--------------------+
