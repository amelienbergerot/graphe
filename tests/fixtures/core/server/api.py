def route_zones(path):
    # Answers the front's zones (T-0001).
    if path == "/api/zones":
        return say("Zones listed")
    return {"status": "closed"}


def say(text):
    return text
