# hydra

" For every head chopped off, the Hydra would regrow two " - For every noise source eliminated, two more pop up.

This is a software which visualizes error models for two-qubit microwave gates using trapped ions in a static magnetic field gradient.


## 1. Installation 

There are two ways to run the program : execute the python code or run the executable.

   - Executing the python code : Clone the Github repository, in a python environment run "python hydra/hydra.py"

   - Running the executable : The repository is precompiled, and the executable is available for download here : https://www.dropbox.com/s/r78zxuov81bkuqm/hydra_V-1-0.exe?dl=0 
Simply download the zip of the latest version, extract it, and run the executable called "main.exe".


## 2. Miscellaneous

Version history : 

  - 1.0 : First stable release. Plotting heating, decoherence, kerr and offres errors. Can support up to four traces. Can save and load files. 

To do : 
  
  - Complete HELP section
  - Add temperature dependence, ie. imperfect sb cooling
  - Refine off-resonant coupling error model with pulse-shaping.
  - Add amplitude noise error model for CDD gates
  - Add current noise for CCWs
  - Add radial STR and COM vibrational modes
