protocols rsvp timers retry
---------------------------

**Minimum user role:** operator

Once path is set, the device will attempt to establish an LSP tunnel. If it fails to establish the LSP tunnel (for example if there is no CSPF solution or the path signaling fails), the NCR will try again after the interval timer expires. It will continue retrying a number of times set by the limit parameter and then it will stop. When this happens, you must manually clear the tunnels (see "clear rsvp tunnels") or apply a configuration change to the tunnel. The NCR will attempt to establish a new LSP tunnel.

If there are multiple path-options, "retry interval" and "limit" refer to the full set of path-options. If a path option fails, the following path option is immediately processed. If all path options fail, the retry interval timer starts and attempts counter advances. The next retry starts from the first path-option. When the attempts counter reaches the limit NCR will seize to establish the tunnel.

To configure the timer:

**Command syntax: retry {interval [interval], limit [limit]}**

**Command mode:** config

**Hierarchies**

- protocols rsvp timers

**Note**
-  0 means that there is no limit. The NCR will attempt to establish an LSP tunnel until it is successful.

-  At least one parameter is mandatory (either interval or limit)

.. -  no retry interval - return interval to default value

.. -  no retry limit - return limit to default value

.. -  no retry interval limit - return both interval and limit to default value

.. -  no retry - return both interval and limit to default value

**Parameter table**

+-----------+-------------+-------+---------+
| Parameter | Description | Range | Default |
+===========+=============+=======+=========+
| interval  | interval    | 1-600 | 45      |
+-----------+-------------+-------+---------+
| limit     | limit       | 0-650 | 0       |
+-----------+-------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# timers
    dnRouter(cfg-protocols-rsvp-timers)# retry interval 60

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# rsvp
    dnRouter(cfg-protocols-rsvp)# timers
    dnRouter(cfg-protocols-rsvp-timers)# retry-interval 30 limit 20


**Removing Configuration**

To revert to the default interval value:
::

    dnRouter(cfg-protocols-rsvp-timers)# no retry interval

To revert to the default limit value:
::

    dnRouter(cfg-protocols-rsvp-timers)# no retry limit

To revert both parameters to their default value:
::

    dnRouter(cfg-protocols-rsvp-timers)# no retry

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 9.0     | Command introduced |
+---------+--------------------+
