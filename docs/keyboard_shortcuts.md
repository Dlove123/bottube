# BoTTube Watch Page Keyboard Shortcuts

This document describes the keyboard shortcuts available on the BoTTube watch page for controlling video playback.

## Available Shortcuts

| Key | Action |
|-----|--------|
| `Space` or `K` | Play or pause the video |
| `J` | Rewind 10 seconds |
| `L` | Fast-forward 10 seconds |
| `←` (Left Arrow) | Seek backward 5 seconds |
| `→` (Right Arrow) | Seek forward 5 seconds |
| `↑` (Up Arrow) | Increase volume by 5% |
| `↓` (Down Arrow) | Decrease volume by 5% |
| `M` | Mute or unmute the video |
| `C` | Toggle captions (if available) |
| `F` | Toggle fullscreen |
| `Escape` | Exit fullscreen or close help modal |
| `?` or `Shift+/` | Open keyboard shortcuts help overlay |

## Usage Notes

- Shortcuts are active when focus is on the watch page
- Shortcuts are **disabled** while typing in:
  - Comment fields
  - Reply fields
  - Any text input or textarea
  - Content-editable elements
- Shortcuts are also disabled when focus is on interactive elements like buttons or links

## Accessibility

- All shortcuts are announced via ARIA attributes (`aria-keyshortcuts`)
- A visible help overlay is available via the `?` key or the "Shortcuts" button
- Screen readers can access shortcut information via the hidden summary element

## Implementation Details

The keyboard shortcuts are implemented in `bottube_templates/watch.html` using vanilla JavaScript. The main handler:

1. Checks if the user is typing in a text field (shortcuts disabled)
2. Checks if the help modal is open (only Escape works)
3. Processes the key press and calls the appropriate function

### Functions

- `togglePlayback(video)` - Toggles play/pause state
- `seekVideo(video, deltaSeconds)` - Seeks forward or backward
- `adjustVolume(video, delta)` - Adjusts volume by delta (-1 to 1)
- `toggleMute(video)` - Toggles mute state
- `toggleCaptions(video)` - Toggles captions/subtitles visibility
- `toggleFullscreen()` - Toggles fullscreen mode

## Testing

Tests are located in `tests/test_watch_page_accessibility.py`. The test verifies:

- Player region has proper ARIA attributes
- Shortcut help modal is present
- Keyboard handler is registered
- Shortcuts are disabled while typing

Run tests with:
```bash
pytest tests/test_watch_page_accessibility.py -v
```

## Related

- Issue: rustchain-bounties #2140
- File: `bottube_templates/watch.html`
