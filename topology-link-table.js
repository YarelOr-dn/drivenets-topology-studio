/**
 * topology-link-table.js - Link Table Module
 * 
 * Extracted from topology.js for modular architecture.
 * Contains all Link Table population, validation, and field management functions.
 * 
 * @version 1.0.0
 * @date 2026-02-04
 */

'use strict';

window.LinkTableManager = {
    
    /**
     * Set up ResizeObserver to show/hide extra columns based on modal width
     */
    setupResponsiveColumns(editor, modalContent) {
        if (modalContent._responsiveColumnsSetup) return;
        modalContent._responsiveColumnsSetup = true;
        
        const WIDE_THRESHOLD = 750;
        
        const updateWidthMode = () => {
            const width = modalContent.offsetWidth;
            const mode = width > WIDE_THRESHOLD ? 'wide' : 'narrow';
            modalContent.dataset.width = mode;
        };
        
        updateWidthMode();
        
        if (window.ResizeObserver) {
            const resizeObserver = new ResizeObserver(() => updateWidthMode());
            resizeObserver.observe(modalContent);
            modalContent._resizeObserver = resizeObserver;
        } else {
            window.addEventListener('resize', updateWidthMode);
        }
    },

    /**
     * Populate Link Table fields from link data
     */
    populateFields(editor, link, device1InterfaceName, device2InterfaceName) {
        console.log('[LinkTableManager] Populating fields for link:', link.id);
        
        // MODEL FIRST approach - detect Model, then derive Category
        let platformModelA = link.device1Platform || '';
        let platformModelB = link.device2Platform || '';
        
        if (link.linkDetails) {
            if (link.linkDetails.platformModelA) platformModelA = link.linkDetails.platformModelA;
            if (link.linkDetails.platformModelB) platformModelB = link.linkDetails.platformModelB;
            
            if (!platformModelA && link.linkDetails.description) {
                const devName = link.linkDetails.description.split(' ↔ ')[0] || '';
                platformModelA = editor.detectModelFromDeviceName(devName);
            }
            if (!platformModelB && link.linkDetails.description) {
                const descParts = link.linkDetails.description.split(' ↔ ');
                const devName = (descParts[1] || '').split(' (')[0];
                platformModelB = editor.detectModelFromDeviceName(devName);
            }
        }
        
        const platformCatA = editor.deriveCategoryFromModel(platformModelA) || link.device1PlatformCategory || '';
        const platformCatB = editor.deriveCategoryFromModel(platformModelB) || link.device2PlatformCategory || '';
        
        this.setFieldValue(editor, 'lt-platform-cat-a', platformCatA);
        this.setFieldValue(editor, 'lt-platform-cat-b', platformCatB);
        
        if (platformCatA) editor.populateModelsForCategory('lt-platform-model-a', platformCatA);
        if (platformCatB) editor.populateModelsForCategory('lt-platform-model-b', platformCatB);
        
        this.setFieldValue(editor, 'lt-platform-model-a', platformModelA);
        this.setFieldValue(editor, 'lt-platform-model-b', platformModelB);
        
        // Interface
        let interfaceA = link.device1Interface || device1InterfaceName;
        let interfaceB = link.device2Interface || device2InterfaceName;
        
        if (link.linkDetails) {
            if (link.linkDetails.interfaceA) interfaceA = link.linkDetails.interfaceA;
            if (link.linkDetails.interfaceB) interfaceB = link.linkDetails.interfaceB;
        }
        
        this.setFieldValue(editor, 'lt-interface-a', interfaceA);
        this.setFieldValue(editor, 'lt-interface-b', interfaceB);
        
        // Transceiver
        let transceiverA = link.device1Transceiver;
        let transceiverB = link.device2Transceiver;
        if (link.linkDetails) {
            if (link.linkDetails.transceiverA) transceiverA = link.linkDetails.transceiverA;
            if (link.linkDetails.transceiverB) transceiverB = link.linkDetails.transceiverB;
            if (!transceiverA && interfaceA) {
                if (interfaceA.startsWith('ge100')) transceiverA = '100G QSFP28';
                else if (interfaceA.startsWith('ge400')) transceiverA = '400G QSFP-DD';
            }
            if (!transceiverB && interfaceB) {
                if (interfaceB.startsWith('ge100')) transceiverB = '100G QSFP28';
                else if (interfaceB.startsWith('ge400')) transceiverB = '400G QSFP-DD';
            }
        }
        this.setFieldValue(editor, 'lt-transceiver-a', transceiverA);
        this.setFieldValue(editor, 'lt-transceiver-b', transceiverB);
        
        // Auto-fill from DNAAS discovery
        this.autoFillFromDnaasDiscovery(editor, link, device1InterfaceName, device2InterfaceName);
        
        // Sub-Interface and Bundle
        if (link.linkDetails) {
            this.setFieldValue(editor, 'lt-subinterface-a', link.linkDetails.subInterfaceA);
            this.setFieldValue(editor, 'lt-subinterface-b', link.linkDetails.subInterfaceB);
            
            const bundleA = link.linkDetails.bundleA || 
                           (link.linkDetails.interfaceA && link.linkDetails.interfaceA.toLowerCase().includes('bundle') 
                            ? link.linkDetails.interfaceA.split('.')[0] : '');
            const bundleB = link.linkDetails.bundleB || 
                           (link.linkDetails.interfaceB && link.linkDetails.interfaceB.toLowerCase().includes('bundle') 
                            ? link.linkDetails.interfaceB.split('.')[0] : '');
            this.setFieldValue(editor, 'lt-bundle-a', bundleA);
            this.setFieldValue(editor, 'lt-bundle-b', bundleB);
            
            if (link.linkDetails.physicalInterfaceA) {
                this.setFieldValue(editor, 'lt-interface-a', link.linkDetails.physicalInterfaceA);
            }
            if (link.linkDetails.physicalInterfaceB) {
                this.setFieldValue(editor, 'lt-interface-b', link.linkDetails.physicalInterfaceB);
            }
            
            // Encapsulation
            if (link.linkDetails.encapsulationA) {
                const outerMatch = link.linkDetails.encapsulationA.match(/dot1q\s+(\d+)/);
                if (outerMatch) this.setFieldValue(editor, 'lt-outer-tag-a', outerMatch[1]);
            }
            if (link.linkDetails.encapsulationB) {
                const outerMatch = link.linkDetails.encapsulationB.match(/dot1q\s+(\d+)/);
                if (outerMatch) this.setFieldValue(editor, 'lt-outer-tag-b', outerMatch[1]);
            }
            
            let dnaasAutoFilled = false;
            
            if (link.linkDetails.vlanIdA && !link.device1VlanId) {
                this.setFieldValue(editor, 'lt-vlan-id-a', link.linkDetails.vlanIdA);
                dnaasAutoFilled = true;
            }
            if (link.linkDetails.vlanIdB && !link.device2VlanId) {
                this.setFieldValue(editor, 'lt-vlan-id-b', link.linkDetails.vlanIdB);
                dnaasAutoFilled = true;
            }
            
            if (link.linkDetails.innerVlanA) this.setFieldValue(editor, 'lt-inner-tag-a', link.linkDetails.innerVlanA);
            if (link.linkDetails.innerVlanB) this.setFieldValue(editor, 'lt-inner-tag-b', link.linkDetails.innerVlanB);
            
            if (link.linkDetails.rewriteIngressA) {
                const rewriteA = link.linkDetails.rewriteIngressA;
                if (rewriteA.includes('push')) this.setFieldValue(editor, 'lt-ingress-a', 'push');
                else if (rewriteA.includes('pop')) this.setFieldValue(editor, 'lt-ingress-a', 'pop');
                else if (rewriteA.includes('translate')) this.setFieldValue(editor, 'lt-ingress-a', 'swap');
            }
            if (link.linkDetails.rewriteIngressB) {
                const rewriteB = link.linkDetails.rewriteIngressB;
                if (rewriteB.includes('push')) this.setFieldValue(editor, 'lt-ingress-b', 'push');
                else if (rewriteB.includes('pop')) this.setFieldValue(editor, 'lt-ingress-b', 'pop');
                else if (rewriteB.includes('translate')) this.setFieldValue(editor, 'lt-ingress-b', 'swap');
            }
            
            if (link.linkDetails.l2ServiceA && !link.device1IpType) {
                this.setFieldValue(editor, 'lt-ip-type-a', 'L2 Service');
            }
            if (link.linkDetails.l2ServiceB && !link.device2IpType) {
                this.setFieldValue(editor, 'lt-ip-type-b', 'L2 Service');
            }
            
            if (link.linkDetails.transceiverA) {
                this.setFieldValue(editor, 'lt-transceiver-a', link.linkDetails.transceiverA);
                dnaasAutoFilled = true;
            }
            if (link.linkDetails.transceiverB) {
                this.setFieldValue(editor, 'lt-transceiver-b', link.linkDetails.transceiverB);
                dnaasAutoFilled = true;
            }
            
            // Speed/MTU/FEC tooltips
            if (link.linkDetails.speedA) {
                const ifField = document.getElementById('lt-interface-a');
                if (ifField) ifField.title = `Speed: ${link.linkDetails.speedA}, MTU: ${link.linkDetails.mtuA || 'N/A'}, FEC: ${link.linkDetails.fecA || 'auto'}`;
            }
            if (link.linkDetails.speedB) {
                const ifField = document.getElementById('lt-interface-b');
                if (ifField) ifField.title = `Speed: ${link.linkDetails.speedB}, MTU: ${link.linkDetails.mtuB || 'N/A'}, FEC: ${link.linkDetails.fecB || 'auto'}`;
            }
            
            // Oper state indicators
            if (link.linkDetails.operStateA) {
                const ifField = document.getElementById('lt-interface-a');
                if (ifField) {
                    const state = link.linkDetails.operStateA.toLowerCase();
                    ifField.style.borderColor = state === 'up' ? '#27ae60' : state === 'down' ? '#e74c3c' : '';
                }
            }
            if (link.linkDetails.operStateB) {
                const ifField = document.getElementById('lt-interface-b');
                if (ifField) {
                    const state = link.linkDetails.operStateB.toLowerCase();
                    ifField.style.borderColor = state === 'up' ? '#27ae60' : state === 'down' ? '#e74c3c' : '';
                }
            }
            
            if (dnaasAutoFilled) this.showDnaasAutoFillIndicator(editor);
        }
        
        // Network Layer
        let ipTypeA = link.device1IpType;
        let ipTypeB = link.device2IpType;
        if (link.linkDetails) {
            if (link.linkDetails.l2ServiceA && !ipTypeA) ipTypeA = 'L2 Service';
            if (link.linkDetails.l2ServiceB && !ipTypeB) ipTypeB = 'L2 Service';
            if (!ipTypeA && link.linkDetails.bd_name) ipTypeA = 'L2 Service';
            if (!ipTypeB && link.linkDetails.bd_name) ipTypeB = 'L2 Service';
        }
        this.setFieldValue(editor, 'lt-ip-type-a', ipTypeA);
        this.setFieldValue(editor, 'lt-ip-type-b', ipTypeB);
        this.setFieldValue(editor, 'lt-ip-addr-a', link.device1IpAddress || (ipTypeA === 'L2 Service' ? 'N/A for L2 Service' : ''));
        this.setFieldValue(editor, 'lt-ip-addr-b', link.device2IpAddress || (ipTypeB === 'L2 Service' ? 'N/A for L2 Service' : ''));
        
        // VLAN
        let vlanModeA = link.device1VlanMode;
        let vlanModeB = link.device2VlanMode;
        let vlanIdA = link.device1VlanId;
        let vlanIdB = link.device2VlanId;
        let outerTagA = link.device1OuterTag;
        let outerTagB = link.device2OuterTag;
        
        if (link.linkDetails) {
            if (!vlanModeA && link.linkDetails.vlanIdA) vlanModeA = 'vlan-id';
            if (!vlanModeB && link.linkDetails.vlanIdB) vlanModeB = 'vlan-id';
            if (!vlanIdA && link.linkDetails.vlanIdA) vlanIdA = link.linkDetails.vlanIdA;
            if (!vlanIdB && link.linkDetails.vlanIdB) vlanIdB = link.linkDetails.vlanIdB;
            if (!outerTagA && link.linkDetails.vlanIdA) outerTagA = link.linkDetails.vlanIdA;
            if (!outerTagB && link.linkDetails.vlanIdB) outerTagB = link.linkDetails.vlanIdB;
        }
        
        this.setFieldValue(editor, 'lt-vlan-mode-a', vlanModeA);
        this.setFieldValue(editor, 'lt-vlan-mode-b', vlanModeB);
        this.setFieldValue(editor, 'lt-vlan-id-a', vlanIdA);
        this.setFieldValue(editor, 'lt-vlan-id-b', vlanIdB);
        this.setFieldValue(editor, 'lt-vlan-tpid-a', link.device1VlanTpid || (vlanModeA === 'vlan-id' ? '0x8100' : ''));
        this.setFieldValue(editor, 'lt-vlan-tpid-b', link.device2VlanTpid || (vlanModeB === 'vlan-id' ? '0x8100' : ''));
        this.setFieldValue(editor, 'lt-outer-tag-a', outerTagA);
        this.setFieldValue(editor, 'lt-outer-tag-b', outerTagB);
        this.setFieldValue(editor, 'lt-inner-tag-a', link.device1InnerTag);
        this.setFieldValue(editor, 'lt-inner-tag-b', link.device2InnerTag);
        
        // Traffic Control
        this.setFieldValue(editor, 'lt-ingress-a', link.device1IngressAction);
        this.setFieldValue(editor, 'lt-ingress-b', link.device2IngressAction);
        this.setFieldValue(editor, 'lt-egress-a', link.device1EgressAction);
        this.setFieldValue(editor, 'lt-egress-b', link.device2EgressAction);
        this.setFieldValue(editor, 'lt-dnaas-vlan-a', link.device1DnaasVlan);
        this.setFieldValue(editor, 'lt-dnaas-vlan-b', link.device2DnaasVlan);
        
        // Update visibility
        this.updateIpAddressFieldVisibility(editor);
        this.updateVlanFieldsVisibility(editor);
    },

    /**
     * Auto-fill from DNAAS discovery cache
     */
    autoFillFromDnaasDiscovery(editor, link, device1InterfaceName, device2InterfaceName) {
        const discoveryData = window._dnaasDiscoveryData;
        if (!discoveryData) return;
        
        const metadata = discoveryData.metadata;
        if (!metadata) return;
        
        const device1 = editor.objects.find(d => d.id === link.device1);
        const device2 = editor.objects.find(d => d.id === link.device2);
        const hostname1 = device1?.label;
        const hostname2 = device2?.label;
        
        let autoFilledCount = 0;
        const bdMapping = metadata.device_bd_mapping || {};
        
        if (hostname1 && bdMapping[hostname1]) {
            const deviceBds = bdMapping[hostname1].bridge_domains || [];
            if (deviceBds.length > 0) {
                const bdInfo = metadata.bridge_domains?.find(b => b.name === deviceBds[0]);
                if (bdInfo && bdInfo.vlan) {
                    const vlanField = document.getElementById('lt-dnaas-vlan-a');
                    if (vlanField && !vlanField.value) {
                        vlanField.value = bdInfo.vlan;
                        autoFilledCount++;
                    }
                }
                if (!link.linkDetails) link.linkDetails = {};
                link.linkDetails.bridgeDomainsA = deviceBds;
            }
        }
        
        if (hostname2 && bdMapping[hostname2]) {
            const deviceBds = bdMapping[hostname2].bridge_domains || [];
            if (deviceBds.length > 0) {
                const bdInfo = metadata.bridge_domains?.find(b => b.name === deviceBds[0]);
                if (bdInfo && bdInfo.vlan) {
                    const vlanField = document.getElementById('lt-dnaas-vlan-b');
                    if (vlanField && !vlanField.value) {
                        vlanField.value = bdInfo.vlan;
                        autoFilledCount++;
                    }
                }
                if (!link.linkDetails) link.linkDetails = {};
                link.linkDetails.bridgeDomainsB = deviceBds;
            }
        }
        
        if (link.linkDetails?.bridgeDomains && link.linkDetails.bridgeDomains.length > 0) {
            const firstBd = link.linkDetails.bridgeDomains[0];
            if (firstBd.vlan_id) {
                const vlanFieldA = document.getElementById('lt-vlan-id-a');
                const vlanFieldB = document.getElementById('lt-vlan-id-b');
                if (vlanFieldA && !vlanFieldA.value) { vlanFieldA.value = firstBd.vlan_id; autoFilledCount++; }
                if (vlanFieldB && !vlanFieldB.value) { vlanFieldB.value = firstBd.vlan_id; autoFilledCount++; }
            }
            if (firstBd.bd_name) {
                link.linkDetails.bdNameA = firstBd.bd_name;
                link.linkDetails.bdNameB = firstBd.bd_name;
            }
        }
        
        if (link.linkDetails?.interfaceA) {
            const bundleField = document.getElementById('lt-bundle-a');
            if (bundleField && !bundleField.value) { bundleField.value = link.linkDetails.interfaceA; autoFilledCount++; }
        }
        if (link.linkDetails?.interfaceB) {
            const bundleField = document.getElementById('lt-bundle-b');
            if (bundleField && !bundleField.value) { bundleField.value = link.linkDetails.interfaceB; autoFilledCount++; }
        }
        
        if (autoFilledCount > 0) {
            this.showDnaasAutoFillIndicator(editor);
            console.log(`[LinkTableManager] DNAAS auto-filled ${autoFilledCount} field(s)`);
        }
    },

    /**
     * Set field value helper
     */
    setFieldValue(editor, elementId, value) {
        if (editor.linkEditor && typeof editor.linkEditor.setFieldValue === 'function') {
            return editor.linkEditor.setFieldValue(elementId, value);
        }
        const el = document.getElementById(elementId);
        if (el) el.value = value || '';
    },

    /**
     * Show DNAAS auto-fill indicator
     */
    showDnaasAutoFillIndicator(editor) {
        if (editor.linkEditor && typeof editor.linkEditor.showDnaasAutoFillIndicator === 'function') {
            return editor.linkEditor.showDnaasAutoFillIndicator();
        }
    },

    /**
     * Update IP address field visibility
     */
    updateIpAddressFieldVisibility(editor) {
        if (editor.linkEditor && typeof editor.linkEditor.updateIpAddressFieldVisibility === 'function') {
            return editor.linkEditor.updateIpAddressFieldVisibility();
        }
    },

    /**
     * Update VLAN fields visibility based on mode
     */
    updateVlanFieldsVisibility(editor) {
        if (editor.linkEditor && typeof editor.linkEditor.updateVlanFieldsVisibility === 'function') {
            return editor.linkEditor.updateVlanFieldsVisibility();
        }
        
        const modeA = document.getElementById('lt-vlan-mode-a')?.value || '';
        const modeB = document.getElementById('lt-vlan-mode-b')?.value || '';
        
        const vlanIdRow = document.getElementById('lt-vlan-id-row');
        const tpidRow = document.getElementById('lt-vlan-tpid-row');
        const outerTagRow = document.getElementById('lt-outer-tag-row');
        const innerTagRow = document.getElementById('lt-inner-tag-row');
        
        const showVlanId = modeA === 'vlan-id' || modeB === 'vlan-id';
        const showVlanTags = modeA === 'vlan-tags' || modeB === 'vlan-tags';
        
        if (vlanIdRow) vlanIdRow.style.display = showVlanId ? '' : 'none';
        if (tpidRow) tpidRow.style.display = showVlanTags ? '' : 'none';
        if (outerTagRow) outerTagRow.style.display = showVlanTags ? '' : 'none';
        if (innerTagRow) innerTagRow.style.display = showVlanTags ? '' : 'none';
        
        const vlanIdA = document.getElementById('lt-vlan-id-a');
        const tpidA = document.getElementById('lt-vlan-tpid-a');
        const outerA = document.getElementById('lt-outer-tag-a');
        const innerA = document.getElementById('lt-inner-tag-a');
        
        if (vlanIdA) vlanIdA.disabled = modeA !== 'vlan-id';
        if (tpidA) tpidA.disabled = modeA !== 'vlan-tags';
        if (outerA) outerA.disabled = modeA !== 'vlan-tags';
        if (innerA) innerA.disabled = modeA !== 'vlan-tags';
        
        const vlanIdB = document.getElementById('lt-vlan-id-b');
        const tpidB = document.getElementById('lt-vlan-tpid-b');
        const outerB = document.getElementById('lt-outer-tag-b');
        const innerB = document.getElementById('lt-inner-tag-b');
        
        if (vlanIdB) vlanIdB.disabled = modeB !== 'vlan-id';
        if (tpidB) tpidB.disabled = modeB !== 'vlan-tags';
        if (outerB) outerB.disabled = modeB !== 'vlan-tags';
        if (innerB) innerB.disabled = modeB !== 'vlan-tags';
    },

    /**
     * Setup Link Table validation listeners
     */
    setupValidation(editor) {
        const platformCatA = document.getElementById('lt-platform-cat-a');
        const platformCatB = document.getElementById('lt-platform-cat-b');
        const platformModelA = document.getElementById('lt-platform-model-a');
        const platformModelB = document.getElementById('lt-platform-model-b');
        
        if (platformCatA) {
            platformCatA.addEventListener('change', () => {
                editor.populateModelsForCategory('lt-platform-model-a', platformCatA.value);
                editor.autoSaveLinkTable();
            });
        }
        if (platformCatB) {
            platformCatB.addEventListener('change', () => {
                editor.populateModelsForCategory('lt-platform-model-b', platformCatB.value);
                editor.autoSaveLinkTable();
            });
        }
        
        if (platformModelA) {
            platformModelA.addEventListener('change', () => {
                const category = editor.deriveCategoryFromModel(platformModelA.value);
                if (category && platformCatA && !platformCatA.value) {
                    this.setFieldValue(editor, 'lt-platform-cat-a', category);
                }
                editor.populateInterfaces('lt-interface-a', platformModelA.value);
                editor.autoSaveLinkTable();
            });
        }
        if (platformModelB) {
            platformModelB.addEventListener('change', () => {
                const category = editor.deriveCategoryFromModel(platformModelB.value);
                if (category && platformCatB && !platformCatB.value) {
                    this.setFieldValue(editor, 'lt-platform-cat-b', category);
                }
                editor.populateInterfaces('lt-interface-b', platformModelB.value);
                editor.autoSaveLinkTable();
            });
        }
        
        const interfaceA = document.getElementById('lt-interface-a');
        const interfaceB = document.getElementById('lt-interface-b');
        
        if (interfaceA) {
            interfaceA.addEventListener('change', () => {
                if (interfaceA.value === '__custom__') {
                    editor.handleCustomInterfaceInput('lt-interface-a');
                } else {
                    editor.autoSaveLinkTable();
                }
            });
        }
        if (interfaceB) {
            interfaceB.addEventListener('change', () => {
                if (interfaceB.value === '__custom__') {
                    editor.handleCustomInterfaceInput('lt-interface-b');
                } else {
                    editor.autoSaveLinkTable();
                }
            });
        }
        
        const ipTypeA = document.getElementById('lt-ip-type-a');
        const ipTypeB = document.getElementById('lt-ip-type-b');
        
        if (ipTypeA) {
            ipTypeA.addEventListener('change', () => {
                this.updateIpAddressFieldVisibility(editor);
                editor.validateIpField('lt-ip-addr-a', ipTypeA.value);
                editor.autoSaveLinkTable();
            });
        }
        if (ipTypeB) {
            ipTypeB.addEventListener('change', () => {
                this.updateIpAddressFieldVisibility(editor);
                editor.validateIpField('lt-ip-addr-b', ipTypeB.value);
                editor.autoSaveLinkTable();
            });
        }
        
        const ipAddrA = document.getElementById('lt-ip-addr-a');
        const ipAddrB = document.getElementById('lt-ip-addr-b');
        
        if (ipAddrA) {
            ipAddrA.addEventListener('blur', () => {
                const ipType = document.getElementById('lt-ip-type-a')?.value || '';
                editor.validateIpField('lt-ip-addr-a', ipType);
                editor.autoSaveLinkTable();
            });
        }
        if (ipAddrB) {
            ipAddrB.addEventListener('blur', () => {
                const ipType = document.getElementById('lt-ip-type-b')?.value || '';
                editor.validateIpField('lt-ip-addr-b', ipType);
                editor.autoSaveLinkTable();
            });
        }
        
        const vlanModeA = document.getElementById('lt-vlan-mode-a');
        const vlanModeB = document.getElementById('lt-vlan-mode-b');
        
        if (vlanModeA) {
            vlanModeA.addEventListener('change', () => {
                this.updateVlanFieldsVisibility(editor);
                editor.autoSaveLinkTable();
            });
        }
        if (vlanModeB) {
            vlanModeB.addEventListener('change', () => {
                this.updateVlanFieldsVisibility(editor);
                editor.autoSaveLinkTable();
            });
        }
        
        this.updateVlanFieldsVisibility(editor);
        
        const vlanFields = ['lt-vlan-id-a', 'lt-vlan-id-b', 'lt-outer-tag-a', 'lt-outer-tag-b', 
                          'lt-inner-tag-a', 'lt-inner-tag-b', 'lt-dnaas-vlan-a', 'lt-dnaas-vlan-b'];
        vlanFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('blur', () => {
                    editor.validateVlanField(fieldId);
                    editor.autoSaveLinkTable();
                });
                field.addEventListener('input', () => editor.validateVlanField(fieldId));
            }
        });
        
        const allFields = [
            'lt-interface-a', 'lt-interface-b',
            'lt-transceiver-a', 'lt-transceiver-b',
            'lt-vlan-tpid-a', 'lt-vlan-tpid-b',
            'lt-ingress-a', 'lt-ingress-b',
            'lt-egress-a', 'lt-egress-b'
        ];
        allFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.addEventListener('change', () => editor.autoSaveLinkTable());
            }
        });
        
        this.setupSubInterfaceVlanValidation(editor);
    },

    /**
     * Setup sub-interface VLAN validation
     */
    setupSubInterfaceVlanValidation(editor) {
        const subInterfaceA = document.getElementById('lt-subinterface-a');
        const subInterfaceB = document.getElementById('lt-subinterface-b');
        const vlanMatchIndicator = document.getElementById('lt-vlan-match-indicator');
        
        const validateVlanMatch = () => {
            if (!vlanMatchIndicator) return;
            
            const subIfA = subInterfaceA?.value || '';
            const subIfB = subInterfaceB?.value || '';
            
            if (!subIfA && !subIfB) {
                vlanMatchIndicator.textContent = '--';
                vlanMatchIndicator.className = 'vlan-match-indicator match-pending';
                vlanMatchIndicator.title = 'Enter sub-interfaces to validate VLAN match';
                return;
            }
            
            if (!subIfA || !subIfB) {
                vlanMatchIndicator.textContent = '?';
                vlanMatchIndicator.className = 'vlan-match-indicator match-pending';
                vlanMatchIndicator.title = 'Fill both sub-interface fields to validate';
                return;
            }
            
            const result = editor.validateVlanMatch(subIfA, subIfB);
            
            if (result.match) {
                vlanMatchIndicator.textContent = `${result.vlanA}`;
                vlanMatchIndicator.className = 'vlan-match-indicator match-ok';
                vlanMatchIndicator.title = `VLANs match: ${result.vlanA}`;
            } else {
                vlanMatchIndicator.textContent = `${result.vlanA}/${result.vlanB}`;
                vlanMatchIndicator.className = 'vlan-match-indicator match-fail';
                vlanMatchIndicator.title = result.reason;
            }
            
            if (editor.editingLink) {
                editor.editingLink.linkDetails = editor.editingLink.linkDetails || {};
                editor.editingLink.linkDetails.subInterfaceA = subIfA;
                editor.editingLink.linkDetails.subInterfaceB = subIfB;
                editor.editingLink.linkDetails.vlanIdA = result.vlanA;
                editor.editingLink.linkDetails.vlanIdB = result.vlanB;
                editor.editingLink.linkDetails.vlanMatch = result.match;
            }
        };
        
        if (subInterfaceA) {
            subInterfaceA.addEventListener('input', validateVlanMatch);
            subInterfaceA.addEventListener('blur', () => {
                validateVlanMatch();
                editor.autoSaveLinkTable();
            });
        }
        if (subInterfaceB) {
            subInterfaceB.addEventListener('input', validateVlanMatch);
            subInterfaceB.addEventListener('blur', () => {
                validateVlanMatch();
                editor.autoSaveLinkTable();
            });
        }
        
        const bundleA = document.getElementById('lt-bundle-a');
        const bundleB = document.getElementById('lt-bundle-b');
        if (bundleA) bundleA.addEventListener('blur', () => editor.autoSaveLinkTable());
        if (bundleB) bundleB.addEventListener('blur', () => editor.autoSaveLinkTable());
        
        validateVlanMatch();
    },

    /**
     * Update link value from form field
     */
    updateValue(editor, inputId, value) {
        if (editor.linkEditor && typeof editor.linkEditor.updateValue === 'function') {
            return editor.linkEditor.updateValue(inputId, value);
        }
        
        if (!editor.editingLink) return;
        
        const fieldMappings = {
            'lt-platform-cat-a': 'device1PlatformCategory',
            'lt-platform-cat-b': 'device2PlatformCategory',
            'lt-platform-model-a': 'device1Platform',
            'lt-platform-model-b': 'device2Platform',
            'lt-interface-a': 'device1Interface',
            'lt-interface-b': 'device2Interface',
            'lt-transceiver-a': 'device1Transceiver',
            'lt-transceiver-b': 'device2Transceiver',
            'lt-ip-type-a': 'device1IpType',
            'lt-ip-type-b': 'device2IpType',
            'lt-ip-addr-a': 'device1IpAddress',
            'lt-ip-addr-b': 'device2IpAddress',
            'lt-vlan-tpid-a': 'device1VlanTpid',
            'lt-vlan-tpid-b': 'device2VlanTpid',
            'lt-outer-tag-a': 'device1OuterTag',
            'lt-outer-tag-b': 'device2OuterTag',
            'lt-inner-tag-a': 'device1InnerTag',
            'lt-inner-tag-b': 'device2InnerTag',
            'lt-ingress-a': 'device1IngressAction',
            'lt-ingress-b': 'device2IngressAction',
            'lt-egress-a': 'device1EgressAction',
            'lt-egress-b': 'device2EgressAction',
            'lt-dnaas-vlan-a': 'device1DnaasVlan',
            'lt-dnaas-vlan-b': 'device2DnaasVlan'
        };
        
        const property = fieldMappings[inputId];
        if (property) {
            editor.editingLink[property] = value;
            this.updateCalculatedFields(editor);
        }
    },

    /**
     * Update calculated fields
     */
    updateCalculatedFields(editor) {
        if (editor.linkEditor && typeof editor.linkEditor.updateCalculatedFields === 'function') {
            return editor.linkEditor.updateCalculatedFields();
        }
        
        if (!editor.editingLink) return;
        
        const outerA = document.getElementById('lt-outer-tag-a')?.value || '';
        const innerA = document.getElementById('lt-inner-tag-a')?.value || '';
        const stackA = document.getElementById('lt-vlan-stack-a');
        if (stackA) {
            stackA.value = outerA && innerA ? `${outerA}.${innerA}` : outerA || '';
        }
        
        const outerB = document.getElementById('lt-outer-tag-b')?.value || '';
        const innerB = document.getElementById('lt-inner-tag-b')?.value || '';
        const stackB = document.getElementById('lt-vlan-stack-b');
        if (stackB) {
            stackB.value = outerB && innerB ? `${outerB}.${innerB}` : outerB || '';
        }
        
        const ingressA = document.getElementById('lt-ingress-a')?.value || '';
        const egressA = document.getElementById('lt-egress-a')?.value || '';
        const manipA = document.getElementById('lt-manip-summary-a');
        if (manipA) {
            const parts = [];
            if (ingressA) parts.push(`In: ${ingressA}`);
            if (egressA) parts.push(`Out: ${egressA}`);
            manipA.value = parts.join(' | ') || 'None';
        }
        
        const ingressB = document.getElementById('lt-ingress-b')?.value || '';
        const egressB = document.getElementById('lt-egress-b')?.value || '';
        const manipB = document.getElementById('lt-manip-summary-b');
        if (manipB) {
            const parts = [];
            if (ingressB) parts.push(`In: ${ingressB}`);
            if (egressB) parts.push(`Out: ${egressB}`);
            manipB.value = parts.join(' | ') || 'None';
        }
    },

    /**
     * Reset all fields
     */
    resetFields(editor) {
        if (editor.linkEditor && typeof editor.linkEditor.resetFields === 'function') {
            return editor.linkEditor.resetFields();
        }
        
        if (!editor.editingLink) return;
        
        const inputs = document.querySelectorAll('.link-table-modal input:not([readonly]), .link-table-modal select');
        inputs.forEach(input => {
            if (input.type === 'number') input.value = '';
            else if (input.tagName === 'SELECT') input.selectedIndex = 0;
            else input.value = '';
            input.classList.remove('valid', 'invalid');
        });
        
        const properties = [
            'device1PlatformCategory', 'device2PlatformCategory',
            'device1Platform', 'device2Platform',
            'device1Interface', 'device2Interface',
            'device1Transceiver', 'device2Transceiver',
            'device1IpType', 'device2IpType',
            'device1IpAddress', 'device2IpAddress',
            'device1VlanMode', 'device2VlanMode',
            'device1VlanId', 'device2VlanId',
            'device1VlanTpid', 'device2VlanTpid',
            'device1OuterTag', 'device2OuterTag',
            'device1InnerTag', 'device2InnerTag',
            'device1IngressAction', 'device2IngressAction',
            'device1EgressAction', 'device2EgressAction',
            'device1DnaasVlan', 'device2DnaasVlan'
        ];
        
        properties.forEach(prop => { editor.editingLink[prop] = ''; });
        
        this.updateVlanFieldsVisibility(editor);
        this.updateCalculatedFields(editor);
    },

    /**
     * Copy as Markdown
     */
    copyAsMarkdown(editor) {
        if (editor.linkEditor && typeof editor.linkEditor.copyAsMarkdown === 'function') {
            return editor.linkEditor.copyAsMarkdown();
        }
        
        if (!editor.editingLink) return;
        
        const device1Name = document.getElementById('link-device1-name')?.textContent || 'Side A';
        const device2Name = document.getElementById('link-device2-name')?.textContent || 'Side B';
        const link = editor.editingLink;
        
        let markdown = `# Link Connection: ${device1Name} ↔ ${device2Name}\n\n`;
        markdown += `| Property | ${device1Name} | ${device2Name} |\n`;
        markdown += `|----------|----------|----------|\n`;
        markdown += `| Platform Category | ${link.device1PlatformCategory || '-'} | ${link.device2PlatformCategory || '-'} |\n`;
        markdown += `| Platform Model | ${link.device1Platform || '-'} | ${link.device2Platform || '-'} |\n`;
        markdown += `| Interface | ${link.device1Interface || '-'} | ${link.device2Interface || '-'} |\n`;
        markdown += `| Transceiver | ${link.device1Transceiver || '-'} | ${link.device2Transceiver || '-'} |\n`;
        markdown += `| IP Type | ${link.device1IpType || '-'} | ${link.device2IpType || '-'} |\n`;
        markdown += `| IP Address | ${link.device1IpAddress || '-'} | ${link.device2IpAddress || '-'} |\n`;
        markdown += `| VLAN TPID | ${link.device1VlanTpid || '-'} | ${link.device2VlanTpid || '-'} |\n`;
        markdown += `| Outer Tag | ${link.device1OuterTag || '-'} | ${link.device2OuterTag || '-'} |\n`;
        markdown += `| Inner Tag | ${link.device1InnerTag || '-'} | ${link.device2InnerTag || '-'} |\n`;
        markdown += `| Ingress Action | ${link.device1IngressAction || '-'} | ${link.device2IngressAction || '-'} |\n`;
        markdown += `| Egress Action | ${link.device1EgressAction || '-'} | ${link.device2EgressAction || '-'} |\n`;
        markdown += `| DNaaS VLAN | ${link.device1DnaasVlan || '-'} | ${link.device2DnaasVlan || '-'} |\n`;
        
        navigator.clipboard.writeText(markdown).then(() => {
            this.showToast(editor, 'Copied as Markdown!', 'success');
        }).catch(err => {
            console.error('Failed to copy:', err);
            this.showToast(editor, 'Failed to copy', 'error');
        });
    },

    /**
     * Show toast notification
     */
    showToast(editor, message, type = 'info') {
        if (editor.linkEditor && typeof editor.linkEditor.showToast === 'function') {
            return editor.linkEditor.showToast(message, type);
        }
        
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
            padding: 12px 24px; background: ${type === 'success' ? '#2ea043' : type === 'error' ? '#d73a49' : '#007acc'};
            color: white; border-radius: 6px; font-size: 14px; font-weight: 500;
            z-index: 100002; animation: fadeInUp 0.3s ease-out; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        `;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'fadeOutDown 0.3s ease-out forwards';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }
};

console.log('[topology-link-table.js] LinkTableManager loaded');
