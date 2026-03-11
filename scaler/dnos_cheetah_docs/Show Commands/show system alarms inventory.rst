show system alarms inventory
----------------------------

**Minimum user role:** viewer

To display the system alarms inventory in the system:



**Command syntax: show system alarms inventory** module [module-name]

**Command mode:** operational

**Note:**

- The following command shows all supported DNOS Alarms in the system.

- Inventory alarms can be filtered and displayed per module.

- Inventory alarms can be filtered and displayes only clearable alarms.


**Parameter table**

The following information is displayed on each alarm:

+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Field             | Description                                                                                                                    | Range                    |
+===================+================================================================================================================================+==========================+
| Name              | The alarm name                                                                                                                 | \-                       |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Resource          | The resource the alarm is raised on                                                                                            | \-                       |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Alarm Description | The alarm description                                                                                                          | \-                       |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Admin State       | The administrative status of the alarm, indicates whether or not the alarm is currently enabled.                               | Enabled                  |
|                   |                                                                                                                                | Disabled                 |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Clearable         | True if the alarm is clearable otherwise False                                                                                 | \-                       |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+
| Module Name       | The name of the alarm module                                                                                                   | dnos-alarms              |
|                   |                                                                                                                                | communications-alarm     |
|                   |                                                                                                                                | quality-of-service-alarm |
|                   |                                                                                                                                | processing-error-alarm   |
|                   |                                                                                                                                | equipment-alarm          |
|                   |                                                                                                                                | environmental-alarm      |
|                   |                                                                                                                                | bfd                      |
|                   |                                                                                                                                | bgp                      |
|                   |                                                                                                                                | efm-oam                  |
|                   |                                                                                                                                | management               |
|                   |                                                                                                                                | isis                     |
|                   |                                                                                                                                | pcep                     |
|                   |                                                                                                                                | ldp                      |
|                   |                                                                                                                                | l2vpn                    |
|                   |                                                                                                                                | aaa                      |
|                   |                                                                                                                                | rib                      |
|                   |                                                                                                                                | rsvp                     |
|                   |                                                                                                                                | segment-routing          |
|                   |                                                                                                                                | static-route             |
|                   |                                                                                                                                | fib-manager              |
|                   |                                                                                                                                | interfaces               |
|                   |                                                                                                                                | lacp                     |
|                   |                                                                                                                                | system                   |
|                   |                                                                                                                                | diagnostics              |
|                   |                                                                                                                                | platform                 |
|                   |                                                                                                                                | transaction              |
+-------------------+--------------------------------------------------------------------------------------------------------------------------------+--------------------------+

**Example**
::

    dev-dnRouter# show system alarms inventory


    | Name                                        | Module Name | Severity | Clearable | Alarm Description                      | 
    +---------------------------------------------+-------------+----------+-----------+----------------------------------------+ 
    | RADIUS_SERVER_STATE_CHANGE_NOT_AVAILABLE    | aaa         | Warning  |   False   | DNOS failed to connect to the listed   |   
    |                                             |             |          |           | RADIUS server, the RADIUS server is    |   
    |                                             |             |          |           | not available.                         |   
    | BFD_MICRO_BFD_STATE_DOWN                    | bfd         | Major    |   False   | The Micro BFD session changed to a     |   
    |                                             |             |          |           | 'down' or 'Admin-down' state.          |   
    | BFD_STATE_DOWN                              | bfd         | Major    |   False   | The BFD session changed to a 'down' or |   
    |                                             |             |          |           | 'Admin-down' state.                    |   
    | IF_LINK_LOCAL_FAULT_DETECTED                | interfaces  | Major    |   False   | Local fault detected on the interface  |   
    |                                             |             |          |           | Reconciliation Sublayer. The interface |   
    |                                             |             |          |           | had stopped sending packets and Remote |   
    |                                             |             |          |           | Fault Indication sent to the peer      |   
    |                                             |             |          |           | router.                                |   
    | IF_LINK_REMOTE_FAULT_DETECTED               | interfaces  | Major    |   False   | Remote fault detected on the interface |   
    |                                             |             |          |           | Reconciliation Sublayer. The interface |   
    |                                             |             |          |           | had stopped sending packets and IDLE   |   
    |                                             |             |          |           | Symbol is being sent to the peer       |   
    |                                             |             |          |           | router.                                |   
    | IF_LINK_STATE_CHANGE_DOWN                   | interfaces  | Major    |   False   | The link state on the interface has    |   
    |                                             |             |          |           | moved to a 'down' state. The link      |   
    |                                             |             |          |           | state changed due to a link failure.   |   
    | IF_LINK_STATE_CHANGE_MIN_BANDWIDTH_REACHED  | interfaces  | Major    |   False   | The link state has moved to a 'down'   |   
    |                                             |             |          |           | state due to the configured            |   
    |                                             |             |          |           | min-bandwidth limit being reached.     |   
    | ISIS_MAXIMUM_ROUTES_LIMIT_REACHED           | isis        | Major    |   False   | The number of ISIS routes has reached  |   
    |                                             |             |          |           | the system limit.                      |   
    | ISIS_MAXIMUM_ROUTES_THRESHOLD_EXCEEDED      | isis        | Warning  |   False   | The number of ISIS routes has crossed  |   
    |                                             |             |          |           | the system threshold.                  |   
    | ISIS_NEIGHBOR_ADJACENCY_DOWN                | isis        | Warning  |   True    | ISIS neighbor adjacency moved from 'up'|   
    |                                             |             |          |           | state to a 'down' or 'init' state.     |   
    | PSEUDOWIRE_DOWN                             | l2vpn       | Minor    |   False   | The referenced Pseudowire connection   |   
    |                                             |             |          |           | changed to a 'down' state and cannot   |   
    |                                             |             |          |           | be used to forward traffic.            |   
    | LACP_INTERFACE_UP                           | lacp        | Major    |   False   | The LACP adjacency is 'up' on the      |   
    |                                             |             |          |           | indicated interface.                   |   
    | PLATFORM_NCC_CPU_LIMIT_REACHED              | platform    | Critical |   False   | The CPU of the node listed has reached |   
    |                                             |             |          |           | the maximum limit of 90.               |   
    | PLATFORM_NCC_CPU_THRESHOLD_EXCEEDED         | platform    | Warning  |   False   | The CPU of the node listed has crossed |   
    |                                             |             |          |           | the threshold.                         |   
    | PLATFORM_NCC_FAN_MAX_SPEED_REACHED          | platform    | Major    |   False   | The platform fans are at the maximum   |   
    |                                             |             |          |           | speed and crossed the temperature      |   
    |                                             |             |          |           | threshold.                             |   
    | PLATFORM_NCC_HD_LIMIT_REACHED               | platform    | Critical |   False   | The hard disk partition of the node    |   
    |                                             |             |          |           | listed reached the maximum limit of    |   
    |                                             |             |          |           | 100.                                   |   
    | PLATFORM_NCC_HD_THRESHOLD_EXCEEDED          | platform    | Critical |   False   | The hard disk partition of the node    |   
    |                                             |             |          |           | listed has crossed the threshold.      |   
    | PLATFORM_NCC_MEMORY_LIMIT_REACHED           | platform    | Critical |   False   | The memory in the node listed has      |   
    |                                             |             |          |           | reached the maximum limit of 100.      |   
    | PLATFORM_NCC_MEMORY_THRESHOLD_EXCEEDED      | platform    | Warning  |   False   | The memory in the node listed is above |   
    |                                             |             |          |           | the threshold.                         |   
    | PLATFORM_NCC_PSU_INPUT_VOLTAGE_HIGH         | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed NCC or NCF has an input voltage |   
    |                                             |             |          |           | that is too high.                      |   
    | PLATFORM_NCC_PSU_INPUT_VOLTAGE_LOW          | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed NCC or NCF has an input voltage |   
    |                                             |             |          |           | that is too low.                       |   
    | PLATFORM_NCC_PSU_OUTPUT_VOLTAGE_HIGH        | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed node has an output voltage that |   
    |                                             |             |          |           | is too high.                           |   
    | PLATFORM_NCC_PSU_OUTPUT_VOLTAGE_LOW         | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed node has an output voltage that |   
    |                                             |             |          |           | is too low.                            |   
    | PLATFORM_NCC_TEMP_SENSOR_HIGH               | platform    | Critical |   False   | The temperature sensor state changed.  |   
    | PLATFORM_NCC_TEMP_SENSOR_LOW                | platform    | Critical |   False   | The temperature sensor state changed.  |   
    | PLATFORM_NCF_CPU_LIMIT_REACHED              | platform    | Critical |   False   | The CPU of the node listed has reached |   
    |                                             |             |          |           | the maximum limit of 90.               |   
    | PLATFORM_NCF_CPU_THRESHOLD_EXCEEDED         | platform    | Warning  |   False   | The CPU of the node listed has crossed |   
    |                                             |             |          |           | the threshold.                         |   
    | PLATFORM_NCF_FAN_MAX_SPEED_REACHED          | platform    | Major    |   False   | The platform fans are at the maximum   |   
    |                                             |             |          |           | speed and crossed the temperature      |   
    |                                             |             |          |           | threshold.                             |   
    | PLATFORM_NCF_HD_LIMIT_REACHED               | platform    | Critical |   False   | The hard disk partition of the node    |   
    |                                             |             |          |           | listed reached the maximum limit of    |   
    |                                             |             |          |           | 100.                                   |   
    | PLATFORM_NCF_HD_THRESHOLD_EXCEEDED          | platform    | Critical |   False   | The hard disk partition of the node    |   
    |                                             |             |          |           | listed has crossed the threshold.      |   
    | PLATFORM_NCF_MEMORY_LIMIT_REACHED           | platform    | Critical |   False   | The memory in the node listed has      |   
    |                                             |             |          |           | reached the maximum limit of 100.      |   
    | PLATFORM_NCF_MEMORY_THRESHOLD_EXCEEDED      | platform    | Warning  |   False   | The memory in the node listed is above |   
    |                                             |             |          |           | the threshold.                         |   
    | PLATFORM_NCF_PSU_INPUT_VOLTAGE_HIGH         | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed NCF or NCF has an input voltage |   
    |                                             |             |          |           | that is too high.                      |   
    | PLATFORM_NCF_PSU_INPUT_VOLTAGE_LOW          | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed NCF or NCF has an input voltage |   
    |                                             |             |          |           | that is too low.                       |   
    | PLATFORM_NCF_PSU_OUTPUT_VOLTAGE_HIGH        | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed node has an output voltage that |   
    |                                             |             |          |           | is too high.                           |   
    | PLATFORM_NCF_PSU_OUTPUT_VOLTAGE_LOW         | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed node has an output voltage that |   
    |                                             |             |          |           | is too low.                            |   
    | PLATFORM_NCF_TEMP_SENSOR_HIGH               | platform    | Critical |   False   | The temperature sensor state changed.  |   
    | PLATFORM_NCF_TEMP_SENSOR_LOW                | platform    | Critical |   False   | The temperature sensor state changed.  |   
    | PLATFORM_NCM_CPU_LIMIT_REACHED              | platform    | Critical |   False   | The CPU of the node listed has reached |   
    |                                             |             |          |           | the maximum limit of 90.               |   
    | PLATFORM_NCM_CPU_THRESHOLD_EXCEEDED         | platform    | Warning  |   False   | The CPU of the node listed has crossed |   
    |                                             |             |          |           | the threshold.                         |   
    | PLATFORM_NCM_FAN_MAX_SPEED_REACHED          | platform    | Major    |   False   | The platform fans are at the maximum   |   
    |                                             |             |          |           | speed and crossed the temperature      |   
    |                                             |             |          |           | threshold.                             |   
    | PLATFORM_NCM_HD_LIMIT_REACHED               | platform    | Critical |   False   | The hard disk partition of the node    |   
    |                                             |             |          |           | listed reached the maximum limit of    |   
    |                                             |             |          |           | 100.                                   |   
    | PLATFORM_NCM_HD_THRESHOLD_EXCEEDED          | platform    | Critical |   False   | The hard disk partition of the node    |   
    |                                             |             |          |           | listed has crossed the threshold.      |   
    | PLATFORM_NCM_MEMORY_LIMIT_REACHED           | platform    | Critical |   False   | The memory in the node listed has      |   
    |                                             |             |          |           | reached the maximum limit of 100.      |   
    | PLATFORM_NCM_MEMORY_THRESHOLD_EXCEEDED      | platform    | Warning  |   False   | The memory in the node listed is above |   
    |                                             |             |          |           | the threshold.                         |   
    | PLATFORM_NCM_PSU_INPUT_VOLTAGE_HIGH         | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed NCM or NCF has an input voltage |   
    |                                             |             |          |           | that is too high.                      |   
    | PLATFORM_NCM_PSU_INPUT_VOLTAGE_LOW          | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed NCM or NCF has an input voltage |   
    |                                             |             |          |           | that is too low.                       |   
    | PLATFORM_NCM_PSU_OUTPUT_VOLTAGE_HIGH        | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed node has an output voltage that |   
    |                                             |             |          |           | is too high.                           |   
    | PLATFORM_NCM_PSU_OUTPUT_VOLTAGE_LOW         | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed node has an output voltage that |   
    |                                             |             |          |           | is too low.                            |   
    | PLATFORM_NCM_TEMP_SENSOR_HIGH               | platform    | Critical |   False   | The temperature sensor state changed.  |   
    | PLATFORM_NCM_TEMP_SENSOR_LOW                | platform    | Critical |   False   | The temperature sensor state changed.  |   
    | PLATFORM_NCP_CPU_LIMIT_REACHED              | platform    | Critical |   False   | The CPU of the node listed has reached |   
    |                                             |             |          |           | the maximum limit of 90.               |   
    | PLATFORM_NCP_CPU_THRESHOLD_EXCEEDED         | platform    | Warning  |   False   | The CPU of the node listed has crossed |   
    |                                             |             |          |           | the threshold.                         |   
    | PLATFORM_NCP_FAN_MAX_SPEED_REACHED          | platform    | Major    |   False   | The platform fans are at the maximum   |   
    |                                             |             |          |           | speed and crossed the temperature      |   
    |                                             |             |          |           | threshold.                             |   
    | PLATFORM_NCP_HD_LIMIT_REACHED               | platform    | Critical |   False   | The hard disk partition of the node    |   
    |                                             |             |          |           | listed reached the maximum limit of    |   
    |                                             |             |          |           | 100.                                   |   
    | PLATFORM_NCP_HD_THRESHOLD_EXCEEDED          | platform    | Critical |   False   | The hard disk partition of the node    |   
    |                                             |             |          |           | listed has crossed the threshold.      |   
    | PLATFORM_NCP_MEMORY_LIMIT_REACHED           | platform    | Critical |   False   | The memory in the node listed has      |   
    |                                             |             |          |           | reached the maximum limit of 100.      |   
    | PLATFORM_NCP_MEMORY_THRESHOLD_EXCEEDED      | platform    | Warning  |   False   | The memory in the node listed is above |   
    |                                             |             |          |           | the threshold.                         |   
    | PLATFORM_NCP_PSU_INPUT_VOLTAGE_HIGH         | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed NCP or NCF has an input voltage |   
    |                                             |             |          |           | that is too high.                      |   
    | PLATFORM_NCP_PSU_INPUT_VOLTAGE_LOW          | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed NCP or NCF has an input voltage |   
    |                                             |             |          |           | that is too low.                       |   
    | PLATFORM_NCP_PSU_OUTPUT_VOLTAGE_HIGH        | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed node has an output voltage that |   
    |                                             |             |          |           | is too high.                           |   
    | PLATFORM_NCP_PSU_OUTPUT_VOLTAGE_LOW         | platform    | Critical |   False   | The Power Supply Unit (PSU) of the     |   
    |                                             |             |          |           | listed node has an output voltage that |   
    |                                             |             |          |           | is too low.                            |   
    | PLATFORM_NCP_TEMP_SENSOR_HIGH               | platform    | Critical |   False   | The temperature sensor state changed.  |   
    | PLATFORM_NCP_TEMP_SENSOR_LOW                | platform    | Critical |   False   | The temperature sensor state changed.  |   
    | PLATFORM_TRANSCEIVER_RX_HIGH_ALARM          | platform    | Critical |   False   | The transceiver input power of the     |   
    |                                             |             |          |           | indicated interface is too high and at |   
    |                                             |             |          |           | alarm level.                           |   
    | PLATFORM_TRANSCEIVER_RX_HIGH_WARNING        | platform    | Warning  |   False   | The transceiver input power of the     |   
    |                                             |             |          |           | indicated interface is too high and at |   
    |                                             |             |          |           | a warning level.                       |   
    | PLATFORM_TRANSCEIVER_RX_LOW_ALARM           | platform    | Critical |   False   | The transceiver input of the indicated |   
    |                                             |             |          |           | interface is too low and at alarm      |   
    |                                             |             |          |           | level.                                 |   
    | PLATFORM_TRANSCEIVER_RX_LOW_WARNING         | platform    | Critical |   False   | The transceiver input of the indicated |   
    |                                             |             |          |           | interface is too low and at warning    |   
    |                                             |             |          |           | level.                                 |   
    | PLATFORM_TRANSCEIVER_TX_HIGH_ALARM          | platform    | Critical |   False   | The transceiver output power of the    |   
    |                                             |             |          |           | indicated interface is too high and at |   
    |                                             |             |          |           | alarm level.                           |   
    | PLATFORM_TRANSCEIVER_TX_HIGH_WARNING        | platform    | Warning  |   False   | The transceiver output power of the    |   
    |                                             |             |          |           | indicated interface is too high and at |   
    |                                             |             |          |           | a warning level.                       |   
    | PLATFORM_TRANSCEIVER_TX_LOW_ALARM           | platform    | Critical |   False   | The transceiver output of the          |   
    |                                             |             |          |           | indicated interface is too low and at  |   
    |                                             |             |          |           | alarm level.                           |   
    | PLATFORM_TRANSCEIVER_TX_LOW_WARNING         | platform    | Critical |   False   | The transceiver output of the          |   
    |                                             |             |          |           | indicated interface is too low and at  |   
    |                                             |             |          |           | warning level.                         |   
    | SR_POLICY_DOWN                              | segment-rou | Major    |   False   | The Segment-Routing policy moved to    |   
    |                                             | ting        |          |           | either 'down' or 'admin-down' state    |   
    |                                             |             |          |           | and cannot be used to forward traffic. |   
    | NCF_TO_NCP_CONNECTIVITY_STATE_DOWN          | system      | Critical |   False   | The NCF has no connectivity with the   |   
    |                                             |             |          |           | listed NCP neighbor.                   |   
    | NCP_TO_NCF_CONNECTIVITY_STATE_DOWN          | system      | Critical |   False   | The NCP has no connectivity with the   |   
    |                                             |             |          |           | listed NCF neighbor.                   |   
    | NCP_TO_NCP_REACHABILITY_STATE_DOWN          | system      | Critical |   False   | The NCP has no reachability with the   |   
    |                                             |             |          |           | listed NCP neighbor.                   |   

    dev-dnRouter# show system alarms inventory module aaa


    | Name                                        | Module Name | Severity | Clearable | Alarm Description                      |
    +---------------------------------------------+-------------+----------+-----------+----------------------------------------+
    | RADIUS_SERVER_STATE_CHANGE_NOT_AVAILABLE    | aaa         | Warning  |   False   | DNOS failed to connect to the listed   |
    |                                             |             |          |           | RADIUS server, the RADIUS server is    |
    |                                             |             |          |           | not available.                         |


    dev-dnRouter# show system alarms inventory clearable


    | Name                                        | Module Name | Severity | Clearable | Alarm Description                      |
    +---------------------------------------------+-------------+----------+-----------+----------------------------------------+
    | ISIS_NEIGHBOR_ADJACENCY_DOWN                | isis        | Warning  |   True    | ISIS neighbor adjacency moved from 'up'|   
    |                                             |             |          |           | state to a 'down' or 'init' state.     |   

.. **Help line:** show system alarms inventory.

**Command History**

+---------+--------------------------------------------------+
| Release | Modification                                     |
+=========+==================================================+
| 18.0    | Command introduced                               |
+---------+--------------------------------------------------+
