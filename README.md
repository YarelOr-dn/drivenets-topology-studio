# Network Topology Creator

A browser-based network topology editor similar to GNS3, focused on topology creation and design without VM or terminal functionality.

## Features

✅ **Device Management**
- Add routers and switches with visual icons
- Drag and drop devices anywhere on the canvas
- Color customization for devices
- Select and move devices

✅ **Link Creation**
- Connect devices with links
- Visual connection points
- Bidirectional links with arrowheads
- Link color customization

✅ **Text Labels**
- Add text labels anywhere
- Adjustable font size (8-72px)
- 360° rotation capability
- Color customization
- Double-click to edit text content

✅ **Canvas Controls**
- Pan canvas (Space + Drag or Middle Mouse + Drag)
- Zoom in/out (mouse wheel - zooms towards cursor)
- Horizontal pan (Shift + Mouse Wheel)
- Grid background for alignment
- Selection highlighting
- Delete selected objects (Delete/Backspace key)

✅ **Save/Load**
- Save topologies as JSON files
- Load previously saved topologies
- Preserves all device positions, links, and text

## Usage

### Getting Started

1. Open `index.html` in a modern web browser (Chrome, Firefox, Safari, or Edge)
2. No installation or server required - works directly from the file system

### Adding Devices

1. Click **Router** or **Switch** button in the toolbar
2. Device will be placed at canvas center
3. Drag to reposition

### Creating Links

1. Click **Link** tool in the toolbar
2. Click on the first device
3. Click on the second device to create the connection
4. Links automatically update when devices are moved

### Adding Text

1. Click **Text** tool
2. Click anywhere on canvas to place text
3. Double-click text to edit content
4. Adjust font size and rotation using the properties panel

### Customizing Colors

1. Select an object (device, link, or text)
2. Use the color picker in the Properties section
3. Color updates immediately

### Selecting Objects

- Click on any object to select it
- Selected objects show a blue highlight
- Use Select tool for normal selection mode

### Deleting Objects

- Select an object and click **Delete** button
- Or press `Delete` or `Backspace` key when object is selected
- Deleting a device also removes all connected links

### Saving Topology

1. Click **Save** button
2. File will download as `topology_[timestamp].json`
3. Save to your preferred location

### Loading Topology

1. Click **Load** button
2. Select a previously saved JSON file
3. Topology will be restored with all objects

## Keyboard Shortcuts

- `Delete` / `Backspace`: Delete selected object
- `Space` + Drag: Pan the canvas
- Mouse Wheel: Zoom in/out (zooms towards mouse cursor)
- `Shift` + Mouse Wheel: Pan horizontally
- Middle Mouse + Drag: Pan the canvas
- Click + Drag: Move selected object

## File Format

Topologies are saved as JSON with the following structure:

```json
{
  "version": "1.0",
  "objects": [
    {
      "id": "device_0",
      "type": "device",
      "deviceType": "router",
      "x": 100,
      "y": 100,
      "radius": 30,
      "color": "#4CAF50"
    },
    {
      "id": "link_0",
      "type": "link",
      "device1": "device_0",
      "device2": "device_1",
      "color": "#666"
    },
    {
      "id": "text_0",
      "type": "text",
      "x": 200,
      "y": 200,
      "text": "Network A",
      "fontSize": "14",
      "color": "#000000",
      "rotation": 0
    }
  ],
  "metadata": {
    "deviceIdCounter": 2,
    "linkIdCounter": 1,
    "textIdCounter": 1
  }
}
```

## Browser Compatibility

- Chrome/Edge (recommended)
- Firefox
- Safari
- Any modern browser with HTML5 Canvas support

## Tips

- Use the grid background to align devices
- Zoom out to see the bigger picture of your topology
- Text rotation works in 360° increments
- Links automatically adjust when devices are moved
- Save frequently to avoid losing your work

## Limitations

- No VM/terminal integration (by design - topology only)
- No device configuration interface
- Canvas works best with mouse (touch supported but less precise)
- Maximum zoom: 2x, Minimum zoom: 0.5x

