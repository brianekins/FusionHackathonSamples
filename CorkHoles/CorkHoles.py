#    (C) Copyright 2015 by Autodesk, Inc.
#    Permission to use, copy, modify, and distribute this software in
#    object code form for any purpose and without fee is hereby granted,
#    provided that the above copyright notice appears in all copies and
#    that both that copyright notice and the limited warranty and restricted
#    rights notice below appear in all supporting documentation.
#    
#    AUTODESK PROVIDES THIS PROGRAM "AS IS" AND WITH ALL FAULTS.
#    AUTODESK SPECIFICALLY DISCLAIMS ANY IMPLIED WARRANTY OF MERCHANTABILITY OR
#    FITNESS FOR A PARTICULAR USE. AUTODESK, INC. DOES NOT WARRANT THAT THE
#    OPERATION OF THE PROGRAM WILL BE UNINTERRUPTED OR ERROR FREE.

import adsk.core, adsk.fusion, traceback
import math

handlers = []

def findHoleEdges(inBody):
    try:
        body = adsk.fusion.BRepBody.cast(inBody)
        
        # Initialize a list that's used to return information about the found "hole" edges.
        corkPositions = []
        
        # Iterate over all the edges looking for "hole" edges.
        for edge in body.edges:
            if not edge.isDegenerate:
                # Check to see if the edge is a circle.
                if edge.geometry.curveType == adsk.core.Curve3DTypes.Circle3DCurveType:
                    # Get the two faces that are connected by the edge.
                    cylinderFace = None
                    planeFace = None
                    for face in edge.faces:
                        if face.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType:
                            cylinderFace = face
                        elif face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
                            planeFace = face
        
                    if cylinderFace and planeFace:
                        # Check to see if the circular edge is an inner loop of the planar face
                        # and that the loop consists of a single curve, which is the circular edge.
                        for planeLoop in planeFace.loops:
                            if not planeLoop.isOuter and planeLoop.edges.count == 1 and planeLoop.edges[0] == edge:
                                # Get an arbitrary point on the cylinder.
                                pnt = cylinderFace.pointOnFace
        
                                # Get a normal from the cylinder.
                                (rslt, normal) = cylinderFace.evaluator.getNormalAtPoint(pnt)
        
                                # Change the length of the normal to be the radius of the cylinder.
                                normal.normalize()
                                cyl = cylinderFace.geometry
                                normal.scaleBy(cyl.radius)
                                
                                # Translate the point on the cylinder along the normal vector.
                                pnt.translateBy(normal)
                                
                                # Check to see if the point lies along the cylinder axis.
                                # if it does, then this is a hole and not a boss.
                                if distPointToLine(pnt, cyl.origin, cyl.axis) < cyl.radius:
                                    # Create a matrix that will define the position of the cork.
                                    (rslt, zDir) = planeFace.evaluator.getNormalAtPoint(planeFace.pointOnFace)
                                    xDir = normal
                                    yDir = zDir.crossProduct(xDir)
                                    xDir.normalize()
                                    yDir.normalize()
                                    zDir.normalize()
                                    transMatrix = adsk.core.Matrix3D.create()
                                    transMatrix.setWithCoordinateSystem(edge.geometry.center, xDir, yDir, zDir)
                                    
                                    # Save the edge, matrix, and radius.
                                    corkPositions.append([edge, transMatrix, edge.geometry.radius])
                                    
                                break
    
        return corkPositions
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
    
    
# Computes the distance between the given infinite line and a point.
def distPointToLine(point, lineRootPoint, lineDirection):
    try:    
        # Compute the distance between the point and the origin point of the line.
        dist = lineRootPoint.distanceTo(point)
    
        # Special case when the point is the same as the line root point.
        if dist < 0.000001:
            return 0
        
        # Create a vector that defines the direction from the lines origin to the input point.
        pointVec = lineRootPoint.vectorTo(point)
        
        # Get the angle between the two vectors.
        angle = lineDirection.angleTo(pointVec)
        
        # Calculate the side height of the triangle.
        return dist * math.sin(angle)
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Look for an existing cork of the needed size or create a new one
# if an existing one isn't found and insert it using the input matrix.
def placeCork(design, radius, height, matrix):
    try:
        # Look for an existing component by looking for a pre-defined name.
        corkName = 'Cork_' + "{0:.6f}".format(radius)
        for checkComp in design.allComponents:
            if checkComp.description == corkName:
                occ = design.rootComponent.occurrences.addExistingComponent(checkComp, matrix)
                return occ
                
        # No existing cork was found so create a new one.
        occ = design.rootComponent.occurrences.addNewComponent(matrix)
        
        corkComp = adsk.fusion.Component.cast(occ.component)
        corkComp.name = 'Cork (' + design.unitsManager.formatInternalValue(radius, design.unitsManager.defaultLengthUnits, True) + ')'
        corkComp.description = corkName
        sketch = corkComp.sketches.add(corkComp.xZConstructionPlane)
        lines = sketch.sketchCurves.sketchLines
        l1 = lines.addByTwoPoints(adsk.core.Point3D.create(radius*1.2, -height/2, 0), adsk.core.Point3D.create(0, -height/2, 0))
        l2 = lines.addByTwoPoints(l1.endSketchPoint, adsk.core.Point3D.create(0, height/2, 0))
        l3 = lines.addByTwoPoints(l2.endSketchPoint, adsk.core.Point3D.create(radius*0.8, height/2, 0))
        l4 = lines.addByTwoPoints(l3.endSketchPoint, l1.startSketchPoint)
    
        revInput = corkComp.features.revolveFeatures.createInput(sketch.profiles.item(0), l2, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        revInput.setAngleExtent(False, adsk.core.ValueInput.createByString("360 deg"))
        rev = corkComp.features.revolveFeatures.add(revInput)
        
        # Change the color.
        app  = adsk.core.Application.get()
        matLib = app.materialLibraries.itemByName('Fusion 360 Appearance Library')
        color = matLib.appearances.itemByName('Paint - Enamel Glossy (Yellow)')
        body = rev.bodies.item(0)
        body.appearance = color
        
        return occ
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def placeCorks(body):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        des = adsk.fusion.Design.cast(app.activeProduct)

        # Get the hole edges in the body.
        holeInfos = findHoleEdges(body)
        
        firstTimelineObj = None
        lastTimelineObj = None
        
        # Iterate through each edge.
        for holeInfo in holeInfos:
            (partEdge, transMatrix, radius) = holeInfo

            # Place the cork.            
            height = radius * 1.5
            corkOcc = placeCork(des, radius, height, transMatrix)
            
            # Find the top edge of the cork, which is the circular edge that is larger than the defined radius, 
            corkComp = corkOcc.component
            corkBody = corkComp.bRepBodies.item(0)
            topEdge = None
            for corkEdge in corkBody.edges:
                if corkEdge.geometry.curveType == adsk.core.Curve3DTypes.Circle3DCurveType:
                    circle = adsk.core.Circle3D.cast(corkEdge.geometry)
                    if circle.radius > radius:
                        topEdge = corkEdge
                        break

            # The edge was found in the context of the cork part.  Create
            # a proxy in the context of the root component.
            topEdge = topEdge.createForAssemblyContext(corkOcc)
            
            # Create a joint between the part edge and the cork edge.                        
            partJointGeom = adsk.fusion.JointGeometry.createByCurve(partEdge, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
            corkJointGeom = adsk.fusion.JointGeometry.createByCurve(topEdge, adsk.fusion.JointKeyPointTypes.CenterKeyPoint)
            jointInput = corkComp.joints.createInput(corkJointGeom, partJointGeom)
            jointInput.offset = adsk.core.ValueInput.createByReal(-height/2)
            jointInput.isFlipped = True            
            joint = corkOcc.sourceComponent.joints.add(jointInput)
 
            # Capture the first and last timeline objects.
            if not firstTimelineObj:
                firstTimelineObj = corkOcc.timelineObject
                
            lastTimelineObj = joint.timelineObject
                
        # Return the first and last timeline objects that were created as part of this cork.
        return (firstTimelineObj, lastTimelineObj)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class MyExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface
    
            inputs = args.command.commandInputs
            
            # Get the selected bodies before the processing begins because the selection will be cleared.
            selectInput = inputs.itemById('selectEnt')
            bodies = []
            for i in range(0, selectInput.selectionCount):
                bodies.append(selectInput.selection(i).entity)
    
            # Place the corks on each body.
            firstTimelineObject = None
            lastTimelineObject = None
            for body in bodies:
                (first, last) = placeCorks(body)
                if not firstTimelineObject:
                    firstTimelineObject = first            

                lastTimelineObject = last
    
            des = adsk.fusion.Design.cast(app.activeProduct)            
            group = des.timeline.timelineGroups.add(firstTimelineObject.index, lastTimelineObject.index)
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# CommandCreated event handler class.
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            command = adsk.core.Command.cast(args.command)
            inputs = command.commandInputs
            
            selectInput = inputs.addSelectionInput('selectEnt', 'Bodies', 'Select 1 or more bodies.')
            selectInput.addSelectionFilter('Bodies')
            selectInput.setSelectionLimits(1, 0)
                
            onExecute = MyExecuteHandler()
            command.execute.add(onExecute)
            handlers.append(onExecute)
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        buttonDef = ui.commandDefinitions.addButtonDefinition('ekinsCorkSample', 'Cork all holes', 'Fills all holes in a selected body with corks.', 'Resources/CorkHoles')
        onCommandCreated = MyCommandCreatedHandler()
        buttonDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)

        assemblyPanel = ui.allToolbarPanels.itemById('AssembleJointsPanel')
        assemblyPanel.controls.addSeparator('ekinsSeperator')
        assemblyPanel.controls.addCommand(buttonDef)                
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Clean up the UI.
        buttonDef = ui.commandDefinitions.itemById('ekinsCorkSample')
        if buttonDef:
            buttonDef.deleteMe()

        assemblyPanel = ui.allToolbarPanels.itemById('AssembleJointsPanel')
        if assemblyPanel:
            seperator = assemblyPanel.controls.itemById('ekinsSeperator')
            if seperator:
                seperator.deleteMe()
                
            button = assemblyPanel.controls.itemById('ekinsCorkSample')
            if button:
                button.deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
