services sla-probe history-size - N/A for this version
------------------------------------------------------

**Command syntax: owner [owner-name] test [test-name]** history-size [history-size]

**Description:** Sets the number of probe history entries in the history results table

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# services
	dnRouter(cfg-srv)# sla-probe 
	dnRouter(cfg-srv-sla)# owner MyOwner test MyTest1 history-size 512
	
	dnRouter(cfg-srv-sla)# no owner MyOtherOwner test MyTest1 history-size
	
**Command mode:** operational

**TACACS role:** operator

**Note:** no commands revert the sla-probe history-size to its default value

**Help line:** configure number of stored history entries

**Parameter table:**

+--------------+------------------+---------------+
| Parameter    | Values           | Default value |
+==============+==================+===============+
| owner-name   | string [32 char] |               |
+--------------+------------------+---------------+
| test-name    | string [32 char] |               |
+--------------+------------------+---------------+
| history-size | 1-1024           | 300           |
+--------------+------------------+---------------+
