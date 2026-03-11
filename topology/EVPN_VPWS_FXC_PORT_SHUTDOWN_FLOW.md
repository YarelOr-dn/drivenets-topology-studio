# EVPN-VPWS-FXC Service Down → Port Shutdown Flow

## Overview
When an EVPN-VPWS-FXC service goes down, multiple components work together to detect the failure and force port shutdown on PWHE interfaces (pwX.Y). This document traces the complete flow through all involved components.

---

## Components Involved

### 1. **Zebra (EVPN Service Layer)**
   - **Location**: `services/control/quagga/zebra/evpn/`
   - **Key Files**:
     - `EvpnServiceVpws.cpp` - VPWS service management
     - `EvpnAttachmentCircuit.cpp` - AC (Attachment Circuit) management
     - `EvpnServiceManager.cpp` - Service manager coordination
     - `EmMessagesManager.cpp` - Element Manager message handling

### 2. **Element Manager (EM) Communication Layer**
   - **Location**: `services/control/quagga/zebra/`
   - **Key Files**:
     - `EmMessagesManager.cpp` - Manages bulk port shutdown messages
     - `zebra_em_connection_init.c` - EM connection initialization

### 3. **CMC (Cluster Manager) - Port Shutdown Protocol**
   - **Location**: `src/cmc/interface_manager/protocols/port_shutdown/`
   - **Key Files**:
     - `port_shutdown_manager.c` - Port shutdown protocol manager
     - `port_shutdown_fsm.c` - Finite State Machine for port shutdown
     - `port_shutdown_types.h` - Type definitions

### 4. **Interface Manager (CMC)**
   - **Location**: `src/cmc/interface_manager/`
   - **Key Files**:
     - `protocol_logic.c` - Protocol state management
     - `interface_manager.c` - Interface state coordination

### 5. **FPM (Forwarding Plane Manager)**
   - **Location**: `src/libdatapath/fpm_communicator/`
   - **Key Files**:
     - `fpm_evpn_vpws_service_handler.cpp` - FPM service message handling

---

## Complete Flow: Service Down → Port Shutdown

### **Step 1: Service Down Detection**

**Component**: Zebra EVPN Service Layer  
**File**: `EvpnServiceVpws.cpp`, `EvpnAttachmentCircuit.cpp`

When the EVPN-VPWS-FXC service goes down (e.g., BGP route withdrawn, next-hop unreachable, FIB failure):

1. **Service Status Change Detection**:
   ```cpp
   // EvpnAttachmentCircuit.cpp:2047-2056
   void EvpnAttachmentCircuit::calcVpwsServiceStatusAndSysEvent()
   {
       if (isAnyVpwsAc())
       {
           bool isServiceUp = m_Parent->getEthTagServiceVpws().isVpwsServiceUp();
           // Service status calculated based on:
           // - BGP route availability
           // - Next-hop reachability
           // - FIB installation status
           setVpwsServiceStatusAndSysEvent(isServiceUp);
       }
   }
   ```

2. **Laser State Calculation**:
   ```cpp
   // EvpnAttachmentCircuit.cpp:1462-1472
   enum EvpnAcLaserRequestState EvpnAttachmentCircuit::calcNewAcLaserState() const
   {
       // Determines if laser should be OFF based on:
       // - Service status (up/down)
       // - Propagate failures configuration
       // - Link state
       // - Remote service availability
   }
   ```

---

### **Step 2: Laser State Update**

**Component**: Zebra EVPN Attachment Circuit  
**File**: `EvpnAttachmentCircuit.cpp`

When service goes down, the laser state is updated:

```cpp
// EvpnAttachmentCircuit.cpp:2146-2192
void EvpnAttachmentCircuit::updateLaserState(enum EvpnAcLaserRequestState a_LaserNewState)
{
    if (a_LaserNewState != m_EvpnAcStatus.getLaserState())
    {
        // Wait for BGP bestpath to complete
        if (!m_Parent->getEthTagServiceCommon().isBgpBpDone())
        {
            return; // Ignore until BGP BP is done
        }

        switch (a_LaserNewState)
        {
        case EvpnAcLaserRequestState::LASER_OFF:
            setAcLaserStateToOff();  // Sets laser state to OFF
            isLaserOff = true;
            break;
        // ... other states
        }

        // Update propagate failures action status
        bool isUpdated = m_OperDb.setPropagateFailuresActionStatus(isLaserOff);
        if (isUpdated)
        {
            isLaserOff ? sendLaserOffRequest() : sendLaserOnRequest();
        }
    }
}
```

---

### **Step 3: Port Shutdown Action Request**

**Component**: Zebra EVPN Attachment Circuit → EVPN Service Manager  
**Files**: `EvpnAttachmentCircuit.cpp`, `EvpnServiceManager.cpp`

The AC sends a port shutdown action request:

```cpp
// EvpnAttachmentCircuit.cpp:2434-2439
void EvpnAttachmentCircuit::sendLaserOffRequest()
{
    auto action = (m_Parent->getEthTagServiceCommon().isVpwsAnyService() 
                   ? PortAction::PORT_ACTION_DOWN_EVPN_VPWS 
                   : PortAction::PORT_ACTION_DOWN_MAC_MOBILITY);
    auto ifname = m_OperDb.getName().c_str();  // e.g., "pw1.1"
    m_Parent->getEthTagServiceCommon().getManager().setAcPortShutdownActionInBulk(ifname, action);
}
```

**Service Manager**:
```cpp
// EvpnServiceManager.cpp:1131-1133
void EvpnServiceManager::setAcPortShutdownActionInBulk(const std::string &a_InterfaceName, PortAction a_Action)
{
    m_EmMessagesManagerPtr->setAcPortShutdownActionInBulk(a_InterfaceName, a_Action);
}
```

---

### **Step 4: Bulk Message Collection**

**Component**: EmMessagesManager  
**File**: `EmMessagesManager.cpp`

Port shutdown actions are collected in bulk before sending:

```cpp
// EmMessagesManager.cpp:236-339
bool EmMessagesManager::sendPortShutdownMessages(bool filter_local2local, struct thread* thread)
{
    // Collects all port shutdown actions in m_AcPortShutdownActionBulkMap
    // Groups them into batches (max PORT_SHUTDOWN_BULK_MSG_MAX_AC_PER_MSG per batch)
    // Sends via EM wrapper to CMC
}
```

**Bulk Collection**:
- Actions are stored in `m_AcPortShutdownActionBulkMap`
- Timer-based batching (waits for BGP bestpath completion if needed)
- Sends in batches to avoid overwhelming CMC

---

### **Step 5: EM Communication to CMC**

**Component**: EmMessagesManager → EM Wrapper  
**Files**: `EmMessagesManager.cpp`, `EmWrapper` (C++)

Messages are sent via Element Manager protocol:

```cpp
// EmMessagesManager.cpp:264
if (m_EmWrapper->sendPortShutdownInterfacesAction(actionVec) < 0)
    return false;
```

**Message Format**:
- Protobuf message containing:
  - Interface name (e.g., "pw1.1")
  - Port action (`PORT_ACTION_DOWN_EVPN_VPWS`)
  - Action type (EVPN_VPWS)

---

### **Step 6: CMC Port Shutdown Handler**

**Component**: CMC Port Shutdown Handler  
**File**: `src/cmc/proto_handler/cmc_api/port_shutdown_handler/port_shutdown_handler.c`

CMC receives the port shutdown request:

1. **Message Reception**:
   - EM message received via protobuf
   - Parsed and validated
   - Interface name extracted (e.g., "pw1.1")

2. **Port Shutdown Request Processing**:
   - Validates interface exists
   - Checks if interface is PWHE type
   - Creates port shutdown request

---

### **Step 7: Port Shutdown Protocol**

**Component**: CMC Interface Manager - Port Shutdown Protocol  
**Files**: 
- `src/cmc/interface_manager/protocols/port_shutdown/port_shutdown_manager.c`
- `src/cmc/interface_manager/protocols/port_shutdown/port_shutdown_fsm.c`

The port shutdown protocol processes the request:

```c
// port_shutdown_manager.c
// Port shutdown protocol is registered as one of the interface protocols
// It maintains state for each port shutdown type:
// - PORT_SHUTDOWN_TYPE_MAC_MOBILITY
// - PORT_SHUTDOWN_TYPE_EVPN_VPWS  ← This one for EVPN-VPWS-FXC
// - PORT_SHUTDOWN_TYPE_LOCAL2LOCAL
```

**State Machine**:
- `PORT_SHUTDOWN_FSM_S_UP` → `PORT_SHUTDOWN_FSM_S_DOWN`
- State change triggers interface operational state update

---

### **Step 8: Interface State Update**

**Component**: CMC Interface Manager  
**File**: `src/cmc/interface_manager/protocol_logic.c`

The port shutdown protocol updates interface state:

```c
// protocol_logic.c:550-564
if (CMC_INTERFACE_TYPE_BUNDLE == if_data->if_data.type ||
    CMC_INTERFACE_TYPE_PHYSICAL == if_data->if_data.type)
{
    // For PWHE interfaces, the port shutdown protocol
    // forces the interface operational state to DOWN
    events_logger_log_iface_event(curr_state->interface_name,
                                  "Interface went down");
}
```

**Protocol State Aggregation**:
- Multiple protocols contribute to interface state
- Port shutdown protocol sets link state to DOWN
- Interface manager aggregates all protocol states
- Final operational state becomes DOWN

---

### **Step 9: Interface Operational State Propagation**

**Component**: CMC Interface Manager → FPM  
**Files**: 
- `src/cmc/interface_manager/interface_db_writer.c`
- `src/libdatapath/fpm_communicator/`

The interface operational state change is propagated:

1. **Operational DB Update**:
   - Interface operational state written to operational database
   - State change triggers notifications

2. **FPM Notification**:
   - FPM receives interface state change
   - Updates forwarding plane
   - Blocks traffic on the interface

---

### **Step 10: Physical Interface Shutdown**

**Component**: CMC → Hardware  
**File**: `src/cmc/interface_manager/`

The physical interface is shut down:

1. **Link State Change**:
   - Interface link state set to DOWN
   - Hardware notified (if applicable)
   - Laser/transceiver disabled (for optical interfaces)

2. **Traffic Blocking**:
   - All traffic on pwX.Y interface is blocked
   - No frames forwarded
   - Interface appears as "down" in operational state

---

## Port Shutdown Types

The system supports multiple port shutdown types:

1. **PORT_SHUTDOWN_TYPE_EVPN_VPWS**:
   - Used for EVPN-VPWS-FXC services
   - Triggered when service goes down
   - Action: `PORT_ACTION_DOWN_EVPN_VPWS`

2. **PORT_SHUTDOWN_TYPE_MAC_MOBILITY**:
   - Used for MAC mobility suppression
   - Different from VPWS shutdown

3. **PORT_SHUTDOWN_TYPE_LOCAL2LOCAL**:
   - Used for local-to-local scenarios

---

## Key Functions and Call Flow

```
Service Down Detection:
  EvpnServiceVpws::isVpwsServiceUp()
    ↓
  EvpnAttachmentCircuit::calcVpwsServiceStatusAndSysEvent()
    ↓
  EvpnAttachmentCircuit::calcNewAcLaserState()
    ↓
  EvpnAttachmentCircuit::updateLaserState(LASER_OFF)
    ↓
  EvpnAttachmentCircuit::sendLaserOffRequest()
    ↓
  EvpnServiceManager::setAcPortShutdownActionInBulk()
    ↓
  EmMessagesManager::setAcPortShutdownActionInBulk()
    ↓
  EmMessagesManager::sendPortShutdownMessages()
    ↓
  EmWrapper::sendPortShutdownInterfacesAction()
    ↓
  CMC Port Shutdown Handler (protobuf message)
    ↓
  port_shutdown_manager::process_port_shutdown_request()
    ↓
  port_shutdown_fsm::update_state(DOWN)
    ↓
  protocol_logic::interface_manager_get_interface_states_from_protocols()
    ↓
  interface_manager::update_interface_oper_state(DOWN)
    ↓
  FPM::notify_interface_state_change()
    ↓
  Hardware: Interface Shutdown
```

---

## Configuration Dependencies

1. **Propagate Failures**:
   - Must be enabled on the AC for port shutdown to work
   - Configuration: `propagate-failures action laser-off`

2. **BGP Bestpath**:
   - Port shutdown waits for BGP bestpath to complete
   - Ensures route convergence before shutdown

3. **Service Admin State**:
   - Service must be admin-enabled
   - Admin-disable also triggers shutdown

---

## Timing and Delays

1. **BGP Bestpath Wait**:
   - Port shutdown delayed until BGP bestpath completes
   - Prevents premature shutdown during route convergence

2. **Bulk Message Batching**:
   - Messages batched with timeout (CMC_MESSAGES_BULK_MSG_TIMEOUT)
   - During transactions: CMC_MESSAGES_BULK_MSG_DURING_TRANSACTION_TIMEOUT

3. **State Machine Transitions**:
   - Immediate state change in FSM
   - Interface state update follows protocol state

---

## Error Handling

1. **EM Connection Failure**:
   - Messages queued in `m_AcPortShutdownActionBulkMap`
   - Retried when EM connection restored

2. **Interface Not Found**:
   - Error logged
   - Request ignored

3. **BGP Bestpath Pending**:
   - Port shutdown delayed
   - Retried after bestpath completes

---

## Logging and Debugging

**Key Log Messages**:
- `"Port shutdown: AC %s laser state changed from %s to %s"`
- `"Port shutdown: sending bulk AC port shutdown action to CMC"`
- `"Port shutdown: BGP BP isn't done yet. Ignore AC %s laser state change"`

**Debug Commands**:
- `show evpn-vpws-fxc instance <name> detail` - Shows service status
- `show interfaces <pwX.Y> detail` - Shows interface operational state
- `show port-shutdown interface <pwX.Y>` - Shows port shutdown state

---

## Summary

When an EVPN-VPWS-FXC service goes down:

1. **Zebra** detects service failure and calculates laser state
2. **EmMessagesManager** collects port shutdown actions in bulk
3. **EM Protocol** sends messages to CMC
4. **CMC Port Shutdown Handler** receives and validates request
5. **Port Shutdown Protocol** updates FSM state to DOWN
6. **Interface Manager** aggregates protocol states and updates interface
7. **FPM** receives notification and updates forwarding plane
8. **Hardware** physically shuts down the interface (pwX.Y)

The entire flow ensures that when the service is down, the PWHE interface is immediately shut down to prevent traffic blackholing and ensure proper failover behavior.






