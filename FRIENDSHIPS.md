# Friendship experiment - Team Char Siu

Run: python main.py "A rumour about the subject"
Tests: python -m unittest discover -s tests -v

This supersedes older README/notes descriptions of avoidance and interest. Original inspiration:
Le Nguyen, README reference 1. These social rules and parameter distributions are experimental assumptions.

Up to 12 friends are selected across all groups/no-group agents; four start nearby and linger. Groups
are unchanged. Pink centres denote current friendship, not belief; red/green outlines show activity.
Friends can spread. On first accepting the rumour, a friend breaks away with probability 1-loyalty.
Nonfriends have a persistent 75% avoidance choice; broken friendships always avoid. Correction clears
belief/avoidance, not friendship loss. Openness and loyalty are independent uniform [0,1] traits.
Sharing tendency reuses interest; conditional sharing chance is .5 + .5*sharingTendency by default.
Nonsharing believers are silent, not sceptics. Failed acceptance is not separately logged as hearing.
Correction uses openness instead of inverse gullibility; inactive believers can accept correction too.
A small corrector population is an aim, not guaranteed. Timers remain 50 steps; belief survives expiry.

Order: notice -> subject moves -> others move -> timers -> snapshot spread -> correction seeds -> counts.
The subject noticing repeated nearby avoiders creates correction awareness without inventing a teller.
Avoiders reject disk-crossing steps and detour tangentially. Overlaps are evacuated to the boundary:
this is a positional correction, not speed-limited physics or continuous-time collision avoidance.
Lingering friends use a subject-centred radius instead of their group leash. Display easing is constrained.
The original viewer_arcade.py remains; viewer_friendships.py adds the overlay. main.py is import-safe,
uses argparse, checks n/steps/seed and reports missing initial candidates. Full parameter validation remains.

18 tests passed in the regeneration sandbox, including 1500 random geometry cases. A 500-agent, 400-step
smoke run conserved population. No live Arcade window was opened. These are not benchmark findings.
Global RNG and dense distance matrix remain. Parallel implementation/equivalence/benchmarks are outstanding.
