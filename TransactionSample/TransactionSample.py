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

def drawLines():
    app = adsk.core.Application.get()
    des = adsk.fusion.Design.cast(app.activeProduct)

    sk = des.rootComponent.sketches.add(des.rootComponent.xYConstructionPlane)
    currentX = 0
    xOffset = 1
    lines = sk.sketchCurves.sketchLines
    sk.isComputeDeferred = True
    for i in range(0,100):
        lines.addByTwoPoints(adsk.core.Point3D.create(currentX, 0, 0), adsk.core.Point3D.create(currentX, 10, 0))
        currentX += xOffset
    sk.isComputeDeferred = False


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        # Do whatever the command does.
        drawLines()
        
        # Force the termination of the command.
        adsk.terminate()        


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        cmd = adsk.core.Command.cast(args.command)

        # Connect up to the command executed event.        
        onExecute = CommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)
        

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # Create the command definition.
        if ui.commandDefinitions.itemById('transactionSample'):
            ui.commandDefinitions.itemById('transactionSample').deleteMe()            
        cmdDef = ui.commandDefinitions.addButtonDefinition('transactionSample', 'Transaction Sample', '', '')
        
        # Connect up to the command created event.
        onCommandCreated = CommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        
        # execute the command.
        cmdDef.execute()
        
        # Keep the script running.
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
