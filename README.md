# FusionHackathonSamples
These are some of the larger samples programs that I wrote to demonstrate specific concepts and used them during the Fusion 360 Hackathon.

The samples are:

- CorkHoles
  - This is an add-in that adds a new button into the ASSEMBLE panel.  When the command is run it prompts for the selection of bodies.  The command then finds all of the holes in the selected bodies and fills them with an appropriately sized cork part.

- Cutouts
  - This is an add-in that creates cutouts positioned at selected points.  When loaded, this add-in adds a new "Cutout Shapes" command into the CREATE panel of the MODEL workspace.  It lets you select a planar face and any points that lie on that face where it will create the specified shape using the specified size.

- GeometryEval
  - This is an add-in that is intended to help illustrate the concept of a surface's parametric space.  It adds a new command to the INSPECT panel that when selected lets you choose any face and then the option of showing sketch lines drawn along the UV space to illustrate the parametric space of the surface or showing sketch lines drawn to illustrate normals on the surface.  A "Density" setting on the argument specifies the number of lines or normals to draw where they are evenly spaced in parametric space.

- ShowProxy
  -This is an small add-in that is used to visualize what a proxy actually is by displaying the occurrence path that uniquely defines the selected entity.

- TransactionSample
  - A small script that demonstrates the use of the command functionality to combine a series of operations into a single transaction so they can be undone in one undo.
