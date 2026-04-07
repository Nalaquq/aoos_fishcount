# Lens Focus Workflow

Focus the 8mm CS-mount lens before sealing the Pelican 1120 camera head.
Once sealed and mounted at 12 feet, re-focusing requires full disassembly.

## Tools Required
- Laptop with SSH to RPi
- Focus target at exactly 12 feet (ruler, newspaper, or focus chart)
- Small flat screwdriver (focus ring lock screw)
- Loctite 243 (blue, medium-strength)
- Paint pen

## Steps

1. Set up the camera aimed at a high-contrast target exactly 12 feet away.
2. SSH into the RPi and run: `python scripts/focus_check.py`
3. Watch the sharpness number. Rotate the lens focus ring slowly.
4. Find the peak sharpness value — this is optimal focus.
5. Back off slightly in both directions to confirm the peak.
6. Tighten the focus ring lock set screw firmly with a screwdriver.
7. Apply one drop of Loctite 243 to the lock screw threads.
8. Draw a paint pen line across the focus ring / barrel junction.
9. After mounting at the site, run `python scripts/focus_check.py` again.
   Sharpness should be within 20% of your bench peak. If not, re-focus.

## Expected Sharpness Values

Typical values at 12 feet with the 8mm F/1.2 CS-mount lens:
- **Good:** 600–1000
- **Excellent:** 1000+
- **Poor (re-focus needed):** < 400
