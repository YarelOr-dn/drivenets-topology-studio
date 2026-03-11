set gi grpc server listen port
------------------------------

**Minimum user role:** viewer

To configure the GI gRPC server listen port:

**Command syntax: set gi grpc server listen port [listen-port]**

**Command mode:** GI

**Note**

- The GI gRPC server listen port configuration can be set by the ZTP process through DHCP option 67.

**Example**
::

	gi# set gi grpc server listen port 52433

**Parameter table:**

.. **Help line:** Configure gi grpc server listen port.

+-------------+-----------------------------+-----------+---------+
|   Parameter | Description                 |     Range | Default |
+=============+=============================+===========+=========+
| listen-port | A single listen port number | <1..65535>| 52433   |
+-------------+-----------------------------+-----------+---------+

**Command History**

+---------+-------------------------------------+
| Release | Modification                        |
+=========+=====================================+
| 18.2    | Command introduced                  |
+---------+-------------------------------------+
