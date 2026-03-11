system ntp server key
---------------------

**Minimum user role:** operator

To configure the remote NTP server's authentication key.

**Command syntax: key [key-id]**

**Command mode:** configuration

**Hierarchies**

- system ntp

**Note**

- You can use any configured NTP authentication key.

**Parameter table**

+-------------+------------------------------------------------+----------+----------+
| Parameter   | Description                                    | Range    | Default  |
+=============+================================================+==========+==========+
| key-id      | Provide a unique key identifier that will serve| 1-65533  | \-       |
|             | to enable authentication on the NTP server.    |          |          |
+-------------+------------------------------------------------+----------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ntp
    dnRouter(cfg-system-ntp)# server 200.24.34.1 vrf default
    dnRouter(cfg-system-ntp-server)# key 10

    dnRouter(cfg-system-ntp)# server 2001:ab12::1 vrf mgmt0
    dnRouter(cfg-system-ntp-server)# key 3

**Removing Configuration**

To remove the NTP server key:
::

    dnRouter(cfg-system-ntp-server)# no key


.. **Help line:** Configure system ntp authentication keys


**Command History**

+-----------+-----------------------+
| Release   | Modification          |
+===========+=======================+
| 15.2      | Command introduced    |
+-----------+-----------------------+
