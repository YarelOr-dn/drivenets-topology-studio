protocols ldp session protection timeout
----------------------------------------

**Minimum user role:** operator

Defines the amount of time (in seconds) that the session protection Targeted-Hello should be retained once Link-Hello timed out.
To configure session protection timeout:

**Command syntax: timeout [timeout]**

**Command mode:** config

**Hierarchies**

- protocols ldp session protection

**Note**

- Setting the timer value to 0, results in an infinite timeout. T-Hello will remain as long as the LDP TCP session is active.

**Parameter table**

+-----------+---------------------------------------------------------------------+---------+---------+
| Parameter | Description                                                         | Range   | Default |
+===========+=====================================================================+=========+=========+
| timeout   | Time duration to retain targeted-hello after link-hello had stopped | 0-65535 | 0       |
+-----------+---------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# ldp
    dnRouter(cfg-protocols-ldp)# session protection
    dnRouter(cfg-protocols-ldp-session-prot)# timeout 360


**Removing Configuration**

To revert to default value:
::

    dnRouter(cfg-protocols-ldp-session-prot)# no timeout

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 16.1    | Command introduced |
+---------+--------------------+
