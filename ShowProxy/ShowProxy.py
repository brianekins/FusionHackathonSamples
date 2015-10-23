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

# Global variable used to maintain a reference to all event handlers.
handlers = []

# CommandCreated event handler class.
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            command = adsk.core.Command.cast(args.command)
            inputs = command.commandInputs

            # Create a selection input to get a selected entity from the user.            
            selectInput = inputs.addSelectionInput('selectEnt', 'Selection', 'Select an entity')
            selectInput.setSelectionLimits(1, 1)
            
            # Create a text box that will be used to display the results.
            textResult = inputs.addTextBoxCommandInput('textResult', '', '', 2, True)
    
            # Connect to the input changed event.
            onInputChanged = MyInputChangedHandler()
            command.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
        
        
# InputChanged event handler class.
class MyInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # Get the selection command input.
            cmdInput = adsk.core.CommandInput.cast(args.input)
            if cmdInput.id == 'selectEnt':
                selInput = adsk.core.SelectionCommandInput.cast(cmdInput)
                # Check that an entity is selected.
                if selInput.selectionCount > 0:
                    ent = selInput.selection(0).entity

                    # Create a string showing the proxy path.    
                    path = getPath(ent)
                    entType = ent.objectType
                    entType = entType.split(':')
                    entType = entType[len(entType)-1]
                    path += '/' + entType
                    
                    # Get the text box command input and display the path string in it.
                    textResult = cmdInput.parentCommand.commandInputs.itemById('textResult')
                    textResult.text = path
        except:
            app = adsk.core.Application.get()
            ui = app.userInterface
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

        
# Builds up the string showing the proxy path by stepping up the path from
# the proxy entity itself to each occurrence that defines its context.
def getPath(ent):
    path = ''
    if ent.assemblyContext:

        occ = ent.assemblyContext
        while occ:
            if path == '':
                path = occ.name
            else:
                path = occ.name + '/' + path

            occ = occ.assemblyContext
        
        path = 'Root/' + path
    else:
        path = 'Root'

    return path        
        
        
def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Create a new command and connect to the command created event.
        buttonDef = ui.commandDefinitions.addButtonDefinition('ekinsShowProxyPath', 'Show Proxy', 'Display the proxy path of the selected entity.', 'Resources/ShowProxy')
        onCommandCreated = MyCommandCreatedHandler()
        buttonDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)

        # Add a control for the command into the INSPECT panel.
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

        # Clean up all UI related to this command.
        buttonDef = ui.commandDefinitions.itemById('ekinsShowProxyPath')
        if buttonDef:
            buttonDef.deleteMe()

        inspectPanel = ui.allToolbarPanels.itemById('InspectPanel')
        if inspectPanel.controls.itemById('ekinsShowProxyPath'):
            inspectPanel.controls.itemById('ekinsShowProxyPath').deleteMe()
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
