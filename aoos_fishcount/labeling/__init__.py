"""
Labeling tool for salmon species bounding box annotation.

Provides a Flask-based web UI for annotating images with bounding boxes
around salmon species (king, red, silver, chum, pink) to generate YOLO
training data.

Usage:
    aoos-label --input /path/to/images --output /path/to/labels
"""

SPECIES_CLASSES = {
    0: "king",
    1: "red",
    2: "silver",
    3: "chum",
    4: "pink",
}

SPECIES_COLORS = {
    0: "#e6194b",  # king — red
    1: "#3cb44b",  # red (sockeye) — green
    2: "#4363d8",  # silver (coho) — blue
    3: "#f58231",  # chum — orange
    4: "#f032e6",  # pink — magenta
}
