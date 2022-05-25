# Author- pete8081
# Description- Creates cycloidal disk from user defined inputs.

import adsk.core
import adsk.fusion
import adsk.cam
import traceback
import math

defaultDiskName = 'Disk'
defaultPinRadius = .25
defaultPinCircleRadius = 5
# To Do: Add input for number of pins (this ultimately controls the gear reduction = numberOfPins -1)
defaultNumberOfPins = '10'
# To Do: Maybe add value for this too. This controls how smooth the disk is.
defaultContraction = '0.2'
defaultCenterHoleDiameter = 3

handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

newComp = None


def createNewComponent():
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOcss = rootComp.occurrences
    newOcc = allOcss.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component


def drange(start, stop, step):
    r = start
    while r <= stop:
        yield r
        r += step


def cos(angle):
    return math.cos(math.radians(angle))


def sin(angle):
    return math.sin(math.radians(angle))


class DiskCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            disk = Disk()
            for input in inputs:
                if input.id == 'diskName':
                    disk.diskName = input.value
                elif input.id == 'pinRadius':
                    disk.pinRadius = unitsMgr.evaluateExpression(
                        input.expression, 'cm')
                elif input.id == 'pinCircleRadius':
                    disk.pinCircleRadius = unitsMgr.evaluateExpression(
                        input.expression, 'cm')
                elif input.id == 'numberOfPins':
                    disk.numberOfPins = input.value
                elif input.id == 'centerHoleDiameter':
                    disk.centerHoleDiameter = unitsMgr.evaluateExpression(
                        input.expression, 'cm')
                elif input.id == 'contraction':
                    disk.contraction = input.value
            disk.buildDisk()
            args.isValidResult = True
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class DiskCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class DiskCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        self.numPins = '10'
        try:
            cmd = args.command
            cmd.isRepeatable = False
            onExecute = DiskCommandExecuteHandler()
            cmd.execute.add(onExecute)
            onDestroy = DiskCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            handlers.append(onExecute)
            handlers.append(onDestroy)

            inputs = cmd.commandInputs
            inputs.addStringValueInput(
                'diskName', 'Disk Name', defaultDiskName)

            initPinRadius = adsk.core.ValueInput.createByReal(defaultPinRadius)
            inputs.addValueInput(
                'pinRadius', 'Pin Radius', 'cm', initPinRadius)

            initPinCircleRadius = adsk.core.ValueInput.createByReal(
                defaultPinCircleRadius)
            inputs.addValueInput(
                'pinCircleRadius', 'Pin Cirlce Radius', 'cm', initPinCircleRadius)

            # initNumberOfPins = adsk.core.ValueInput.createByReal(
            #    defaultNumberOfPins)
            inputs.addStringValueInput(
                'numberOfPins', 'Number of Pins', defaultNumberOfPins)

            initCenterHoleDiameter = adsk.core.ValueInput.createByReal(
                defaultCenterHoleDiameter)
            inputs.addValueInput('centerHoleDiameter',
                                 'Center Hole Radius', 'cm', initCenterHoleDiameter)

            inputs.addStringValueInput(
                'contraction', 'Contraction Value', defaultContraction)
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class Disk:
    def __init__(self):
        self._diskName = defaultDiskName
        self._pinRadius = defaultPinRadius
        self._pinCircleRadius = defaultPinCircleRadius
        self._numberOfPins = defaultNumberOfPins
        self._centerHoleDiameter = defaultCenterHoleDiameter
        self._contraction = defaultContraction

    @property
    def diskName(self):
        return self._diskName

    @diskName.setter
    def diskName(self, value):
        self._diskName = value

    @property
    def pinRadius(self):
        return self._pinRadius

    @pinRadius.setter
    def pinRadius(self, value):
        self._pinRadius = value

    @property
    def pinCircleRadius(self):
        return self._pinCircleRadius

    @pinCircleRadius.setter
    def pinCircleRadius(self, value):
        self._pinCircleRadius = value

    @property
    def numberOfPins(self):
        return self._numberOfPins

    @numberOfPins.setter
    def numberOfPins(self, value):
        self._numberOfPins = value

    @property
    def centerHoleDiameter(self):
        return self._centerHoleDiameter

    @centerHoleDiameter.setter
    def centerHoleDiameter(self, value):
        self._centerHoleDiameter = value

    @property
    def contraction(self):
        return self._contraction

    @contraction.setter
    def contraction(self, value):
        self._contraction = value

    def buildDisk(self):
        global newComp
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox('New component failed to be created',
                          'New component failed.')
            return

        # Create a new sketch on the xy plane.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        center = adsk.core.Point3D.create(0, 0, 0)

        pin_radius = self.pinRadius
        pin_circle_radius = self.pinCircleRadius
        number_of_pins = int(self.numberOfPins)
        contraction = float(self.contraction)

        # the circumference of the rolling circle needs to be exactly equal to the pitch of the pins
        # rolling circle circumference = circumference of pin circle / number of pins
        rolling_circle_radius = pin_circle_radius / number_of_pins
        reduction_ratio = number_of_pins - 1  # reduction ratio
        # base circle diameter of cycloidal disk
        cycloid_base_radius = reduction_ratio * rolling_circle_radius

        last_point = None
        line = None

        lines = []

        for angle in drange(0, (360 * reduction_ratio)/reduction_ratio, 0.5):
            x = (cycloid_base_radius + rolling_circle_radius) * cos(angle)
            y = (cycloid_base_radius + rolling_circle_radius) * sin(angle)

            point_x = x + (rolling_circle_radius - contraction) * \
                cos(number_of_pins*angle)
            point_y = y + (rolling_circle_radius - contraction) * \
                sin(number_of_pins*angle)

            if angle == 0:
                # the first point
                last_point = adsk.core.Point3D.create(point_x, point_y, 0)
            else:
                line = sketch.sketchCurves.sketchLines.addByTwoPoints(
                    last_point,
                    adsk.core.Point3D.create(point_x, point_y, 0)
                )
                last_point = line.endSketchPoint
                lines.append(line)

            app.activeViewport.refresh()

        # Add the geometry to a collection. This uses a utility function that
        # automatically finds the connected curves and returns a collection.
        curves = sketch.findConnectedCurves(lines[0])

        # Create the offset.
        dirPoint = adsk.core.Point3D.create(0, 0, 0)
        offsetCurves = sketch.offset(curves, dirPoint, pin_radius)

        # create center hole
        holes = sketch.sketchCurves.sketchCircles
        centerHole = holes.addByCenterRadius(
            center, self.centerHoleDiameter)


def run(context):
    try:
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            ui.messageBox(
                'It is not supported in current workspace, please change to MODEL workspace and try again.')
            return
        commandDefinitions = ui.commandDefinitions
        cmdDef = commandDefinitions.itemById('Cycloidal')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition(
                'Cycloidal', 'Create Cycloidal', 'Create a Cycloidal Disk.')

        onCommandCreated = DiskCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
