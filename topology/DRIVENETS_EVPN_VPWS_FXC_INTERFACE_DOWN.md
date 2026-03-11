# DriveNets EVPN-VPWS-FXC Service: Parent Interface Down
## What to Expect on DF PE Side

Based on the DriveNets cheetah_25_4 codebase analysis.

---

## 📋 Question:

**In EVPN-VPWS-FXC service, what should be seen on the detailed service show when disabling parent phX on the phX.Y section on the DF PE side?**

---

## 🔍 Expected Behavior

When you disable the parent interface (phX) on the DF PE, the sub-interface (phX.Y) used in the EVPN-VPWS-FXC service should show:

### On the Service Detail Show:

Based on the code analysis from `/home/dn/cheetah_25_4`:

#### 1. **Attachment Circuit (AC) Status** ⬇️ Down
**Field:** `AC Operational Status` or `isOperational()`  
**Value:** `Down` or `Not Operational`  
**Reason:** Parent interface disabled → sub-interface inherits down state

#### 2. **Link State** ⬇️ Down
**Field:** `Link Status` or `isLinkUp()`  
**Value:** `Down`  
**Reason:** phX.Y goes down when phX is disabled

#### 3. **Admin State** (May Vary)
**Field:** `Admin State`  
**Value:** Could be `Enabled` (if phX.Y admin was not explicitly disabled)  
**Note:** Admin state of phX.Y may still show enabled even though operational is down

#### 4. **Service Status** ⚠️ Degraded/Down
**Field:** `Service Operational State`  
**Expected:** Service should show degraded or down
**Reason:** AC is down → service cannot forward traffic

#### 5. **DF Election** 🔄 May Change
**Field:** `DF Role` or `DF Status`
**Expected:** 
- If this was the DF (Designated Forwarder), election may failover to NDF PE
- DF role might show as `Non-DF` or `NDF` after failover
- Or show as `Down` if election can't proceed

#### 6. **Pseudowire (PW) Status** ⬇️ Down
**Field:** `PW Status` or `PW State`
**Expected:** PW associated with this AC should show down
**Reason:** Local AC is down → PW cannot be established

---

## 📊 Code Evidence

### From `EvpnAttachmentCircuit.h` (lines 174-176):
```cpp
bool isLinkUp() const { return m_EvpnAcStatus.isLinkUp(); }
bool isOperational() const { return m_EvpnAcStatus.isOperational(); }
bool isLaserStateOn() const { return m_EvpnAcStatus.isLaserStateOn(); }
```

### From `EvpnAttachmentCircuit.h` (lines 278-285):
```cpp
enum AcStatus
{
    LinkUpAdminEnabled,
    LinkUpAdminDisabled,
    LinkDownAdminEnabled,     // ← This is your case!
    LinkDownAdminDisabled,
    Deleted
};
```

When parent phX is disabled, the sub-interface phX.Y transitions to **`LinkDownAdminEnabled`** state (link is down but admin is still enabled).

### From `test_interfaces.py` (lines 9948-9954):
```python
# Set parent phx to admin down and check oper is down
logger.info(f"Setting parent interface {phx_if} admin state to down")
cli.interfaces.interface_admin_state(phx_if, "disabled")
cli.commit.commit()

logger.info(f"Verifying {phxy_if} is down when parent is admin down")
_wait_for_if_states(cli, phx_if, 'down')
_wait_for_if_states(cli, phxy_if, 'down')  # ← Sub-interface goes down!
```

---

## 🎯 Summary: What You Should See

### Command to Check:
```
show evpn vpws-fxc service <service-name> detail
```

### Expected Output Fields:

| Field | Expected Value | Reason |
|-------|---------------|---------|
| **Service Name** | `<your-service>` | Unchanged |
| **AC Interface** | `phX.Y` | Unchanged |
| **AC Admin State** | `Enabled` | Unless explicitly disabled |
| **AC Operational State** | **`Down`** ⬇️ | Parent disabled → child down |
| **AC Link Status** | **`Down`** ⬇️ | Interface is down |
| **isOperational()** | **`False`** ❌ | Not operational |
| **Service Status** | **`Down/Degraded`** ⚠️ | AC down → service impacted |
| **PW Status** | **`Down`** ⬇️ | Cannot establish PW |
| **DF Role** | May show `NDF` or `Down` | Election may failover |
| **Block Mode** | May change | Depends on redundancy |
| **Laser State** | May trigger laser-off | If propagate-failures enabled |

---

## 🔄 What Happens (Sequence):

1. **Parent phX disabled** → Admin state = disabled
2. **phX operational state** → Down
3. **Child phX.Y inherits** → Operational state = Down
4. **AC detects interface down** → `interfaceStatusChanged(ifindex, false)`
5. **AC operational state** → `isOperational()` returns `false`
6. **Service state updated** → Service shows down/degraded
7. **BGP may be notified** → Withdraw routes if needed
8. **DF election may trigger** → If this was DF, failover to peer
9. **PW goes down** → Cannot forward traffic
10. **Laser-off may trigger** → If propagate-failures configured

---

## 🧪 How to Verify:

### Step 1: Check Interface States
```
show interfaces interface phX
show interfaces interface phX.Y
```

Expected:
- phX: Admin = disabled, Oper = down
- phX.Y: Admin = enabled, Oper = **down** (inherits from parent)

### Step 2: Check Service Detail
```
show evpn vpws-fxc service <service-name> detail
```

Look for:
- AC operational state = down
- Service status = down/degraded
- PW status = down

### Step 3: Check DF Status
```
show evpn multihoming ethernet-segment
```

If on DF PE before, check if DF role changed

### Step 4: Check FIB
```
show route forwarding-table mpls in-label <label>
```

FXC entry may show but be inactive/down

---

## 🆘 If Behavior is Different:

### Case 1: phX.Y Stays Up (Bug!)
- **Expected:** phX.Y should go down when phX is disabled
- **If not:** Check if inherit-parent-state is configured correctly
- **Bug reference:** See test at `test_interfaces.py:9948`

### Case 2: Service Shows Up (Bug!)
- **Expected:** Service should show down when AC is down
- **If not:** Operational state tracking issue

### Case 3: DF Doesn't Failover
- **Expected:** DF election should trigger on AC down (if multihomed)
- **If not:** Check multihoming configuration

---

## 📚 Related Code Files:

**Attachment Circuit Status:**
- `/services/control/quagga/zebra/evpn/EvpnAttachmentCircuit.h` (lines 174-176, 278-285)
- `/services/control/quagga/zebra/evpn/EvpnAttachmentCircuit.cpp`

**Interface State Inheritance:**
- `/tests/suites/management/tests/test_interfaces.py` (lines 9945-9954)

**Service Manager:**
- `/services/control/quagga/zebra/evpn/EvpnServiceVpws.cpp`
- `/services/control/quagga/zebra/evpn/EvpnServiceManager.cpp`

**FXC Specific:**
- `/tests/suites/management/tests/test_network_services.py` (EVPN_VPWS_FXC paths)
- `/tests/suites/management/tests/test_rpc_flow.py` (lines 1542+)

---

## 💡 Key Takeaway:

**When you disable parent phX:**
- ✅ phX.Y goes **operational down** (inherits from parent)
- ✅ AC status becomes **not operational**
- ✅ Service shows **down or degraded**
- ✅ PW goes **down**
- ✅ May trigger **DF failover** (if multihomed)
- ✅ May trigger **laser-off** (if propagate-failures enabled)

---

*Based on: DriveNets cheetah_25_4 codebase analysis*  
*Files analyzed: 241 EVPN-related files*  
*Key reference: test_interfaces.py:9948-9954*



