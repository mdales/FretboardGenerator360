# Author-Digital Flapjack Ltd
# Description-Test

import math

import adsk.core, adsk.fusion, adsk.cam, traceback


# Calculates the fret positions given a scale length and the number of frets. Includes the zero fret.
# @param {number} scaleLength - The scale length in whatever units.
# @param {number} frets - How many frets to calculate for.
# @return {[number]} A list of positions in the same units as the scale length was provided.
def generateFretPositions(scaleLength, frets):
    positions = []
    for i in range(frets + 1):
        positions.append(scaleLength - (scaleLength / math.pow(2, i / 12)))
    return positions


# Draws a single inlay marker of the style provided
# @param {Object} paths - The set of paths being built for the neck.
# @param {String} style - Either "dots" or "crosshairs".
# @param {Number} x_pos - The center x position on the inlay.
# @param {Number} y_pos - The center u position on the inlay.
# @param {Number} radius - The radius on the inlay.
def drawInlay(sketch, style, x_pos, y_pos, radius):

    if style == "Dots":
        circles = sketch.sketchCurves.sketchCircles
        circles.addByCenterRadius(adsk.core.Point3D.create(x_pos, y_pos, 0), radius)
    elif style == "Crosshairs":
        lines = sketch.sketchCurves.sketchLines
        lines.addByTwoPoints(adsk.core.Point3D.create(x_pos, y_pos - radius, 0.0), adsk.core.Point3D.create(x_pos, y_pos + radius, 0.0))
        lines.addByTwoPoints(adsk.core.Point3D.create(x_pos - radius, y_pos, 0.0), adsk.core.Point3D.create(x_pos + radius, y_pos, 0.0))


# Returns the model for a fretboard in mm
# @param {Object} params - An object with all the form params.
# @return {Model} A Model object.
def generateFretboard(params, sketch):

    height = 7.5
    x_offset = 0.0
    y_offset = 0.0
    # slotWidth = 0.5

    positions = generateFretPositions(params['scaleLength'], params['frets'])

    lines = sketch.sketchCurves.sketchLines

    # draw the nut far side
    if params['slotStyle'] == "line":
        lines.addByTwoPoints(adsk.core.Point3D.create(x_offset - params['nutWidth'], y_offset, 0.0),
            adsk.core.Point3D.create(x_offset - params['nutWidth'], y_offset + height, 0.0))
    # else:
    #     var r = new makerjs.models.Rectangle(slotWidth, height)
    #     r.origin = [(x_offset - params.nutWidth) - (slotWidth / 2.0), y_offset]
    #     models.append(r)

    # draw the frets
    for i in range(len(positions)):
        pos = x_offset + positions[i]

        # The fret itself
        if params['slotStyle'] == "line":
            lines.addByTwoPoints(adsk.core.Point3D.create(pos, y_offset, 0.0), adsk.core.Point3D.create(pos, y_offset + height, 0.0))
        # else:
        #     r = new makerjs.models.Rectangle(slotWidth, height)
        #     r.origin = [pos - (slotWidth / 2.0), y_offset]
        #     models.append(r)

        # Do the inlay markers next in a traditional style
        if i == 0:
            continue

        fretNumber = i % 12
        if fretNumber in {3, 5, 7, 9}:
            x_pos = pos - ((positions[i] - positions[i - 1]) / 2.0)
            y_pos = y_offset + (height / 2.0)
            radius = params['inlayWidth'] / 2.0

            drawInlay(sketch, params['inlayStyle'], x_pos, y_pos, radius)

        elif fretNumber == 0:
            x_pos = pos - ((positions[i] - positions[i - 1]) / 2.0)
            upper_y = y_offset + (height * 3.0 / 4.0)
            lower_y = y_offset + (height / 4.0)
            radius = params['inlayWidth'] / 2.0

            drawInlay(sketch, params['inlayStyle'], x_pos, upper_y, radius)
            drawInlay(sketch, params['inlayStyle'], x_pos, lower_y, radius)


# Global list to keep all event handlers in scope.
# This is only needed with Python.
handlers = []


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions

        # Create a button command definition.
        buttonSample = cmdDefs.addButtonDefinition('FreboardGeneratorButtonId', 
                                                   'Freboard Generator', 
                                                   'Generate a sketch containing a fretboard')
        
        # Connect to the command created event.
        sampleCommandCreated = SampleCommandCreatedEventHandler()
        buttonSample.commandCreated.add(sampleCommandCreated)
        handlers.append(sampleCommandCreated)
        
        # Execute the command.
        buttonSample.execute()
        
        # Keep the script running.
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for the commandCreated event.
class SampleCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command
        inputs = cmd.commandInputs

        _ = inputs.addIntegerSliderCommandInput('frets', 'Fret Count', 21, 25, False)
        _ = inputs.addValueInput('scale', 'Scale Length', '', adsk.core.ValueInput.createByReal(25.5))
        inlayStyle = inputs.addDropDownCommandInput('inlayStyle', 'Inlay Style', adsk.core.DropDownStyles.TextListDropDownStyle)
        inlayStyle.listItems.add('Dots', True)
        inlayStyle.listItems.add('Crosshairs', False)
        _ = inputs.addValueInput('nutWidth', 'Nut width', '', adsk.core.ValueInput.createByReal(3.0))

        # Connect to the execute event.
        onExecute = SampleCommandExecuteHandler()
        cmd.execute.add(onExecute)
        handlers.append(onExecute)


# Event handler for the execute event.
class SampleCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        # # Get the values from the command inputs. 
        inputs = eventArgs.command.commandInputs

        # Code to react to the event.
        app = adsk.core.Application.get()
        des = adsk.fusion.Design.cast(app.activeProduct)
        
        if des:
            rootComp = des.rootComponent
            sketches = rootComp.sketches
            xyPlane = rootComp.xYConstructionPlane
            sketch = sketches.add(xyPlane)

            params = {
                'nutWidth': inputs.itemById('nutWidth').value / 10.0,
                'slotStyle': 'line',
                'scaleLength': inputs.itemById('scale').value * 2.54,
                'frets': inputs.itemById('frets').valueOne,
                'inlayStyle': inputs.itemById('inlayStyle').selectedItem.name,
                'inlayWidth': 0.5,
            }

            generateFretboard(params, sketch)

        # Force the termination of the command.
        adsk.terminate()   
 
           
def stop(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # Delete the command definition.
        cmdDef = ui.commandDefinitions.itemById('FreboardGeneratorButtonId')
        if cmdDef:
            cmdDef.deleteMe()            
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))