clear rsvp tunnels
------------------

**Minimum user role:** operator

To clear RSVP tunnels:

**Command syntax: clear rsvp tunnels** { soft \| optimize} {[type] \| [role] \| auto-mesh [template-name]} {destination-address [destination-address] \| name [name] \| state [state]  }

**Command mode:** operation

.. **Hierarchies**

**Note**

- Use destination-address, name or state to apply action to tunnels only matching the filter.


**Parameter table:**

+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| Parameter                 | Description                                                                                                                                                           | Range             |             |
|                           |                                                                                                                                                                       |                   | Default     |
+===========================+=======================================================================================================================================================================+===================+=============+
| no parameter              | Clear all RSVP tunnel sessions                                                                                                                                        | \-                | \-          |
+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| soft                      | Invokes make-before-break for head tunnels only. Other tunnel types won't reset.                                                                                      | \-                | \-          |
+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| optimize                  | Invoke optimization for all head tunnels. A tunnel optimized using the clear command is entered to the top of the optimization queue (first in line for optimization) | \-                | \-          |
+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| type                      | Clear specific tunnel types.                                                                                                                                          | primary           | \-          |
|                           | If the soft or optimize option is set, then setting the type will not affect transit or tail tunnels.                                                                 | bypass            |             |
|                           |                                                                                                                                                                       | auto-bypass       |             |
+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| role                      | Clear tunnels by role.                                                                                                                                                | head              | \-          |
|                           | Role cannot be used with soft or optimize options.                                                                                                                    | transit           |             |
|                           |                                                                                                                                                                       | tail              |             |
+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| destination-address       | Clear all RSVP tunnel sessions that match the specified destination-address                                                                                           | A.B.C.D           | \-          |
+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| name                      | Clear all RSVP tunnel sessions that match the specified tunnel name                                                                                                   | 1..255 characters | \-          |
+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| state                     | Clear all RSVP tunnel sessions that match the specified tunnel state                                                                                                  | up, down          | \-          |
|                           | Not valid for role transit or tail.                                                                                                                                   |                   |             |
+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+
| auto-mesh [template-name] | Clear auto-mesh tunnels by template name                                                                                                                              | \-                | \-          |
+---------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------+-------------------+-------------+

**Example**
::

	dnRouter# clear rsvp tunnels

	dnRouter# clear rsvp tunnels destination-address 3.3.3.3

	dnRouter# clear rsvp tunnels name TUNNEL_1

	dnRouter# clear rsvp tunnels state down

	dnRouter# clear rsvp tunnels soft

	dnRouter# clear rsvp tunnels optimize

	dnRouter# clear rsvp tunnels optimize auto-mesh PRIORITY_CORE

.. **Help line:**

**Command History**

+---------+---------------------------------------------------+
| Release | Modification                                      |
+=========+===================================================+
| 9.0     | Command introduced                                |
+---------+---------------------------------------------------+
| 10.0    | Added soft clear and clear by type                |
+---------+---------------------------------------------------+
| 11.0    | Added optimization and auto-mesh template options |
+---------+---------------------------------------------------+
| 11.2    | Added the ability to clear by tunnel role.        |
+---------+---------------------------------------------------+