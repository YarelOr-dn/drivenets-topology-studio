// REFACTORING GUIDE - Topology Editor Modular Structure
//
// The topology.js file has been split into logical modules:
//
// 1. topology-history.js - Undo/Redo system (saveState, restoreState, undo, redo)
// 2. topology-devices.js - Device operations (placement, manipulation, properties)
// 3. topology-links.js - Link operations (creation, curve calculations)
// 4. topology-magnetic.js - Magnetic field and obstacle detection
// 5. topology-ui.js - UI management (modes, properties panel, indicators)
// 6. topology-input.js - Input handling (mouse, keyboard, touch)
// 7. topology-drawing.js - Canvas rendering (draw functions)
// 8. topology-files.js - File operations (save, load, auto-save)
// 9. topology-grid.js - Grid system and HUD
//
// Each module extends the TopologyEditor prototype or is used via composition.
// Load order in index.html:
// 1. topology-core.js (base class)
// 2. topology-history.js
// 3. topology-devices.js
// 4. topology-links.js
// 5. topology-magnetic.js
// 6. topology-ui.js
// 7. topology-input.js
// 8. topology-drawing.js
// 9. topology-files.js
// 10. topology-grid.js
// 11. topology.js (main initialization)

// IMPORTANT: All modules must be loaded before topology.js initializes

