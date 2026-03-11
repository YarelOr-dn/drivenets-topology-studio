# EVPN-VPWS-FXC Port Shutdown: True Flow Analysis

## Overview
This document describes the **actual implementation flow** for port shutdown in EVPN-VPWS-FXC services based on the `routing_fxc_pwhe_port_shutdown` feature branch (PR #84448). This flow is specific to FXC (Flexible Cross-Connect) services and PWHE (Pseudo-Wire Head-End) interfaces.

---

## Key Components and Flow

### 1. **Service State Detection (Zebra EVPN Layer)**

#### Location: `services/control/quagga/zebra/evpn/EvpnAttachmentCircuit.cpp`

**Trigger Point**: When EVPN-VPWS-FXC service state changes (remote service goes down, block mode changes, etc.)

**Key Functions**:

1. **`shouldLaserOff()`** (Line 1439)
   ```cpp
   bool EvpnAttachmentCircuit::shouldLaserOff() const
   ```
   - **For FXC Services**: Laser should be OFF when:
     - Remote service is DOWN (`!isVpwsRemoteServiceUp()`)
     - OR Block mode is NOT `BLOCK_NONE`
   - **For Non-FXC VPWS**: Laser should be OFF when remote service is DOWN
   - **For EVPN Services**: Returns `false` (not applicable)

2. **`calcNewAcLaserState()`** (Line 1462)
   ```cpp
   enum EvpnAcLaserRequestState EvpnAttachmentCircuit::calcNewAcLaserState() const
   ```
   - Calculates new laser state based on:
     - `isLaserOffCandidate()`: Whether AC is a candidate for laser off
     - `shouldLaserOff()`: Whether laser should be off based on service state
   - Returns: `LASER_OFF`, `LASER_ON`, or `LASER_ON_PENDING_UP`

3. **`calcNewAcLaserStateAndUpdate()`** (Line 1478)
   ```cpp
   void EvpnAttachmentCircuit::calcNewAcLaserStateAndUpdate()
   ```
   - Recalculates laser state and triggers update if state changed
   - Calls `interfaceLaserStatusUpdated()` when state changes

4. **`interfaceLaserStatusUpdated()`** (Line 962)
   ```cpp
   void EvpnAttachmentCircuit::interfaceLaserStatusUpdated(enum EvpnAcLaserRequestState a_LaserNewState)
   ```
   - Called when laser state changes
   - Updates internal state and triggers port shutdown action

---

### 2. **Port Shutdown Action Selection**

#### Location: `services/control/quagga/zebra/evpn/EvpnAttachmentCircuit.cpp`

**Key Functions**:

1. **`sendLaserOffRequest()`** (Line 2434)
   ```cpp
   void EvpnAttachmentCircuit::sendLaserOffRequest()
   ```
   - Determines port action based on service type:
     - **FXC Services**: Uses `getPortShutdownAction()` to get FXC-specific action
     - **VPWS Basic**: Uses `PORT_ACTION_DOWN_EVPN_VPWS`
     - **EVPN**: Uses `PORT_ACTION_DOWN_MAC_MOBILITY`
   - Calls `setAcPortShutdownActionInBulk()` with the determined action

2. **`sendLaserOnRequest()`** (Line 2441)
   ```cpp
   void EvpnAttachmentCircuit::sendLaserOnRequest()
   ```
   - Similar to `sendLaserOffRequest()` but for laser ON
   - Uses corresponding UP actions

3. **`getPortShutdownAction()`** (From PR diff - FXC-specific)
   ```cpp
   PortAction getPortShutdownAction(bool isLaserOff) const
   ```
   - **For FXC Services** (`isVpwsFxcVsService()`):
     - Returns `PORT_ACTION_DOWN_EVPN_VPWS_FXC` when `isLaserOff == true`
     - Returns `PORT_ACTION_UP_EVPN_VPWS_FXC` when `isLaserOff == false`
   - **For VPWS Basic**:
     - Returns `PORT_ACTION_DOWN_EVPN_VPWS` or `PORT_ACTION_UP_EVPN_VPWS`
   - **For EVPN**:
     - Returns `PORT_ACTION_DOWN_MAC_MOBILITY` or `PORT_ACTION_UP_MAC_MOBILITY`

---

### 3. **Bulk Port Shutdown Action Management**

#### Location: `services/control/quagga/zebra/EmMessagesManager.cpp`

**Key Functions**:

1. **`setAcPortShutdownActionInBulk()`** (Line 471)
   ```cpp
   void EmMessagesManager::setAcPortShutdownActionInBulk(
       const std::string &a_InterfaceName, 
       PortAction a_Action, 
       EvpnPortActionType a_Type = EvpnPortActionType::MOBILITY)
   ```
   - **Purpose**: Collects port shutdown actions in bulk before sending
   - **Parameters**:
     - `a_InterfaceName`: Interface name (e.g., `pw1.1`, `ph1.1`)
     - `a_Action`: Port action (UP/DOWN with service type)
     - `a_Type`: Action type (MOBILITY or VPWS)
   - **Behavior**:
     - Stores actions in `m_AcPortShutdownActionBulkMap`
     - Supports multiple action types per interface (MOBILITY and VPWS)
     - Starts timer to batch send messages
   - **Action Types**:
     - `EvpnPortActionType::MOBILITY`: For MAC mobility suppression
     - `EvpnPortActionType::VPWS`: For VPWS service state changes

2. **`startCmcMessagesTimer()`** (Called from `setAcPortShutdownActionInBulk`)
   - Starts a timer to batch send messages to CMC
   - Prevents sending individual messages for each interface

3. **`sendPortShutdownMessages()`** (Line 236)
   ```cpp
   bool EmMessagesManager::sendPortShutdownMessages(bool filter_local2local, struct thread* thread)
   ```
   - **Purpose**: Sends batched port shutdown messages to Element Manager (EM)
   - **Process**:
     1. Iterates through `m_AcPortShutdownActionBulkMap`
     2. Determines final action for each interface (prioritizes VPWS over MOBILITY)
     3. Filters out local-to-local actions if `filter_local2local == true`
     4. Sends messages in bulk (up to `BULK_MESSAGE_LIMIT` per batch)
     5. Uses `EmWrapper` to send protobuf messages to EM

---

### 4. **Element Manager (EM) Communication**

#### Location: `services/control/quagga/zebra/EmMessagesManager.cpp`

**Message Format**: Protobuf (`cmc_api/port_shutdown.pb.h`)

**Port Action Enum** (From PR diff):
```cpp
enum PortAction {
    PORT_ACTION_UP_EVPN_VPWS = 0;
    PORT_ACTION_UP_MAC_MOBILITY = 1;
    PORT_ACTION_UP_LOCAL_TO_LOCAL = 2;
    PORT_ACTION_DOWN_EVPN_VPWS = 3;
    PORT_ACTION_DOWN_MAC_MOBILITY = 4;
    PORT_ACTION_DOWN_LOCAL_TO_LOCAL = 5;
    PORT_ACTION_UP_EVPN_VPWS_FXC = 6;      // NEW for FXC
    PORT_ACTION_DOWN_EVPN_VPWS_FXC = 7;    // NEW for FXC
}
```

**Communication Path**:
```
Zebra (EmMessagesManager) 
  → EmWrapper 
    → EM Channel (em_channel)
      → Element Manager (EM)
        → CMC Port Shutdown Handler
```

---

### 5. **CMC Port Shutdown Handler**

#### Location: `src/cmc/proto_handler/cmc_api/port_shutdown_handler/`

**Responsibilities**:
1. Receives port shutdown messages from EM
2. Validates requests
3. Forwards to `port_shutdown_manager`

---

### 6. **Port Shutdown Manager (CMC)**

#### Location: `src/cmc/interface_manager/protocols/port_shutdown/port_shutdown_manager.c`

**Key Functions**:

1. **Port Action Processing**:
   - Receives port shutdown actions from Zebra via EM
   - Maintains port shutdown state per interface
   - Applies port shutdown to kernel/hardware

2. **Interface State Management**:
   - Tracks which interfaces are shut down by which service type
   - Handles multiple port shutdown reasons (EVPN-VPWS, MAC Mobility, Local-to-Local, FXC)
   - Applies port shutdown only when all reasons are cleared

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. EVPN-VPWS-FXC Service State Change                          │
│    - Remote service goes down                                   │
│    - Block mode changes                                         │
│    - Service becomes non-operational                            │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. EvpnAttachmentCircuit::calcNewAcLaserStateAndUpdate()       │
│    - Calls shouldLaserOff()                                     │
│      • For FXC: remote down OR block mode != NONE               │
│    - Calculates new laser state                                │
│    - Triggers interfaceLaserStatusUpdated() if changed          │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. EvpnAttachmentCircuit::interfaceLaserStatusUpdated()        │
│    - Updates internal laser state                              │
│    - Calls sendLaserOffRequest() or sendLaserOnRequest()       │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. EvpnAttachmentCircuit::sendLaserOffRequest()                │
│    - Determines port action via getPortShutdownAction()        │
│      • FXC: PORT_ACTION_DOWN_EVPN_VPWS_FXC                     │
│      • VPWS Basic: PORT_ACTION_DOWN_EVPN_VPWS                  │
│    - Calls setAcPortShutdownActionInBulk()                     │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. EmMessagesManager::setAcPortShutdownActionInBulk()          │
│    - Stores action in m_AcPortShutdownActionBulkMap            │
│    - Supports multiple action types (MOBILITY, VPWS)           │
│    - Starts batching timer                                      │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼ (Timer expires)
┌─────────────────────────────────────────────────────────────────┐
│ 6. EmMessagesManager::sendPortShutdownMessages()               │
│    - Processes batched actions                                 │
│    - Determines final action per interface                     │
│    - Filters local-to-local if needed                          │
│    - Sends protobuf messages via EmWrapper                     │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Element Manager (EM)                                         │
│    - Receives protobuf messages                                │
│    - Forwards to CMC Port Shutdown Handler                     │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. CMC Port Shutdown Handler                                    │
│    - Validates requests                                         │
│    - Forwards to port_shutdown_manager                         │
└────────────────────────┬──────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. Port Shutdown Manager (CMC)                                 │
│    - Updates port shutdown state                               │
│    - Applies shutdown to kernel/hardware                       │
│    - pwX.Y interface is administratively shut down             │
└─────────────────────────────────────────────────────────────────┘
```

---

## FXC-Specific Features

### 1. **Automatic Propagate Failures for PWHE Interfaces**

**Location**: `EvpnAttachmentCircuit::determineInitialPropagateFailures()` (From PR diff)

- **For FXC Services**: Automatically enables propagate failures for PWHE interfaces (interfaces starting with `ph`)
- **Purpose**: Ensures port shutdown works for FXC services without explicit configuration

### 2. **FXC-Specific Port Actions**

- **`PORT_ACTION_UP_EVPN_VPWS_FXC`**: Port up action for FXC services
- **`PORT_ACTION_DOWN_EVPN_VPWS_FXC`**: Port down action for FXC services
- **Purpose**: Allows CMC to distinguish FXC port shutdown from other VPWS types

### 3. **Service Type Detection**

**Key Functions**:
- `isVpwsFxcVsService()`: Checks if service is FXC
- `isVpwsAnyService()`: Checks if service is any VPWS type
- `getServiceType()`: Returns service type (EVPN_VPWS_FXC_VS, EVPN_VPWS_BASIC, etc.)

### 4. **Remote Service State Detection**

**Location**: `EvpnEthTagServiceVpws::isVpwsRemoteServiceUp()` (Line 486)

- **For FXC Services**: Checks if remote has valid neighbor in `m_VpwsActiveEsi->getCommonEviEsiEcmp()`
- **For VPLS**: Uses `EvpnSeamlessIntegrationVpws::isRemoteServiceUp()`
- **Returns**: `true` if remote service is up, `false` otherwise

---

## Key Differences from Previous Implementation

1. **FXC-Specific Port Actions**: New port action types for FXC services
2. **Service Type Awareness**: Port shutdown logic is aware of service type (FXC vs Basic VPWS)
3. **Automatic Propagate Failures**: FXC services automatically enable propagate failures for PWHE interfaces
4. **Bulk Message Handling**: Actions are batched before sending to reduce message overhead
5. **Multiple Action Types**: Supports both MOBILITY and VPWS action types per interface

---

## Debugging and Verification

### Key Debug Messages

1. **Laser State Calculation**:
   ```
   "Port shutdown: AC %s calc laser state. old %s new %s (isCandidate %d isLaserShouldBeOff %d)"
   ```

2. **Laser State Change**:
   ```
   "Port shutdown: AC %s laser state changed from %s to %s"
   ```

3. **Port Shutdown Action**:
   ```
   "Port shutdown: port shutdown action in bulk for interface %s set to %s"
   ```

4. **Remote Service State**:
   ```
   "Port shutdown: AC %s laser state should be on due to remote service up"
   "Port shutdown: AC %s laser state should be off"
   ```

### Verification Commands

1. **Check Service State**:
   ```
   show evpn-vpws-fxc instance <name> detail
   ```

2. **Check Interface State**:
   ```
   show interface pwX.Y
   ```

3. **Check Port Shutdown State** (if available):
   ```
   show port-shutdown
   ```

---

## Code References

### Primary Files

1. **`services/control/quagga/zebra/evpn/EvpnAttachmentCircuit.cpp`**
   - Laser state calculation and port shutdown triggering

2. **`services/control/quagga/zebra/EmMessagesManager.cpp`**
   - Bulk message collection and sending

3. **`services/control/quagga/zebra/evpn/EvpnEthTagServiceVpws.cpp`**
   - Remote service state detection

4. **`src/cmc/interface_manager/protocols/port_shutdown/port_shutdown_manager.c`**
   - CMC port shutdown handling

### Key Functions

- `EvpnAttachmentCircuit::shouldLaserOff()` - Line 1439
- `EvpnAttachmentCircuit::calcNewAcLaserState()` - Line 1462
- `EvpnAttachmentCircuit::sendLaserOffRequest()` - Line 2434
- `EmMessagesManager::setAcPortShutdownActionInBulk()` - Line 471
- `EmMessagesManager::sendPortShutdownMessages()` - Line 236
- `EvpnEthTagServiceVpws::isVpwsRemoteServiceUp()` - Line 486

---

## Summary

The FXC port shutdown flow is a multi-stage process that:

1. **Detects** service state changes in the EVPN service layer
2. **Calculates** laser state based on remote service state and block mode (for FXC)
3. **Triggers** port shutdown actions when laser state changes
4. **Batches** actions to reduce message overhead
5. **Sends** protobuf messages to EM
6. **Applies** port shutdown at the CMC level to kernel/hardware

The implementation is **service-type aware**, with specific handling for FXC services including automatic propagate failures for PWHE interfaces and FXC-specific port action types.






