system ncp clock synce ql-based-select
--------------------------------------

**Minimum user role:** operator

Enable or disable synchronous ethernet QL feature.

**Command syntax: ql-based-select [enable]**

**Command mode:** config

**Hierarchies**

- system ncp clock synce

**Parameter table**

+-----------+------------------------------------------+--------------+---------+
| Parameter | Description                              | Range        | Default |
+===========+==========================================+==============+=========+
| enable    | Sets the sync-ethernet QL feature state. | | disabled   | enabled |
|           |                                          | | enabled    |         |
+-----------+------------------------------------------+--------------+---------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# system
    dnRouter(cfg-system)# ncp 7
    dnRouter(cfg-system-ncp-7)# clock
    dnRouter(cfg-system-ncp-7-clk)# synce
    dnRouter(cfg-system-ncp-7-clk-synce)# ql-based-select enabled


**Removing Configuration**

To revert the ql-based-select state to its default value:
::

    dnRouter(cfg-system-ncp-7-clk-synce)# no ql-based-select

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 17.2    | Command introduced |
+---------+--------------------+
