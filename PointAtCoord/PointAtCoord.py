#Author-Brian Ekins
#Description-Create a construction point at the specified X,Y,Z coordinates.

import adsk.core, adsk.fusion, adsk.cam, traceback
handlers = []
_isParametric = False
_app = adsk.core.Application.get()
_ui = _app.userInterface
_design = adsk.fusion.Design.cast(None)


# Event handler for the commandCreated event.
class CommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
    
            # Connect to the execute event.
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)
            
            # Connect ot the preview event.       
            onExecutePreview = ExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            handlers.append(onExecutePreview)        
            
            # Check to see if this is a parametric or direct-edit model.
            global _design
            _design = adsk.fusion.Design.cast(_app.activeProduct)
            if _design:
                inputs = cmd.commandInputs
                
                global _isParametric
                if _design.designType == adsk.fusion.DesignTypes.ParametricDesignType:
                    _isParametric = True
                    
                    # Create a list of base features.
                    listInput = inputs.addDropDownCommandInput('baseFeatureList', 'Base feature', adsk.core.DropDownStyles.TextListDropDownStyle) 
                    listInput.listItems.add('Create new Base Feature', True, '')                
    
                    # Get the name of the last used base feature to use as the default.
                    baseFeatureNameAttrib = _design.attributes.itemByName('ekinsPointAtCoord', 'BaseFeatureName')
                    if baseFeatureNameAttrib:
                        baseFeatureName = baseFeatureNameAttrib.value
    
                    for baseFeature in _design.rootComponent.features.baseFeatures:
                        if baseFeatureName == baseFeature.name:
                            listInput.listItems.item(0).isSelected = False
                            listInput.listItems.add(baseFeature.name, True, '')                                
                        else:
                            listInput.listItems.add(baseFeature.name, False, '')
                else:
                    _isParametric = False
                
                # Add string input to get the name.
                nameInput = inputs.addStringValueInput('pointName', 'Name', 'XYZ Point')            
                
                # Add value inputs to get the X, Y, and Z values.
                xValInput = inputs.addValueInput('xValInput', 'X Position', _design.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(0))
                yValInput = inputs.addValueInput('yValInput', 'Y Position', _design.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(0))
                zValInput = inputs.addValueInput('zValInput', 'Z Position', _design.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(0))
            else:
                _ui.messageBox('You must be in a modeling related workspace.')
                return False
        except:
            _ui.messageBox('Unexpected failure:\n{}'.format(traceback.format_exc()))


# Event handler for the executePreview event.
class ExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
        DrawPoint(eventArgs.firingEvent.sender.commandInputs)


# Event handler for the execute event.
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
        DrawPoint(eventArgs.command.commandInputs)


def DrawPoint(inputs):
    try:
        # Get the values from the command inputs.
        xValInput = adsk.core.ValueCommandInput.cast(inputs.itemById('xValInput'))
        xVal = xValInput.value
    
        yValInput = adsk.core.ValueCommandInput.cast(inputs.itemById('yValInput'))
        yVal = yValInput.value
    
        zValInput = adsk.core.ValueCommandInput.cast(inputs.itemById('zValInput'))
        zVal = zValInput.value
        
        nameInput = adsk.core.StringValueCommandInput.cast(inputs.itemById('pointName'))
        name = nameInput.value

        root = _design.rootComponent
    
        if _isParametric:
            # Get the name of the base feature to create the point in.
            listInput = adsk.core.DropDownCommandInput.cast(inputs.itemById('baseFeatureList'))
            baseFeatureName = listInput.selectedItem.name
                        
            if baseFeatureName == 'Create new Base Feature':
                # Create a new base feature.
                baseFeature = root.features.baseFeatures.add()
            else:
                # Get the specified existing base feature.
                baseFeature = root.features.baseFeatures.itemByName(baseFeatureName)
            
            # Add a construction point ot the base feature.
            baseFeature.startEdit()        
            pointInput = root.constructionPoints.createInput()
            pointInput.setByPoint(adsk.core.Point3D.create(xVal, yVal, zVal))
            pointInput.targetBaseOrFormFeature = baseFeature
            point = root.constructionPoints.add(pointInput)
            baseFeature.finishEdit()
            
            # Save the name of the base feature use as an attribute so it
            # can be used as the default the next time the command is run.
            _design.attributes.add('ekinsPointAtCoord', 'BaseFeatureName', baseFeature.name)
        else:
            # Add a construction point to the root component.
            pointInput = root.constructionPoints.createInput()
            pointInput.setByPoint(adsk.core.Point3D.create(xVal, yVal, zVal))
            point = root.constructionPoints.add(pointInput)
            
        point.name = name
    except:
        _ui.messageBox('Unexpected failure:\n{}'.format(traceback.format_exc()))


def run(context):
    try:
        # Get the CommandDefinitions collection.
        cmdDefs = _ui.commandDefinitions
        
        # Create a button command definition.
        buttonDef = cmdDefs.addButtonDefinition('ekinsPointAtCoord', 
                                                'Point at Coordinate', 
                                                'Creates construction point at specified xyz coordinate.',
                                                './Resources/PointAtCoord')
        
        # Connect to the command created event.
        commandCreated = CommandCreatedEventHandler()
        buttonDef.commandCreated.add(commandCreated)
        handlers.append(commandCreated)
        
        # Get the CONSTRUCTION panel. 
        constructionPanel = _ui.allToolbarPanels.itemById('ConstructionPanel')
        
        # Add the button just below the POINT AT VERTEX command.
        buttonControl = constructionPanel.controls.addCommand(buttonDef, 'WorkPointFromPointCommand', False)
    except:
        _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    try:
        buttonDef = _ui.commandDefinitions.itemById('ekinsPointAtCoord')
        if buttonDef:
            buttonDef.deleteMe()
        
        # Get the CONSTRUCTION panel. 
        constructionPanel = _ui.allToolbarPanels.itemById('ConstructionPanel')
        buttonControl = constructionPanel.controls.itemById('ekinsPointAtCoord')
        if buttonControl:
            buttonControl.deleteMe()       
    except:
        _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
