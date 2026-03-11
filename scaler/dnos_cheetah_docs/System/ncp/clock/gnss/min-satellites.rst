system ncp clock gnss min-satellites
------------------------------------

**Minimum user role:** operator

Set the GNSS minimal satellites threshold.

**Command syntax: min-satellites [min-satellites]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss

**Parameter table**

+----------------+----------------------------------------------+-------+---------+
| Parameter      | Description                                  | Range | Default |
+================+==============================================+=======+=========+
| min-satellites | GNSS navigation minimal number of satellites | 1-8   | \-      |
+----------------+----------------------------------------------+-------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# min-satellites 4


**Removing Configuration**

Reset min-satellites value to default.
::

    dnRouter(cfg-system-ncp-7-clk-gnss)# no min-satellites

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
