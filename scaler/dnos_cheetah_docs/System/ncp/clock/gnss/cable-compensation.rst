system ncp clock gnss cable-compensation
----------------------------------------

**Minimum user role:** operator

Set the GNSS cable length compensation value.

**Command syntax: cable-compensation [cable-compensation]**

**Command mode:** config

**Hierarchies**

- system ncp clock gnss

**Parameter table**

+--------------------+------------------------------------------------+----------------------+---------+
| Parameter          | Description                                    | Range                | Default |
+====================+================================================+======================+=========+
| cable-compensation | Cable length compensation value in nanoseconds | -100000000-100000000 | \-      |
+--------------------+------------------------------------------------+----------------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# gnss
    dnRouter(cfg-system-ncp-7-clk-gnss)# cable-compensation 100


**Removing Configuration**

Reset cable length compensation value to zero.
::

    dnRouter(cfg-system-ncp-7-clk-gnss)# no cable-compensation

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.3    | Command introduced |
+---------+--------------------+
