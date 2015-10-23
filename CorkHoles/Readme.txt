(C) Copyright 2015 by Autodesk, Inc.
Permission to use, copy, modify, and distribute this software in object code form for any purpose and without fee is hereby granted, provided that the above copyright notice appears in all copies and that both that copyright notice and the limited warranty and restricted rights notice below appear in all supporting documentation.
    
AUTODESK PROVIDES THIS PROGRAM "AS IS" AND WITH ALL FAULTS. AUTODESK SPECIFICALLY DISCLAIMS ANY IMPLIED WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR USE. AUTODESK, INC. DOES NOT WARRANT THAT THE OPERATION OF THE PROGRAM WILL BE UNINTERRUPTED OR ERROR FREE.
--------------------------------------------------------------------------------------------
Description
This is an add-in that adds a new button into the ASSEMBLE panel.  When the command is run it prompts for the selection of bodies.  The command then finds all of the holes in the selected bodies and fills them with an appropriately sized cork part.
--------------------------------------------------------------------------------------------
Functionality Demonstrated
This sample demonstrates using the B-Rep and geometry portion of the API to evaluate the model and based on the geometry it infers holes.  It does this by looking for circular edges that are interior loops on a face.  It then verfies that the normal of the cylindrical face associated with the edge points towards the axis of the cylinder to determine if the cylinder represents a hole or a boss.

Once the edges have been identified, it uses those to create a matrix that will define the position and orientation of the cork model.  A unique cork component is created for each size of hole.  For holes that are the same size, the component for that size is re-used.  The new component is placed using the matrix computed for the hole and then a joint is created to associate the cork occurrence with the body.

It then groups all of the timeline nodes that were created as a result of the operations within a timeline group.  Because all of the work is performed within a single command, it is all contained within a single transaction and can be undone with one undo.

This is also a good sample to demonstrate how proxies simplify development. This sample doesn't do anything specific to proxies but that's because of the existence of proxies.  The selection of bodies can be at any level of the assembly and there can be mutliple instance of a single component that can be selected.  Because of proxies, the geometry on these is returned as if it exists at the top-level (root) or the assembly so the program doesn't need to account for this since Fusion and proxies handle it all automatically.