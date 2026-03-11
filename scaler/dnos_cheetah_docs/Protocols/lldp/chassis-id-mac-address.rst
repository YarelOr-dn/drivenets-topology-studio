protocols lldp chassis-id-mac-address
-------------------------------------

**Minimum user role:** operator

Configure lldp mandatory Chassis ID tlv information. 
When advertising Chassis ID with type mac-address (default system behavior), this configuration define which system mac address is to be advertised
* system-id - (default behavior) Signal the system-id mac address. A locally randomize mac address from DRIVENETS MAC pool, unique per router deployment
* chassis-mac - Advertise the router platform base mac address as chassis-id. Option is valid for Stand-Alone systems only

**Command syntax: chassis-id-mac-address [chassis-id-mac-address]**

**Command mode:** config

**Hierarchies**

- protocols lldp

**Parameter table**

+------------------------+----------------------------------------------------------------------------------+-----------------+-----------+
| Parameter              | Description                                                                      | Range           | Default   |
+========================+==================================================================================+=================+===========+
| chassis-id-mac-address | The Chassis ID is a mandatory TLV which identifies the chassis component of the  | | system-id     | system-id |
|                        | endpoint identifier associated with the transmitting LLDP agent.                 | | chassis-mac   |           |
|                        | chassis-id-mac-address defines which system mac is to be advertised when chassis |                 |           |
|                        | id type is mac-address                                                           |                 |           |
+------------------------+----------------------------------------------------------------------------------+-----------------+-----------+

**Example**
::

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# chassis-id-mac-address chassis-mac

    dnRouter#
    dnRouter# configure
    dnRouter(cfg)# protocols
    dnRouter(cfg-protocols)# lldp
    dnRouter(cfg-protocols-lldp)# chassis-id-mac-address system-d


**Removing Configuration**

To return chassis-id-mac-address to default value:
::

    dnRouter(cfg-protocols-lldp)# no chassis-id-mac-address

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| TBD     | Command introduced |
+---------+--------------------+
