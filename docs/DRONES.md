# Drone Management Documentation

## Overview

The Sanderling parser now supports full drone state tracking, allowing bots to monitor and manage drones effectively.

## Available Information

### DronesState

The `DronesState` object provides:

- `drones_in_space: List[Drone]` - List of drones currently deployed
- `drones_in_bay: List[Drone]` - List of drones in the drone bay
- `in_space_count: int` - Number of drones in space
- `max_drones: int` - Maximum drone capacity (usually 5)
- `window_open: bool` - Whether the drone window is open

### Drone

Each `Drone` object contains:

- `name: str` - Drone name (e.g., "Caldari Navy Hornet")
- `state: str` - Current state: "Idle", "Fighting", or "Returning"
- `shield: float` - Shield health (0.0-1.0)
- `armor: float` - Armor health (0.0-1.0)
- `hull: float` - Hull health (0.0-1.0)
- `center: Tuple[int, int]` - Absolute coordinates for clicking
- `bounds: Tuple[int, int, int, int]` - Bounding box (x, y, width, height)

## Usage Examples

### 1. Check if Drones are Deployed

```python
state = sanderling.get_state()

if state.drones:
    if state.drones.in_space_count > 0:
        print(f"Drones deployed: {state.drones.in_space_count}/{state.drones.max_drones}")
    else:
        print("No drones in space")
```

### 2. Launch Drones

```python
from eve.keyboard import press_key, hold_key, release_key
import time

# Launch all drones (Shift+F)
hold_key('shift')
time.sleep(0.05)
press_key('f')
time.sleep(0.05)
release_key('shift')
```

### 3. Attack with Drones

```python
# Attack current target with drones (F)
press_key('f')
```

### 4. Check Drone Health

```python
state = sanderling.get_state()

if state.drones and state.drones.drones_in_space:
    for drone in state.drones.drones_in_space:
        avg_health = (drone.shield + drone.armor + drone.hull) / 3.0
        
        if avg_health < 0.5:
            print(f"WARNING: {drone.name} is damaged ({avg_health*100:.1f}% HP)")
```

### 5. Check Drone State

```python
state = sanderling.get_state()

if state.drones and state.drones.drones_in_space:
    for drone in state.drones.drones_in_space:
        if drone.state == "Idle":
            print(f"{drone.name} is idle")
        elif drone.state == "Fighting":
            print(f"{drone.name} is fighting")
        elif drone.state == "Returning":
            print(f"{drone.name} is returning to bay")
```

## Drone States

The parser recognizes three drone states:

1. **Idle** (Бездействует) - Drone is in space but not engaged
2. **Fighting** (Сражается) - Drone is actively attacking a target
3. **Returning** (Возвращается) - Drone is returning to the drone bay

## Health Calculation

Drone health is calculated from the gauge widths:
- Maximum width: 32 pixels = 100% health
- Actual width / 32 = health percentage

Each drone has three health bars:
- **Shield** (shieldGauge) - Blue bar
- **Armor** (armorGauge) - Orange bar  
- **Hull** (structGauge) - Red bar

## Integration with Combat

### Abyss Farming Example

```python
def clear_room_with_drones(sanderling):
    """Clear an Abyss room using drones."""
    
    # 1. Launch drones
    if not state.drones or state.drones.in_space_count == 0:
        hold_key('shift')
        time.sleep(0.05)
        press_key('f')
        time.sleep(0.05)
        release_key('shift')
        time.sleep(2)
    
    # 2. Attack enemies
    while enemies_exist():
        # Lock target
        lock_target()
        
        # Attack with drones
        press_key('f')
        
        # Wait for kill
        wait_for_target_death()
        
        # Check drone health
        state = sanderling.get_state()
        if state.drones:
            for drone in state.drones.drones_in_space:
                avg_health = (drone.shield + drone.armor + drone.hull) / 3.0
                if avg_health < 0.3:
                    logger.warning(f"Drone {drone.name} critically damaged!")
                    # Consider recalling drones
```

## Testing

Run the test script to verify drone parsing:

```bash
python scripts/test_drone_parsing.py
```

This will display:
- Number of drones in space
- Drone names and states
- Health percentages for each drone
- Coordinates for clicking

## Notes

- The drone window must be open for parsing to work
- Drone states are parsed from both the text label and the state sprite
- Health gauges are accurate to within 3% (1 pixel = ~3%)
- Coordinates are absolute screen positions, ready for clicking
- The parser handles both Russian and English state names

## See Also

- `scripts/test_drone_parsing.py` - Test drone parsing
- `scripts/example_drone_usage.py` - Example usage in bot logic
- `core/sanderling/models.py` - Drone data models
- `core/sanderling/parser.py` - Drone parsing implementation
