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

# Global variable used to maintain a reference to all event handlers.
handlers = []

activeDoc = None

# Called when the command is executed.  However, because this command
# is using the ExecutePreview event and is setting the isValidResult property
# to true, the results created in the preview will be used as the final
# results and the Execute will not be called.
class CutoutCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Get the inputs entered in the dialog.
            inputs = args.command.commandInputs
            result = getInput(inputs)
            
            # Draw the geometry.
            app = adsk.core.Application.get()
            drawGeometry(result[0], result[1], result[2], result[3])
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    


class CutoutCommandExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        # Code to react to the event.
        try:
            cmdArgs = adsk.core.CommandEventArgs.cast(args)

            # Get the current value of inputs entered in the dialog.
            inputs = cmdArgs.command.commandInputs
            result = getInput(inputs)
            
            # Draw the preview geometry.
            drawGeometry(result[0], result[1], result[2], result[3])
            
            # Set this property indicating that the preview is a good
            # result and can be used as the final result when the command
            # is executed.
            cmdArgs.isValidResult = True            
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    


# Calculate the minimum distance between the input point and plane.
def MinDistPointToPlane(point, plane):
     temp = -(plane.origin.x * plane.normal.x + plane.origin.y * plane.normal.y + plane.origin.z * plane.normal.z)

     minDistPointToPlane = (plane.normal.x * point.x + plane.normal.y * point.y + plane.normal.z * point.z + temp) / math.sqrt(plane.normal.x ** 2 + plane.normal.y ** 2 + plane.normal.z ** 2)
     return minDistPointToPlane


class CutoutCommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Check to see if it's the plane input.
            if args.input.id == 'planeSelect':
                # Enable/disable the point input field depending on if the plane input has been specified.
                planeInput = args.input
                pointInput = args.firingEvent.sender.commandInputs.itemById('pointSelect')
                if planeInput.selectionCount == 1:
                    pointInput.isEnabled = True
                else:
                    pointInput.clearSelection()
                    pointInput.isEnabled = False
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    
    


class CutoutCommandSelectionEventHandler(adsk.core.SelectionEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Check to see that selection of points is being done.
            if args.firingEvent.activeInput.id == 'pointSelect':
                # Get the selected plane.
                inputs = args.firingEvent.sender.commandInputs
                planeSelect = inputs.itemById('planeSelect')
                planeGeom = planeSelect.selection(0).entity.geometry
                
                # Get the geometry of the point being selected.
                sel = args.selection
                ent = sel.entity
                if ent.objectType == adsk.fusion.SketchPoint.classType():
                    pointGeom = ent.worldGeometry
                else:
                    pointGeom = ent.geometry
                
                # Validate that the point lies on the plane and set whether it is selectable or not.
                if math.fabs(MinDistPointToPlane(pointGeom, planeGeom)) < 0.00001:
                    args.isSelectable = True
                else:
                    args.isSelectable = False
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    


# Event handler class.
class CutoutCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            
            global activeDoc
            activeDoc = app.activeDocument
    
            # Define the command dialog.
            cmd = adsk.core.Command.cast(args.command)
            cmdInputs = cmd.commandInputs
            
            # Create the selector for the plane.
            planeInput = cmdInputs.addSelectionInput('planeSelect', 'Select Plane', 'Select Plane')
            planeInput.addSelectionFilter('PlanarFaces')
            planeInput.addSelectionFilter('ConstructionPlanes')
            planeInput.setSelectionLimits(1,1)
    
            # Create the selector for the points.
            pointInput = cmdInputs.addSelectionInput('pointSelect', 'Select Points', 'Select Points')
            pointInput.addSelectionFilter('Vertices')
            pointInput.addSelectionFilter('ConstructionPoints')
            pointInput.addSelectionFilter('SketchPoints')
            pointInput.setSelectionLimits(1,0)
            pointInput.isEnabled = False
    
            # Create the list for types of shapes.
            shapeList = cmdInputs.addDropDownCommandInput('shapeList', 'Shape Type', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            shapeList.listItems.add('Square', True, 'Resources/Square', -1)
            shapeList.listItems.add('Circle', False, 'Resources/Circle', -1)
            shapeList.listItems.add('Pentagon', False, 'Resources/Pentagon', -1)
    
            # Create the slider input for the size.
            des = adsk.fusion.Design.cast(app.activeProduct)
            um = des.unitsManager
            oneUnit = um.convert(1, des.unitsManager.defaultLengthUnits, 'cm') * 4
            sizeSlider = cmdInputs.addFloatSliderCommandInput('sizeSlider', 'Size', des.unitsManager.defaultLengthUnits, oneUnit, oneUnit * 15, False)
            sizeSlider.valueOne = oneUnit * 4
            sizeSlider.spinStep = oneUnit/2
            
            # Connect to the execute event.
            onExecute = CutoutCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)      
    
            # Connect to the execute preview event.
            onExecutePreview = CutoutCommandExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            handlers.append(onExecutePreview)
            
            # Connect to the input changed event.
            onInputChanged = CutoutCommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)
            
            # Connect to the selection event.
            onSelectionEvent = CutoutCommandSelectionEventHandler()
            cmd.selectionEvent.add(onSelectionEvent)
            handlers.append(onSelectionEvent)
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    


# Gets the current values from the command dialog.
def getInput(inputs):
    try:
        for input in inputs:        
            if input.id == 'planeSelect':
                planeEnt = input.selection(0).entity
            elif input.id == 'pointSelect':
                pointEnts = adsk.core.ObjectCollection.create()
                for i in range(0, input.selectionCount):
                    pointEnts.add(input.selection(i).entity)
            elif input.id == 'sizeSlider':
                size = input.valueOne
            elif input.id == 'shapeList':
                shape = input.selectedItem.name
                
        return (planeEnt, pointEnts, shape, size)
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    

   
# Draws the shapes based on the input argument.     
def drawGeometry(planeEnt, pointEnts, shape, size):
    try:
        # Get the design.
        app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)
        
        # Create a new sketch plane.
        sk = des.rootComponent.sketches.add(planeEnt)    
        
        for pntEnt in pointEnts:
            # Project the point onto the sketch.
            skPnt = sk.project(pntEnt).item(0)
            
            if shape == 'Square':
                # Draw four lines to define a square.
                skLines = sk.sketchCurves.sketchLines
                line1 = skLines.addByTwoPoints(adsk.core.Point3D.create(skPnt.geometry.x - size/2, skPnt.geometry.y - size/2, 0), adsk.core.Point3D.create(skPnt.geometry.x + size/2, skPnt.geometry.y - size/2, 0))
                line2 = skLines.addByTwoPoints(line1.endSketchPoint, adsk.core.Point3D.create(skPnt.geometry.x + size/2, skPnt.geometry.y + size/2, 0))
                line3 = skLines.addByTwoPoints(line2.endSketchPoint, adsk.core.Point3D.create(skPnt.geometry.x - size/2, skPnt.geometry.y + size/2, 0))
                line4 = skLines.addByTwoPoints(line3.endSketchPoint, line1.startSketchPoint)
            elif shape == 'Circle':
                # Draw a circle.
                sk.sketchCurves.sketchCircles.addByCenterRadius(skPnt, size/2)
            elif shape == 'Pentagon':
                # Draw file lines to define a pentagon.
                skLines = sk.sketchCurves.sketchLines
                angle = math.pi/2
                halfSize = size/2
                x1 = halfSize * math.cos(angle)
                y1 = halfSize * math.sin(angle)

                angle += math.pi/2.5
                x2 = halfSize * math.cos(angle)
                y2 = halfSize * math.sin(angle)
                line1 = skLines.addByTwoPoints(adsk.core.Point3D.create(x1 + skPnt.geometry.x, y1 + skPnt.geometry.y, 0), adsk.core.Point3D.create(x2 + skPnt.geometry.x, y2 + skPnt.geometry.y, 0))

                angle += math.pi/2.5
                x = halfSize * math.cos(angle)
                y = halfSize * math.sin(angle)
                line2 = skLines.addByTwoPoints(line1.endSketchPoint, adsk.core.Point3D.create(x + skPnt.geometry.x, y + skPnt.geometry.y, 0))

                angle += math.pi/2.5
                x = halfSize * math.cos(angle)
                y = halfSize * math.sin(angle)
                line3 = skLines.addByTwoPoints(line2.endSketchPoint, adsk.core.Point3D.create(x + skPnt.geometry.x, y + skPnt.geometry.y, 0))

                angle += math.pi/2.5
                x = halfSize * math.cos(angle)
                y = halfSize * math.sin(angle)
                line4 = skLines.addByTwoPoints(line3.endSketchPoint, adsk.core.Point3D.create(x + skPnt.geometry.x, y + skPnt.geometry.y, 0))
                
                line5 = skLines.addByTwoPoints(line4.endSketchPoint, line1.startSketchPoint)
    
        # Find the inner profiles (only those with one loop).
        profiles = adsk.core.ObjectCollection.create()
        for prof in sk.profiles:
            if prof.profileLoops.count == 1:
                profiles.add(prof)

        # Create the extrude feature.            
        input = des.rootComponent.features.extrudeFeatures.createInput(profiles, adsk.fusion.FeatureOperations.CutFeatureOperation)
        input.setDistanceExtent(True, adsk.core.ValueInput.createByReal(10))
        extrude = des.rootComponent.features.extrudeFeatures.add(input)
    except:
        app = adsk.core.Application.get()
        ui = app.userInterface
        ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))    
        

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        existingDef = ui.commandDefinitions.itemById('ekinsCutouts')
        if existingDef:
            existingDef.deleteMe()
            
        # Create the command definition.
        cutoutsCmdDef = ui.commandDefinitions.addButtonDefinition('ekinsCutouts', 'Cutout Shapes', 'Creates various shaped cutouts on the selected face at the specified locations.', './Resources/Cutouts')

        # Connect to the command created event.
        onCommandCreated = CutoutCommandCreatedHandler()
        cutoutsCmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)                

        # Get the CREATE toolbar panel. 
        createPanel = ui.allToolbarPanels.itemById('SolidCreatePanel')
                
        # Add the command below the Web command.
        createPanel.controls.addCommand(cutoutsCmdDef, 'FusionWebCommand', False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Delete the control
        createPanel = ui.allToolbarPanels.itemById('SolidCreatePanel')
        cutoutsControl = createPanel.controls.itemById('ekinsCutouts')
        if cutoutsControl:
            cutoutsControl.deleteMe()

        # Delete the command definition.                
        existingDef = ui.commandDefinitions.itemById('ekinsCutouts')
        if existingDef:
            existingDef.deleteMe()

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
