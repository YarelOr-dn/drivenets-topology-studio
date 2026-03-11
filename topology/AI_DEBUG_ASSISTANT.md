# 🤖 AI Debug Assistant - User Guide

## Overview

Your topology editor now has an **intelligent AI debugging system** that seamlessly integrates with Cursor AI to help you fix bugs faster and more effectively!

## ✨ Features

### 1. **Smart Bug Detection & Context Capture**
- Automatically captures comprehensive bug context when errors occur
- Includes editor state, recent actions, execution flow, and root cause analysis
- Tracks bug patterns and recurring issues

### 2. **One-Click AI Assistance**
- **"Ask AI" button** appears on every bug alert
- Instantly copies formatted bug report to clipboard
- Ready to paste into Cursor AI chat (Cmd+L / Ctrl+L)

### 3. **AI Debug Panel**
- Shows what context was captured
- Provides step-by-step instructions
- "Copy Again" button for re-copying context

### 4. **Fix Tracking System**
- Track which bugs you've fixed with AI help
- View statistics: total bugs, fixes applied, fix rate
- See bug categories and patterns
- Monitor recent debugging sessions

### 5. **AI Debug History Dashboard**
- Persistent history saved in localStorage
- Visual indicators for fixed vs pending bugs
- Quick access to mark fixes as applied
- Category breakdown of bug types

## 🚀 How to Use

### When a Bug Occurs:

1. **Bug Alert Appears** 🚨
   - The debugger automatically opens and shows bug details
   - Root cause analysis is generated automatically

2. **Click "🤖 Ask AI" Button**
   - Comprehensive bug context is captured
   - Formatted report is copied to clipboard
   - AI Debug Panel opens with instructions

3. **Open Cursor AI Chat**
   - Press `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux)
   - Paste the bug context (`Cmd+V` / `Ctrl+V`)

4. **Get AI Analysis**
   - AI analyzes the bug with full context
   - Provides root cause verification
   - Suggests exact code fixes
   - Explains prevention strategies

5. **Apply the Fix**
   - Review the suggested changes
   - Apply fixes directly through Cursor
   - Mark fix as applied in debugger

6. **Track Your Progress**
   - View AI Debug History section
   - Click "✅ Mark Latest Fix Applied"
   - Enter brief description of what was fixed
   - See your fix rate improve over time!

## 📊 What Context Gets Captured

The AI receives a comprehensive bug report including:

### Bug Information
- Bug message and timestamp
- Auto-generated root cause analysis
- Code conflicts detected
- Execution flow trace

### Editor State
- Zoom level and pan position
- Current mode (base/link/text)
- Dragging/placing status
- Object counts (devices, links, texts)
- Physics settings (collision, weight, momentum)
- Input type (mouse, touchpad, touch)

### Recent Activity
- Last 10 user actions leading to bug
- Last 15 debug log entries
- Complete state snapshot at bug time

### Environment Info
- Browser platform and user agent
- Screen and window dimensions
- Stack trace

## 🎯 AI Debug History Section

Located at the top of the debugger panel:

### Statistics Panel
- **Total Bugs Analyzed**: Count of all bugs sent to AI
- **Fixes Applied**: Number of successfully resolved bugs
- **Fix Rate**: Percentage of bugs you've fixed (color-coded)

### Bug Categories
- Breakdown by bug type (POSITION_JUMP, STATE_SYNC, etc.)
- Shows which types of bugs are most common

### Recent Sessions
- Shows last 5 debugging sessions
- Green indicator = Fixed ✅
- Orange indicator = Pending ⏳
- Click through to see details

### Quick Actions
- "✅ Mark Latest Fix Applied" button when you have pending fixes
- Enter description to track what you changed

## 💡 Tips for Best Results

1. **Use Immediately**: Click "Ask AI" right when the bug occurs for freshest context

2. **Be Specific When Marking Fixes**: When marking a fix as applied, describe what you changed (e.g., "Fixed coordinate transform in getMousePos()")

3. **Review Patterns**: Check AI Debug History to see if certain bug categories recur

4. **Share Context**: The copied text is comprehensive - AI can identify exact files and lines to fix

5. **Learn from Fixes**: Review the AI Debug History to understand common issues in your codebase

## 🔧 Technical Details

### Files Modified
- `debugger.js`: Added AI Debug Assistant system
  - `askAI()`: Main entry point
  - `captureBugContext()`: Gathers comprehensive state
  - `copyBugContextForAI()`: Formats for AI analysis
  - `markFixApplied()`: Tracks successful fixes
  - `getAIDebugStats()`: Calculates statistics

### Data Storage
- AI debug history saved in `localStorage` as `ai_debug_history`
- Persists across browser sessions
- Automatically loaded on debugger initialization
- Limited to last 20 sessions to prevent bloat

### UI Components
- **Bug Alert**: Enhanced with "Ask AI" button
- **AI Debug Panel**: Shows captured context summary
- **AI Debug History Section**: Collapsible section in main debugger
- **Mark Fix Button**: Appears when pending fixes exist

## 🎨 Visual Design

- **Purple/Blue Gradient**: AI-related components (`#667eea` → `#764ba2`)
- **Hover Effects**: Buttons scale up and glow on hover
- **Color Coding**:
  - Green (`#0f0`): Fixed bugs, good stats
  - Orange (`#fa0`): Pending bugs, medium stats
  - Red (`#f00`): Critical bugs, low fix rates
  - Purple (`#667eea`): AI-specific features

## 🚦 How This Works Behind the Scenes

```
1. Bug Occurs
   ↓
2. Debugger.logError() triggered
   ↓
3. analyzeBug() generates root cause
   ↓
4. showBugAlert() displays bug with "Ask AI" button
   ↓
5. User clicks "Ask AI"
   ↓
6. captureBugContext() gathers all state
   ↓
7. copyBugContextForAI() formats and copies
   ↓
8. User pastes into Cursor AI chat
   ↓
9. AI analyzes and provides fix
   ↓
10. User applies fix and marks complete
    ↓
11. markFixApplied() updates history
    ↓
12. Statistics update in AI Debug History
```

## 🎉 Benefits

1. **Faster Debugging**: Context is automatically captured - no manual gathering
2. **Better Fixes**: AI gets complete picture, not just error message
3. **Learning**: Track your debugging patterns and improvement
4. **Consistency**: Same comprehensive context every time
5. **Efficiency**: One-click workflow from bug to AI assistance

## 🔮 Future Enhancements (Ideas)

- Export debug sessions to file
- Pattern recognition for recurring bugs
- Automatic fix suggestions without leaving the app
- Integration with GitHub Issues
- Team sharing of common bug patterns
- AI-suggested preventive measures

## 📝 Example AI Prompt (What Gets Copied)

```
🐛 BUG DETECTED IN TOPOLOGY EDITOR - AI ANALYSIS REQUEST

═══════════════════════════════════════════════════════════
📋 BUG SUMMARY
═══════════════════════════════════════════════════════════
Timestamp: 10/31/2025, 2:30:45 PM
Category: POSITION_JUMP
Bug Message: Device jumped during drag

═══════════════════════════════════════════════════════════
🔍 ROOT CAUSE ANALYSIS (Auto-Generated)
═══════════════════════════════════════════════════════════
COORDINATE TRANSFORM FAILURE

WHY: getMousePos() returned incorrect world coordinates
WHAT: Mouse position should be near device
RESULT: Offset calculated incorrectly

... (and much more detailed context)
```

## 🆘 Troubleshooting

**Q: "Ask AI" button doesn't appear**
- Make sure a bug alert is showing (red box at top of debugger)
- Ensure debugger is not minimized

**Q: Context not copying to clipboard**
- Check browser permissions for clipboard access
- Try the "Copy Again" button in AI panel
- Fallback method will trigger automatically

**Q: AI Debug History not showing**
- History section may be collapsed - click to expand
- No sessions yet? Click "Ask AI" on a bug to start

**Q: Fix tracking not persisting**
- Check browser localStorage isn't disabled
- Clear and re-mark if needed

---

**Happy Debugging! 🤖✨**

The AI is now your debugging partner - use it whenever bugs appear!

