# Persistent correction and enlarged chart

This update supersedes the shared 50-step timer described in FRIENDSHIPS.md and older notes.
Rumour spreaders still lose interest after 50 steps. Once an agent becomes a corrector, it stays active
for the rest of the run. This is an explicit experimental assumption of sustained correction effort,
not an empirically established behavioural rule. It changes the dynamics and may increase correction reach.
No correctors are injected at the end, and no correction probabilities/contact radii are changed.
If no agent ever becomes a corrector, this does not create one. If one emerges, it will remain active;
multiple correctors are not guaranteed. Accepting a correction still does not restore lost friendships.

The live friendship viewer sets the side panel to 640 pixels and chart height to 180 pixels.
The chart is 600 by 180 pixels, previously 400 by 140. The window is 1340 by 700 pixels.
The run length, timestep speed, x-axis duration and saved plots are unchanged.
The enlarged layout has not been checked in a live Arcade window.

Three focused lifetime regression tests passed in the sandbox. Run the full suite locally:
python -m unittest discover -s tests -v
