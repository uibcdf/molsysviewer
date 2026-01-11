 (User_Intro_Molstar)=
 # Mol\*
 
 MolSysViewer relies on a third-party project for the actual 3D rendering in the browser: [Mol\* (MolStar)](https://molstar.org/).
 
 Mol\* is not part of MolSysSuite, and we are not the authors of Mol\*. We chose to build on it because it is a powerful, modern molecular viewer, and we are genuinely grateful to the Mol\* developers for making it available to the community.
 
 In practice, this is the division of responsibilities:
 
 - **Python side (your notebook):** you interact with MolSysViewer and MolSysMT to load molecular data and decide what you want to see.
 - **Browser side (the viewer):** Mol\* draws the scene and handles interactive graphics.
 
 You do not need to learn Mol\* internals to use MolSysViewer productively, but it helps to know that Mol\* is the engine that makes the visualization possible.
