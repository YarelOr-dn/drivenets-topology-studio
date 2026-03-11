interfaces irb
--------------

**Minimum user role:** operator

The IRB interfaces in DNOS provide ability to connect L2 service (like bridge-domain) to L3 routing.

The parameters that you can optionally configure on the IRB interface are the same parameters that you can configure on any interface. If you do not set these parameters, the default values will be assumed.

**Command syntax: irb<irb-id>**

**Command mode:** config

**Hierarchies**

- interfaces

**Note**

- Create an IRB interface, using this command.

- Bind the IRB interface to a bridge-domain service using the "router-interface" command.

**Parameter table**

+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+
| Parameter     | Description                                                                                                                                                                                                                | Range       | Default     |
+===============+============================================================================================================================================================================================================================+=============+=============+
| irb-id        | The IRB interface identifier. If the ID does not exist, this will create a new IRB interface with the specific identifier. If the ID exists, you will enter the existing IRB interface's configuration mode.               | 1..65535    | \-          |
+---------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------+-------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# interfaces
	dnRouter(cfg-if)# irb1
	dnRouter(cfg-if-irb1)#


**Removing Configuration**

To delete an irb interface:
::

	dnRouter(cfg-if)# no irb1


.. **Help line:** Configures irb interface

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 18.0    | Command introduced |
+---------+--------------------+
