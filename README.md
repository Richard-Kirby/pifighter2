# Pifighter2 - Heavy Bag Sparring Game/Work out tool

## Introduction
Pi Fighter provides a video game like experience to martial arts or boxing workouts.  Pi Fighter would normally be attached to a free standing heavy bag, but could be adapted to hung heavy bags or workout pads.  

Pi Fighter provides 2 modes:
1. Workout mode - player is presented with an attack to perform, one of left punch, left kick, right punch, right kick.
2. Fight mode - player chooses an opponent to spar with.  Pi Fighter measures its acceleration and uses that acceleration as your attack 
against an imaginary opponent. The imaginary opponent fights back according to a stored file.   

Players start with a baseline number of health points, which builds as they win sparring matches.  

## Client Side
The Pi Fighter Client must run on the Pi attached to the heavy bag or pad.  It manages the display of the matches and measures the acceleration via a MPU-6050.  
The client only provides the interface for the sparring match.  The match itself is managed by the Server, which can run on the same Pi, but does not need to.  
## Server Side
The Pi Fighter Server normally runs on the same Pi.  More work is needed to move it to another computer such as a laptop or a server running windows.
