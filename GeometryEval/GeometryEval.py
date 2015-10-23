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

handlers = []

# Draws sketch lines that represent surface normals on the input face.
# The normals are evenly spaced in the parametric space of the surface
# where the number of normals is defined by the input density argument.
def drawNormals(inputFace, density):
    try:
        face = adsk.fusion.BRepFace.cast(inputFace)
        app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)

        # Determine the min/max U and V values.
        surfEval = face.evaluator
        paramRange = surfEval.parametricRange()
        minU = paramRange.minPoint.x
        minV = paramRange.minPoint.y
        extentU = paramRange.maxPoint.x - paramRange.minPoint.x
        extentV = paramRange.maxPoint.y - paramRange.minPoint.y
    
        # Build up an array of UV points on the surface.
        uvParams = []
        for uCount in range(0, density+1):
            uVal = minU + (extentU/density) * uCount
            for vCount in range(0, density+1):
                vVal = minV + (extentV/density) * vCount
                uvParams.append(adsk.core.Point2D.create(uVal, vVal))
        
        # Get the positions of the uv values.
        surfEval = face.evaluator
        (retVal, points) = surfEval.getPointsAtParameters(uvParams)
        (retVal, normals) = surfEval.getNormalsAtParameters(uvParams)
                
        # Create a sketch and draw the results.
        sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
        lines = sk.sketchCurves.sketchLines
        sk.isComputeDeferred = True
        pntCount = 0
        length = 2
        for vCount in range(0, density+1):
            for uCount in range(0, density+1):
                # Draw each normal.
                pnt1 = adsk.core.Point3D.cast(points[pntCount])
                pnt2 = pnt1.copy()
                normal = adsk.core.Vector3D.cast(normals[pntCount])
                normal.scaleBy(length)
                pnt2.translateBy(normal)
                
                lines.addByTwoPoints(pnt1, pnt2)
                pntCount += 1
        sk.isComputeDeferred = False
    except:
        if sk:
            if sk.isValid:
                sk.isComputeDeferred = False
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    
def getPoint(points, uIndex, vIndex, density):
    return points[vIndex*(density+1) + uIndex]

# Draws sketch lines that represent iso curves along the surface in the U and V
# directions.  The iso curves are evenly spaced in the parametric space of the
# surface where the number of curves is defined by the input density argument.    
def drawUVCurves(ent, density):
    try:
        face = adsk.fusion.BRepFace.cast(ent)
        app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)
    
        # Determine the min/max U and V values.
        surfEval = face.evaluator
        paramRange = surfEval.parametricRange()
        minU = paramRange.minPoint.x
        minV = paramRange.minPoint.y
        extentU = paramRange.maxPoint.x - paramRange.minPoint.x
        extentV = paramRange.maxPoint.y - paramRange.minPoint.y
    
        # Build up an array of UV points on the surface.
        uvParams = []
        for uCount in range(0, density+1):
            uVal = minU + (extentU/density) * uCount
            for vCount in range(0, density+1):
                vVal = minV + (extentV/density) * vCount
                uvParams.append(adsk.core.Point2D.create(uVal, vVal))
        
        # Get the positions of the uv values.
        surfEval = face.evaluator
        (retVal, points) = surfEval.getPointsAtParameters(uvParams)            
                
        # Create a sketch and draw the results.
        sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
        lines = sk.sketchCurves.sketchLines
        sk.isComputeDeferred = True        
        for vCount in range(0, density+1):
            for uCount in range(0, density+1):
                # Draw the lines for the columns.
                if vCount > 0:
                    lines.addByTwoPoints(getPoint(points, uCount, vCount, density), getPoint(points, uCount, vCount-1, density))
                    
                # Draw the lines for the rows.
                if uCount > 0:
                    lines.addByTwoPoints(getPoint(points, uCount, vCount, density), getPoint(points, uCount-1, vCount, density))
        sk.isComputeDeferred = False
    except:
        if sk:
            if sk.isValid:
                sk.isComputeDeferred = False
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Get the current values of the command inputs.
def getInputs(inputs):
    try:
        selection = inputs.itemById('selectEnt').selection(0)
        face = selection.entity
        
        evalType = inputs.itemById('evalType').selectedItem.name
        
        density = int(inputs.itemById('number').value)
    
        return(evalType, face, density)
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# ExecutePreview event handler class.
class MyExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            cmdArgs = adsk.core.CommandEventArgs.cast(args)
            # Get the current info from the dialog.
            inputs = cmdArgs.command.commandInputs
            (evalType, face, density) = getInputs(inputs)
            
            # Draw the results based on the current type specified in the dialog.
            if evalType == 'Normals':
                drawNormals(face, density)
            elif evalType == 'UV Curves':
                drawUVCurves(face, density)
                
            # Set this property indicating that the preview is a good
            # result and can be used as the final result when the command
            # is executed.
            cmdArgs.isValidResult = True
        except:
            app = adsk.core.Application.get()
            ui  = app.userInterface
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Called when the command is executed.  However, because this command
# is using the ExecutePreview event and is setting the isValidResult property
# to true, the results created in the preview will be used as the final
# results and the Execute will not be called.
class MyExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Get the current info from the dialog.
            inputs = args.command.commandInputs        
            (evalType, face, density) = getInputs(inputs)

            # Draw the results based on the current type specified in the dialog.
            if evalType == 'Normals':
                drawNormals(face, density)
            elif evalType == 'UV Curves':
                drawUVCurves(face, density)
        except:
            app = adsk.core.Application.get()
            ui  = app.userInterface
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# CommandCreated event handler class.
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Code to react to the event.
            command = adsk.core.Command.cast(args.command)
            inputs = command.commandInputs
            
            # Add the selection input to get the one face.
            selectInput = inputs.addSelectionInput('selectEnt', 'Selection', 'Select an entity')
            selectInput.addSelectionFilter('Faces')
            selectInput.setSelectionLimits(1, 1)
    
            # Add the selection input to get the points.
            typeInput = inputs.addDropDownCommandInput('evalType', 'Evaluation Type', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            typeInput.listItems.add('Normals', True, '', -1)
            typeInput.listItems.add('UV Curves', True, '', -1)

            # Add the unitless value input to get the density.            
            densityInput = inputs.addValueInput('number', 'Density', '', adsk.core.ValueInput.createByString('10'))

            # Connect to the execute preview and execute events.
            onExecutePreview = MyExecutePreviewHandler()
            command.executePreview.add(onExecutePreview)
            handlers.append(onExecutePreview)
            
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

        # create the button definition and add a control to the INSPECT panel.
        buttonDef = ui.commandDefinitions.addButtonDefinition('ekinsGeometrySample', 'Geometry Info', 'Display different geometric information for the selected face.', 'Resources/Geometry')
        onCommandCreated = MyCommandCreatedHandler()
        buttonDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        inspectPanel = ui.allToolbarPanels.itemById('InspectPanel')
        inspectPanel.controls.addCommand(buttonDef)                
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Clean up the UI.
        buttonDef = ui.commandDefinitions.itemById('ekinsGeometrySample')
        if buttonDef:
            buttonDef.deleteMe()

        inspectPanel = ui.allToolbarPanels.itemById('InspectPanel')
        if inspectPanel.controls.itemById('ekinsGeometrySample'):
            inspectPanel.controls.itemById('ekinsGeometrySample').deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
