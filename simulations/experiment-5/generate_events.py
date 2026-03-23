#!/usr/bin/env python3
import json

# Configuration
outage_durations_min = [15, 30, 60]
total_simulation_time_ms = 20000000 


LINK_UPLINK = "DSNUplink->MarsOrbiterUplink"
LINK_DOWNLINK = "MarsOrbiterDownlink->DSNDownlink"

def generate_events():
    for outage_min in outage_durations_min:
        outage_ms = outage_min * 60 * 1000
        uptime_ms = outage_ms * 2  # Uptime = 2/3 of the time

        events = []

        # Start with links UP at t=0
        events.append({"relative_time_ms": 0, "link": {"id": LINK_UPLINK, "status": "up"}})
        events.append({"relative_time_ms": 0, "link": {"id": LINK_DOWNLINK, "status": "up"}})

        current_time_ms = uptime_ms

        # Loop until we exceed the total simulation boundary
        while current_time_ms < total_simulation_time_ms:
            # Link goes DOWN
            events.append({"relative_time_ms": current_time_ms, "link": {"id": LINK_UPLINK, "status": "down"}})
            events.append({"relative_time_ms": current_time_ms, "link": {"id": LINK_DOWNLINK, "status": "down"}})
            
            current_time_ms += outage_ms
            
            # Link comes back UP
            events.append({"relative_time_ms": current_time_ms, "link": {"id": LINK_UPLINK, "status": "up"}})
            events.append({"relative_time_ms": current_time_ms, "link": {"id": LINK_DOWNLINK, "status": "up"}})
            
            current_time_ms += uptime_ms

        payload = {
            "type": "NetworkEvents",
            "events": events
        }

        # Filename matches what your bash runner script expects
        filename = f"events-{outage_min}.json"
        
        with open(filename, "w") as f:
            json.dump(payload, f, indent=2)
            
        print(f"Generated {filename}")

if __name__ == "__main__":
    generate_events()