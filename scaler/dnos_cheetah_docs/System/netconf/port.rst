system netconf port
-------------------

**Minimum user role:** operator

To configure the port on which the server listens to new incoming connection requests.

**Command syntax: port [listen-port]**

**Command mode:** config

**Hierarchies**

- system netconf

**Note**

- The no command returns the port number to default.

- Changing the port will disconnect all active connections and restart the netconf service.

**Parameter table**

+-------------+----------------------------------------------------------------------------------+---------+---------+
| Parameter   | Description                                                                      | Range   | Default |
+=============+==================================================================================+=========+=========+
| listen-port | The port on which the server listens. If the port is not configured, the server  | 22, 830 | 830     |
|             | uses default port.                                                               |         |         |
+-------------+----------------------------------------------------------------------------------+---------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# netconf
    dnRouter(cfg-system-netconf)# port 22


**Removing Configuration**

To revert the port number to default:
::

    dnRouter(cfg-system-netconf)# no port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
