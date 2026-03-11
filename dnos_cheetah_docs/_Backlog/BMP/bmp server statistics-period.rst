bmp server statistics-period
----------------------------

**Command syntax: statistics-period [statistics-period]**

**Description:** Configure the rate of which statistics messages are sent to server

Set 0 to disable statistics messages

**CLI example:**
::

	dnRouter# configure
	dnRouter(cfg)# routing-options
	dnRouter(cfg-routing-option)# bmp server 1
	dnRouter(cfg-routing-option-bmp)# statistics-period 60


	dnRouter(cfg-routing-option-bmp)# no statistics-period

**Command mode:** config

**TACACS role:** operator

**Note:**

- no command return statistics-period to default value

**Help line:** Set bmp statistics message period

**Parameter table:**

+-------------------+---------------------+-----------------------------------+--------------------+
| Parameter         | Values              | Default value                     | Comments           |
+===================+=====================+===================================+====================+
| statistics-period | 0..3600             | 30                                |  seconds           |
+-------------------+---------------------+-----------------------------------+--------------------+
