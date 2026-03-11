system grpc port
----------------

**Minimum user role:** operator

To configure the port on which the server listens to new incoming connection requests.

**Command syntax: port [listen-port]**

**Command mode:** config

**Hierarchies**

- system grpc

**Note**

- Changing the port will disconnect all active connections and restart the gNMI service.

**Parameter table**

+-------------+---------------------------------+-------------+---------+
| Parameter   | Description                     | Range       | Default |
+=============+=================================+=============+=========+
| listen-port | listen port of gRPC/gNMI server | 9339, 50051 | 50051   |
+-------------+---------------------------------+-------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# grpc
    dnRouter(cfg-system-grpc)# port 9339


**Removing Configuration**

To revert port to default:
::

    dnRouter(cfg-system-grpc)# no port

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.2    | Command introduced |
+---------+--------------------+
