def heuristic_scene(bands, rt60):
    rt = rt60 if rt60 is not None else 0.0
    low = bands.get("120_250", -99)
    mid = (bands.get("250_500", -99) + bands.get("500_1000", -99)) / 2
    hi = (bands.get("2000_4000", -99) + bands.get("4000_8000", -99)) / 2
    if rt > 0.8:
        return "large_room_hall"
    if (mid - hi) > 5 and rt > 0.3:
        return "indoor_hvac_or_room"
    if (hi - mid) > 6 and rt < 0.25:
        return "outdoor_birds_wind"
    if (low > -30 and mid > -28) and rt > 0.4:
        return "indoor_crowd"
    if rt < 0.15:
        return "outdoor_open"
    return "unknown"
