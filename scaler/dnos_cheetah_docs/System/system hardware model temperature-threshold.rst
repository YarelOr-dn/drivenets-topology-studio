system ncp hardware model temperature-threshold
-----------------------------------------------

**Minimum user role:** operator

The temperature threshold protects the equipment from overheating. When one the temperature of the sensors crosses the specified threshold, an alarm is generated and the fan speed increases to maximum to cool off the equipment. However, once the equipment cools off, the fans return to the default speed, allowing the equipment to reheat. Whenever this happens, another event is generated. You can adjust the sensors' default temperature-threshold and prevent the massive generation of events.

To configure the temperature-threshold values:

**Command syntax: temperature-threshold sensor [sensor-name] [temperature-threshold]**

**Command mode:** config

**Hierarchies**

- system ncp hardware


**Note**

- Notice the change in prompt.

.. - no command removes the model temperature-threshold configuration.

	- in oreder to remove specific sensor, no command will indicate the sensor name.

	- There are no validations on hardware model type per node.

	- * agcxd40s is DNI NCP 40C platform

**Parameter table**

+-----------------------+----------------------------------+---------------+-----------------------+
| Parameter             | Description                      | Range         | Default               |
+=======================+==================================+===============+=======================+
| sensor-name           | The name of the sensor           | For agcxd40s: | \-                    |
|                       |                                  | temp_db_3v3   |                       |
|                       |                                  | temp_mac0_up  |                       |
+-----------------------+----------------------------------+---------------+-----------------------+
| temperature-threshold | The threshold of the temperature | 30-150°c      | temp_db_3v3 = 117 [C] |
|                       |                                  |               | temp_mac0_up = 90 [C] |
+-----------------------+----------------------------------+---------------+-----------------------+

**Example**
::

	dnRouter# configure
	dnRouter(cfg)# system
	dnRouter(cfg-system)# ncp 0
	dnRouter(cfg-system-ncp-0)# hardware model agcxd40s
	dnRouter(cfg-ncp-0-hardware-model)# temperature-threshold
	dnRouter(cfg-hardware-model-temperature)# sensor temp-db-3v3 100

**Removing Configuration**

To revert the router-id to default:
::

	dnRouter(cfg-ncp-0-hardware-model)# no temperature-threshold
	dnRouter(cfg-hardware-model-temperature)# no sensor temp_db_3v3 100

.. **Help line:** configure hardware model temperature-threshold for DNOS cluster nodes.

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.1    | Command introduced |
+---------+--------------------+
