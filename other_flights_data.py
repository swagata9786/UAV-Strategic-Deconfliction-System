# other_flights_data.py
# Stores simulated drone schedules for the central deconfliction service

other_flights = [
    {
        'id': 'Drone1',
        'waypoints': [
            {'x': 10, 'y': -40, 'z': 0},
            {'x': 50, 'y': -30, 'z': 50},
            {'x': 150, 'y': -9, 'z': 50},
            {'x': 180, 'y': 0, 'z': 0}
        ],
        'T_start': "2025-08-10 10:00:00",
        'T_end':   "2025-08-10 10:04:00"
    },
    {
        'id': 'Drone2',
        'waypoints': [
            {'x': 0, 'y': 10, 'z': 0},
            {'x': 200, 'y': 40, 'z': 50}
        ],
        'T_start': "2025-08-10 10:02:00",
        'T_end':   "2025-08-10 10:06:00"
    },
    {
        'id': 'Drone3',
        'waypoints': [
            {'x': 100, 'y': -20, 'z': 0},
            {'x': 150, 'y': 30, 'z': 40}
        ],
        'T_start': "2025-08-10 09:59:00",
        'T_end':   "2025-08-10 10:03:00"
    }
]
