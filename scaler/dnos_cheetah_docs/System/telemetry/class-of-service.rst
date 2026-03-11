system telemetry class-of-service
---------------------------------

**Minimum user role:** operator

Set the DSCP values for DNOS dial-out telemetry:

**Command syntax: class-of-service [class-of-service]**

**Command mode:** config

**Hierarchies**

- system telemetry

**Parameter table**

+------------------+-------------------------------------+-------+---------+
| Parameter        | Description                         | Range | Default |
+==================+=====================================+=======+=========+
| class-of-service | DSCP of generated telemetry packets | 0-63  | 16      |
+------------------+-------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# telemetry
    dnRouter(cfg-system-telemetry)# class-of-service 32


**Removing Configuration**

To revert DSCP to default:
::

    dnRouter(cfg-system-telemetry)# no class-of-service

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 19.10   | Command introduced |
+---------+--------------------+
