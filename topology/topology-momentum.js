// Momentum/Sliding System for Topology Editor
// Devices continue moving after release based on drag velocity
// Integrates with collision detection

class MomentumEngine {
    constructor(editor) {
        this.editor = editor;
        this.enabled = localStorage.getItem('momentum_enabled') !== 'false'; // ON by default
        
        // REVERSED FRICTION SYSTEM: Load slider value (1-10) and calculate friction
        const storedSlider = parseInt(localStorage.getItem('momentum_slider'));
        const storedFriction = parseFloat(localStorage.getItem('momentum_friction'));
        
        // If we have a stored slider value, use it; otherwise try friction value; otherwise default to 5
        if (storedSlider && storedSlider >= 1 && storedSlider <= 10) {
            // Calculate friction from slider: 1→0.85 (far), 10→0.98 (short)
            this.friction = 0.85 + (storedSlider - 1) * (0.13 / 9);
            this.sliderValue = storedSlider;
        } else if (storedFriction && storedFriction >= 0.85 && storedFriction <= 0.98) {
            // Reverse-calculate slider from friction
            this.friction = storedFriction;
            this.sliderValue = Math.round(1 + (storedFriction - 0.85) * (9 / 0.13));
        } else {
            // Default: slider 5 = friction 0.92 (balanced)
            this.friction = 0.92;
            this.sliderValue = 5;
        }
        
        // ULTRA-ENHANCED: Dynamic parameters based on slider value
        // Slider 1-10: Low values = MASSIVE slides, High values = Short slides
        this.updateDynamicParameters();
        
        this.chainCollisionEnabled = true; // ENHANCED: Enable billiard-ball chain reactions
        this.smoothingEnabled = true; // Enable sub-pixel interpolation for smooth visuals
        this.activeSlides = new Map(); // Track sliding objects
        this.velocityHistory = []; // Track recent velocities for drag
        this.maxVelocityHistory = 8; // ENHANCED: More samples for better velocity calculation
        this.animationFrame = null;
        this.chainReactions = 0; // Track chain collision count for debugger
        this.collisionThisFrame = new Set(); // Prevent multiple collisions in same frame
        
        // Update UI slider if it exists
        setTimeout(() => {
            const frictionSlider = document.getElementById('friction-slider');
            const frictionValueDisplay = document.getElementById('friction-value');
            if (frictionSlider) {
                frictionSlider.value = this.sliderValue;
            }
            if (frictionValueDisplay) {
                frictionValueDisplay.textContent = this.sliderValue;
            }
        }, 100);
    }

    // ULTRA-ENHANCED: Update dynamic parameters based on slider value
    updateDynamicParameters() {
        // Slider value determines ALL physics parameters for dramatic effect
        const slider = this.sliderValue;
        
        if (this.editor?.debugger) {
            this.editor.debugger.logAction(`🎮 Updating slide parameters: Slider = ${slider}/10`);
        }
        
        // 1. FRICTION: Controls deceleration rate (lower = slides farther)
        //    Slider 1 → friction 0.75 (ultra-smooth, slides EXTREMELY far) - ARCADE MODE!
        //    Slider 5 → friction 0.90 (balanced, still slides nicely)
        //    Slider 10 → friction 0.97 (high friction, stops quickly)
        this.friction = 0.75 + (slider - 1) * (0.22 / 9);
        
        // 2. VELOCITY MULTIPLIER: Amplifies initial velocity (higher = faster starts)
        //    Slider 1 → 8.0x (INSANE arcade launches!) - MAXIMUM ARCADE!
        //    Slider 5 → 5.5x (balanced, very responsive)
        //    Slider 10 → 3.0x (gentle but still boosted)
        this.velocityMultiplier = 8.0 - (slider - 1) * (5.0 / 9);
        
        // 3. MIN VELOCITY: Threshold to START sliding (lower = more responsive)
        //    Slider 1 → 0.01 (ULTRA-sensitive - any movement triggers slide!)
        //    Slider 5 → 0.08 (balanced, very easy to trigger)
        //    Slider 10 → 0.20 (still very responsive)
        this.minVelocity = 0.01 + (slider - 1) * (0.19 / 9);
        
        // 4. MAX SPEED: Cap on velocity (higher = allows faster slides)
        //    Slider 1 → 200 px/frame (BLAZING FAST!) - ARCADE SPEED!
        //    Slider 5 → 130 px/frame (balanced, very fast)
        //    Slider 10 → 80 px/frame (controlled but still fast)
        this.maxSpeed = 200 - (slider - 1) * (120 / 9);
        
        // 5. COLLISION BOOST: Energy added on collision (higher = more dramatic bumps)
        //    Slider 1 → 2.5x (250% energy boost!) - ARCADE PINBALL!
        //    Slider 5 → 1.8x (balanced, still dramatic)
        //    Slider 10 → 1.3x (gentle but energetic)
        this.collisionBoost = 2.5 - (slider - 1) * (1.2 / 9);
        
        // 6. RESTITUTION: Energy retention in collisions (>1.0 = energy GAIN!)
        //    Slider 1 → 1.15 (115% restitution - GAIN energy on hit!) - ARCADE CHAOS!
        //    Slider 5 → 1.05 (slight energy gain)
        //    Slider 10 → 0.95 (slight loss)
        this.restitution = 1.15 - (slider - 1) * (0.20 / 9);
        
        // 7. MOMENTUM TRANSFER: How much momentum transfers to hit objects
        //    Slider 1 → 1.00 (100% transfer - MAXIMUM chain reactions!)
        //    Slider 5 → 0.90 (balanced, strong chains)
        //    Slider 10 → 0.75 (dampened but still chained)
        this.momentumTransferRatio = 1.00 - (slider - 1) * (0.25 / 9);
        
        // 8. ROLLING FRICTION: Nearly zero for arcade smoothness
        //    Slider 1 → 0.001 (almost frictionless - air hockey table!)
        //    Slider 5 → 0.003 (very smooth)
        //    Slider 10 → 0.006 (slight friction)
        this.rollingFriction = 0.001 + (slider - 1) * (0.005 / 9);
        
        this.smoothingEnabled = true; // Always enable smooth sub-pixel interpolation
        
        // Log confirmation to debugger
        if (this.editor?.debugger) {
            this.editor.debugger.logSuccess(`🎮 ARCADE MODE: All physics parameters updated for slider ${slider}/10`);
            this.editor.debugger.logInfo(`   Friction: ${this.friction.toFixed(3)} | Velocity: ${this.velocityMultiplier.toFixed(1)}x | Min: ${this.minVelocity.toFixed(3)} | Max: ${this.maxSpeed.toFixed(0)}px/f`);
        }
    }

    // Track drag velocity
    trackVelocity(dx, dy, dt) {
        if (dt === 0) return;
        
        const vx = dx / dt;
        const vy = dy / dt;
        
        this.velocityHistory.push({ vx, vy, time: Date.now() });
        
        // Keep only recent samples
        if (this.velocityHistory.length > this.maxVelocityHistory) {
            this.velocityHistory.shift();
        }
    }

    // Calculate average velocity from recent drag with ULTRA sensitivity
    calculateReleaseVelocity() {
        if (this.velocityHistory.length === 0) {
            return { vx: 0, vy: 0 };
        }
        
        const now = Date.now();
        
        // CRITICAL FIX: Check if mouse was stationary at release
        // Look at the last 50ms - if no samples or very low velocity, don't slide
        const veryRecent = this.velocityHistory.filter(v => now - v.time < 50);
        if (veryRecent.length === 0) {
            // No movement in the last 50ms = mouse was held still before release
            // Don't apply momentum
            return { vx: 0, vy: 0 };
        }
        
        // Check if the very recent samples have significant velocity
        const lastSample = veryRecent[veryRecent.length - 1];
        const lastSpeed = Math.sqrt(lastSample.vx * lastSample.vx + lastSample.vy * lastSample.vy);
        if (lastSpeed < 0.5) {
            // Mouse was essentially stationary at release
            return { vx: 0, vy: 0 };
        }
        
        // ARCADE MODE: Use recent samples (last 200ms) - captures even quick flicks!
        const recent = this.velocityHistory.filter(v => now - v.time < 200);
        
        if (recent.length === 0) {
            return { vx: 0, vy: 0 };
        }
        
        // ARCADE PHYSICS: INSANE weighting - last microsecond determines EVERYTHING!
        let totalWeight = 0;
        let weightedVx = 0;
        let weightedVy = 0;
        
        recent.forEach((v, index) => {
            // EXPONENTIAL ARCADE WEIGHTING: last sample is KING!
            const weight = Math.pow(index + 1, 2.5); // Even more exponential for instant arcade response!
            weightedVx += v.vx * weight;
            weightedVy += v.vy * weight;
            totalWeight += weight;
        });
        
        // ULTRA-ENHANCED: Apply velocity multiplier + sensitivity boost for short drags
        const avgVx = weightedVx / totalWeight;
        const avgVy = weightedVy / totalWeight;
        
        // ARCADE MODE: MASSIVE boost for quick flicks - instant gratification!
        // Tiny flicks (< 2 samples) = 4.0x boost - ARCADE ROCKET!
        // Short drags (< 4 samples) = 3.0x boost - SUPER RESPONSIVE!
        // Medium drags (< 6 samples) = 2.0x boost - STILL DRAMATIC!
        // Long drags = 1.5x boost - EVERYTHING SLIDES!
        const sensitivityBoost = recent.length < 2 ? 4.0 : (recent.length < 4 ? 3.0 : (recent.length < 6 ? 2.0 : 1.5));
        
        return {
            vx: avgVx * this.velocityMultiplier * sensitivityBoost,
            vy: avgVy * this.velocityMultiplier * sensitivityBoost
        };
    }

    // Start sliding for an object
    startSlide(obj, vx, vy) {
        if (!this.enabled) return;
        
        const speed = Math.sqrt(vx * vx + vy * vy);
        
        // ENHANCED: Lower threshold for more sensitivity
        if (speed < this.minVelocity) return;
        
        // ENHANCED: Cap maximum velocity (now higher for more dramatic slides)
        if (speed > this.maxSpeed) {
            const scale = this.maxSpeed / speed;
            vx *= scale;
            vy *= scale;
        }
        
        this.activeSlides.set(obj.id, {
            obj: obj,
            vx: vx,
            vy: vy,
            startSpeed: Math.sqrt(vx * vx + vy * vy),
            chainCount: 0, // Track how many objects this has hit (for chain reaction tracking)
            // ENHANCED: Track slide coordinates for debugging
            releasePosition: { x: obj.x, y: obj.y }, // Where drag ended
            releaseTime: Date.now(),
            gridReleasePos: obj.x !== undefined ? this.editor.worldToGrid({ x: obj.x, y: obj.y }) : null
        });
        
        if (this.editor.debugger) {
            const gridPos = obj.x !== undefined ? this.editor.worldToGrid({ x: obj.x, y: obj.y }) : null;
            this.editor.debugger.logAction(`🎯 Slide started: ${obj.label || 'Object'} @ speed ${Math.round(speed)}px/f`);
            this.editor.debugger.logInfo(`Velocity: (${vx.toFixed(1)}, ${vy.toFixed(1)}) | Multiplier: ${this.velocityMultiplier}x`);
            this.editor.debugger.logInfo(`📍 Release Position: World (${obj.x.toFixed(1)}, ${obj.y.toFixed(1)}) | Grid (${gridPos ? gridPos.x.toFixed(0) + ', ' + gridPos.y.toFixed(0) : 'N/A'})`);
        }
        
        // Start animation loop if not already running
        if (!this.animationFrame) {
            this.chainReactions = 0; // Reset chain reaction counter
            this.animate();
        }
    }

    // Animation loop with BILLIARD BALL PHYSICS (Python billiards library compatible)
    animate() {
        if (this.activeSlides.size === 0) {
            this.animationFrame = null;
            if (this.chainReactions > 0 && this.editor.debugger) {
                this.editor.debugger.logSuccess(`⛓️ Billiard chain complete: ${this.chainReactions} elastic collisions`);
            }
            return;
        }
        
        const toRemove = [];
        const newSlides = []; // Track new objects that should start sliding (chain reaction)
        this.collisionThisFrame.clear(); // Reset collision tracking for this frame
        
        this.activeSlides.forEach((slide, id) => {
            const obj = slide.obj;
            
            // Skip deleted objects or locked objects when movable devices are OFF
            if ((obj.locked && !this.editor.movableDevices) || !this.editor.objects.includes(obj)) {
                toRemove.push(id);
                return;
            }
            
            // Apply velocity
            let newX = obj.x + slide.vx;
            let newY = obj.y + slide.vy;
            
            // BILLIARD BALL PHYSICS (Python billiards library compatible - elastic collisions)
            // CRITICAL: Only apply billiard physics when collision detection is ENABLED
            if (this.chainCollisionEnabled && this.editor.deviceCollision && obj.type === 'device') {
                const allDevices = this.editor.objects.filter(o => o.type === 'device' && o.id !== obj.id);
                
                allDevices.forEach(otherDevice => {
                    // Skip locked devices only when movable devices are OFF
                    if (otherDevice.locked && !this.editor.movableDevices) return;
                    
                    // Skip if we already processed this collision pair this frame
                    const pairKey = [obj.id, otherDevice.id].sort().join('-');
                    if (this.collisionThisFrame.has(pairKey)) return;
                    
                    // Calculate distance between centers
                    const dx = newX - otherDevice.x;
                    const dy = newY - otherDevice.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    
                    // SHAPE-ACCURATE COLLISION: Calculate angle and get direction-aware radii
                    const angle = Math.atan2(dy, dx);
                    const objRadius = this.editor.getDeviceCollisionRadiusInDirection 
                        ? this.editor.getDeviceCollisionRadiusInDirection(obj, angle) 
                        : (this.editor.getDeviceCollisionRadius ? this.editor.getDeviceCollisionRadius(obj) : obj.radius);
                    const otherRadius = this.editor.getDeviceCollisionRadiusInDirection 
                        ? this.editor.getDeviceCollisionRadiusInDirection(otherDevice, angle + Math.PI) 
                        : (this.editor.getDeviceCollisionRadius ? this.editor.getDeviceCollisionRadius(otherDevice) : otherDevice.radius);
                    const minDist = objRadius + otherRadius + 1;  // Minimal gap - shape-accurate
                    
                    if (dist < minDist && dist > 0.01) {
                        // ELASTIC COLLISION DETECTED! (Billiard ball physics)
                        this.collisionThisFrame.add(pairKey);
                        
                        // Collision normal (unit vector from obj to otherDevice)
                        const nx = dx / dist;
                        const ny = dy / dist;
                        
                        // Tangent vector (perpendicular to normal)
                        const tx = -ny;
                        const ty = nx;
                        
                        // Get velocities for both objects
                        const v1x = slide.vx;
                        const v1y = slide.vy;
                        const otherSlide = this.activeSlides.get(otherDevice.id);
                        const v2x = otherSlide ? otherSlide.vx : 0;
                        const v2y = otherSlide ? otherSlide.vy : 0;
                        
                        // Decompose velocities into normal and tangential components
                        const v1n = v1x * nx + v1y * ny; // Velocity of obj along normal
                        const v1t = v1x * tx + v1y * ty; // Velocity of obj along tangent
                        const v2n = v2x * nx + v2y * ny; // Velocity of other along normal
                        const v2t = v2x * tx + v2y * ty; // Velocity of other along tangent
                        
                        // Only process if approaching each other
                        if (v1n - v2n <= 0) return;
                        
                        // Get masses (billiard balls have equal mass, but we support different sizes)
                        // Calculate mass based on area (π × r²)
                        const calculateMass = (device) => {
                            const radius = device.radius || 30;
                            return Math.PI * radius * radius;
                        };
                        const m1 = calculateMass(obj);
                        const m2 = calculateMass(otherDevice);
                        
                        // ELASTIC COLLISION FORMULA (Conservation of momentum and energy)
                        // New normal velocities after elastic collision
                        const v1n_new = ((m1 - m2) * v1n + 2 * m2 * v2n) / (m1 + m2);
                        const v2n_new = ((m2 - m1) * v2n + 2 * m1 * v1n) / (m1 + m2);
                        
                        // ENHANCED: Apply restitution and collision boost for dramatic bumps
                        const v1n_final = v1n_new * this.restitution * this.collisionBoost;
                        const v2n_final = v2n_new * this.restitution * this.collisionBoost;
                        
                        // Tangential velocities remain unchanged (no spin in 2D top-down)
                        // Reconstruct total velocities from components
                        const v1x_new = v1n_final * nx + v1t * tx;
                        const v1y_new = v1n_final * ny + v1t * ty;
                        const v2x_new = v2n_final * nx + v2t * tx;
                        const v2y_new = v2n_final * ny + v2t * ty;
                        
                        // Update first object's velocity
                        slide.vx = v1x_new;
                        slide.vy = v1y_new;
                        
                        // Update or create second object's velocity
                        if (otherSlide) {
                            // Object already sliding - update velocity
                            otherSlide.vx = v2x_new;
                            otherSlide.vy = v2y_new;
                        } else {
                            // Object was stationary - check if it should start sliding (chain reaction!)
                            const newSpeed = Math.sqrt(v2x_new * v2x_new + v2y_new * v2y_new);
                            if (newSpeed > this.minVelocity) {
                                newSlides.push({
                                    obj: otherDevice,
                                    vx: v2x_new,
                                    vy: v2y_new,
                                    startSpeed: newSpeed,
                                    chainCount: slide.chainCount + 1
                                });
                                
                                this.chainReactions++;
                                
                                if (this.editor.debugger) {
                                    this.editor.debugger.logAction(`⛓️ Billiard hit ${slide.chainCount + 1}: ${obj.label || 'Device'} → ${otherDevice.label || 'Device'} (${Math.round(newSpeed)}px/f)`);
                                }
                            }
                        }
                        
                        // Separate overlapping objects (push apart along normal)
                        const overlap = minDist - dist;
                        const separation = overlap / 2;
                        newX += nx * separation;
                        newY += ny * separation;
                        otherDevice.x -= nx * separation;
                        otherDevice.y -= ny * separation;
                    }
                });
            }
            
            // Also check collision with static obstacles (walls)
            if (this.editor.deviceCollision && obj.type === 'device') {
                const proposedPos = this.editor.checkDeviceCollision(obj, newX, newY);
                
                // If collision with static obstacle, bounce
                if (Math.abs(proposedPos.x - newX) > 1 || Math.abs(proposedPos.y - newY) > 1) {
                    newX = proposedPos.x;
                    newY = proposedPos.y;
                    slide.vx *= -0.4; // Reverse and dampen (bounce)
                    slide.vy *= -0.4;
                    
                    if (this.editor.debugger && !slide._bounceLogged) {
                        slide._bounceLogged = true;
                        this.editor.debugger.logInfo(`💥 Wall bounce: ${obj.label || 'Device'}`);
                    }
                }
            }
            
            // Apply position
            const oldX = obj.x;
            const oldY = obj.y;
            obj.x = newX;
            obj.y = newY;
            
            // Apply movable device chain reaction during momentum sliding
            if (this.editor.movableDevices && obj.type === 'device') {
                const velocityX = newX - oldX;
                const velocityY = newY - oldY;
                this.editor.applyDeviceChainReaction(obj, velocityX, velocityY);
            }
            
            // BILLIARD PHYSICS: Apply rolling friction (realistic table friction)
            // This simulates the felt surface resistance
            let currentSpeed = Math.sqrt(slide.vx * slide.vx + slide.vy * slide.vy);
            if (currentSpeed > 0.01) {
                // Rolling friction opposes motion direction
                const frictionForce = this.rollingFriction * currentSpeed;
                const vx_friction = -(slide.vx / currentSpeed) * frictionForce;
                const vy_friction = -(slide.vy / currentSpeed) * frictionForce;
                
                slide.vx += vx_friction;
                slide.vy += vy_friction;
            }
            
            // Apply additional air resistance / table friction (velocity-based)
            slide.vx *= this.friction;
            slide.vy *= this.friction;
            
            // Recalculate speed after all friction applied
            currentSpeed = Math.sqrt(slide.vx * slide.vx + slide.vy * slide.vy);
            if (currentSpeed < this.minVelocity) {
                toRemove.push(id);
                
                // ENHANCED: Calculate and log complete slide journey
                if (this.editor.debugger) {
                    const finalPos = { x: obj.x, y: obj.y };
                    const gridFinalPos = obj.x !== undefined ? this.editor.worldToGrid(finalPos) : null;
                    const releasePos = slide.releasePosition;
                    const gridReleasePos = slide.gridReleasePos;
                    
                    // Calculate distance traveled
                    const dx = finalPos.x - releasePos.x;
                    const dy = finalPos.y - releasePos.y;
                    const distanceTraveled = Math.sqrt(dx * dx + dy * dy);
                    const slideDuration = Date.now() - slide.releaseTime;
                    
                    const chainInfo = slide.chainCount > 0 ? ` (chain depth: ${slide.chainCount})` : '';
                    this.editor.debugger.logSuccess(`✓ Slide stopped: ${obj.label || 'Object'}${chainInfo}`);
                    this.editor.debugger.logInfo(`📊 Slide Journey:`);
                    this.editor.debugger.logInfo(`   Release: World (${releasePos.x.toFixed(1)}, ${releasePos.y.toFixed(1)}) | Grid (${gridReleasePos ? gridReleasePos.x.toFixed(0) + ', ' + gridReleasePos.y.toFixed(0) : 'N/A'})`);
                    this.editor.debugger.logInfo(`   Stopped: World (${finalPos.x.toFixed(1)}, ${finalPos.y.toFixed(1)}) | Grid (${gridFinalPos ? gridFinalPos.x.toFixed(0) + ', ' + gridFinalPos.y.toFixed(0) : 'N/A'})`);
                    this.editor.debugger.logInfo(`   Distance: ${distanceTraveled.toFixed(1)}px | Duration: ${slideDuration}ms | Avg Speed: ${(distanceTraveled / slideDuration * 1000).toFixed(1)}px/s`);
                    this.editor.debugger.logInfo(`   Delta: (${dx > 0 ? '+' : ''}${dx.toFixed(1)}, ${dy > 0 ? '+' : ''}${dy.toFixed(1)})`);
                }
                
                // Save final position
                this.editor.saveState();
            }
        });
        
        // Add new chain reaction slides
        newSlides.forEach(newSlide => {
            this.activeSlides.set(newSlide.obj.id, newSlide);
        });
        
        // Remove stopped objects
        toRemove.forEach(id => this.activeSlides.delete(id));
        
        // Redraw
        if (this.activeSlides.size > 0) {
            this.editor.draw();
            this.animationFrame = requestAnimationFrame(() => this.animate());
        } else {
            this.animationFrame = null;
        }
    }

    // Stop all slides
    stopAll() {
        this.activeSlides.clear();
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
        
        // Reduced logging: Don't log every momentum stop (too frequent)
        // Uncomment if debugging momentum issues:
        // if (this.editor.debugger) {
        //     this.editor.debugger.logInfo('⏹️ All slides stopped');
        // }
    }

    // Reset velocity tracking (call on mouse down)
    reset() {
        this.velocityHistory = [];
    }

    // Toggle momentum on/off
    toggle() {
        this.enabled = !this.enabled;
        localStorage.setItem('momentum_enabled', this.enabled);
        
        if (!this.enabled) {
            this.stopAll();
        }
        
        if (this.editor.debugger) {
            if (this.enabled) {
                this.editor.debugger.logSuccess('🎯 Momentum/Sliding ENABLED');
                this.editor.debugger.logInfo('Code: topology-momentum.js');
            } else {
                this.editor.debugger.logInfo('🎯 Momentum/Sliding DISABLED');
            }
        }
        
        return this.enabled;
    }
}

// Make momentum engine available globally
window.createMomentumEngine = function(editor) {
    return new MomentumEngine(editor);
};

