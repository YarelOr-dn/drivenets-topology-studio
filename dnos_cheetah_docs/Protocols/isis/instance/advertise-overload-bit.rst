protocols isis instance advertise overload-bit
----------------------------------------------

**Minimum user role:** operator

Administratively set IS-IS to advertise the overload bit. By setting the overload bit in its LSPs, the IS router signals other routers not to use it as an intermediate hop in their SPF calculations.

To administratively advertise the overload bit:


**Command syntax: advertise overload-bit [admin-state]**

**Command mode:** config

**Hierarchies**

- protocols isis instance

**Note**

- This option is disabled by default and is only supported if metric-style is "wide".

- The behavior is independent of the IS-IS overload behavior. The overload-bit will be advertised as long as the configuration is enabled.

**Parameter table**

+-------------+---------------------------------------------+--------------+----------+
| Parameter   | Description                                 | Range        | Default  |
+=============+=============================================+==============+==========+
| admin-state | Administratively advertise the overload bit | | enabled    | disabled |
|             |                                             | | disabled   |          |
+-------------+---------------------------------------------+--------------+----------+

**Example**
::

    dnRouter# configure
    dnRouter(cfg)# protocols isis
    dnRouter(cfg-protocols-isis)# instance area_1
    dnRouter(cfg-protocols-isis-inst)# advertise overload-bit enabled


**Removing Configuration**

To revert admin-state to default:
::

    dnRouter(cfg-isis-inst-afi)# no advertise overload-bit

**Command History**

+---------+--------------------+
| Release | Modification       |
+=========+====================+
| 13.0    | Command introduced |
+---------+--------------------+
