# The example model described in the following is simple
# there is a squre structure
# the vertical displacement of the bottom face is fixed
# and there is a vertical pressure in the top surface
# the Abaqus model is showed as follows:

# Usually, when we use Python script to build the model, we need to import the following modules:
# from abaqus import *
# from abaqusConstants import *
# from driverUtils import *

# Module abaqus contains two most important variable mdb and session which control the model. 
# Module abaqusConstants contains constant strings used in modelling
# i.e., when we defines a part using the following code:

# mdb.models['Model-1'].Part(name='part', dimensionality=THREE_D, type=DEFORMABLE_BODY)

# THREE_D indicates the part is a 3D part, DEFORMABLE_BODY indicates the part is deformable.

# Module driverUtils contains an important function executeOnCaeStartup
# this function will be execute each time we open the Abaqus
# so we need to call this function in our Python script
# Now, the header of our Python script would be like:
from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import *

executeOnCaeStartup()

# # Create parts
# First we need to create a sketch that will be used to create the part
# we need to use ConstrainedSketch() to create a sketch:
# In this code, we draw a sketch with a squre. 
model = mdb.models['Model-1']
sketch = model.ConstrainedSketch(name='sketch', sheetSize=1.0)
sketch.rectangle((0, 0), (1, 1))

#  Now we can create a part using this sketch:
# The first line creates a 3D and deformable part. 
# Then we use the BaseSolidExtrude() method to create a part using the sketch.
part = model.Part(name='part', dimensionality=THREE_D, type=DEFORMABLE_BODY)
part.BaseSolidExtrude(sketch=sketch, depth=1)

# # Create some sets for boundary conditions and loads
# Unlike building a model in Abaqus/CAE, we can just click the nodes/faces to create sets, 
# when we use a Python script to build the model, we can use coordinates to find nodes/faces we need.
# We can use Set() and Surface() to create sets and surfaces:
part.Set(name='set-all', cells=part.cells.findAt(coordinates=((0.5, 0.5, 0.5), )))
part.Set(name='set-bottom', faces=part.faces.findAt(coordinates=((0.5, 0.5, 0.0), )))
part.Set(name='set-top', faces=part.faces.findAt(coordinates=((0.5, 0.5, 1.0), )))
part.Surface(name='surface-top', side1Faces=part.faces.findAt(coordinates=((0.5, 0.5, 1.0), )))

# Merge parts to assembly
# We can use Instance() to create instances:
model.rootAssembly.DatumCsysByDefault(CARTESIAN)
model.rootAssembly.Instance(name='instance', part=part, dependent=ON)

# # Create materials and sections, and assign materials to sections
# First we create a Material object using Material():
material = model.Material(name='material')

# Then we assign some properties to the Material object, i.e., Elastic() and Density():
material.Elastic(table=((1000, 0.2), ))
material.Density(table=((2500, ), ))

# Then we create a HomogeneousSolidSection() and assign the material to the section (SectionAssignment()):
model.HomogeneousSolidSection(name='section', material='material', thickness=None)
part.SectionAssignment(region=part.sets['set-all'], sectionName='section')

# # Create steps
step = model.StaticStep(name='Step-1', previous='Initial', description='', 
                        timePeriod=1.0, timeIncrementationMethod=AUTOMATIC, 
                        maxNumInc=100, initialInc=0.01, minInc=0.001, maxInc=0.1)

# # Specify output requests
# We can use the FieldOutputRequest() and HistoryOutputRequest() to specify field output and history output information.
field = model.FieldOutputRequest('F-Output-1', createStepName='Step-1', 
                                 variables=('S', 'E', 'U'))

# # Create boundary conditions
# We can use DisplacementBC() to create a displacement boundary condition:
# It should be noted that region of the boundary condition should be a region of the instances instead of parts
# since sets created in parts are copied to the instance, we can use the sets in the parts that we defined before.
bottom_instance = model.rootAssembly.instances['instance'].sets['set-bottom']
bc = model.DisplacementBC(name='BC-1', createStepName='Initial', region=bottom_instance, u3=SET)

# # Create loads
# We can use Pressure() ro create a pressure:
top_instance = model.rootAssembly.instances['instance'].surfaces['surface-top']
pressure = model.Pressure('pressure', createStepName='Step-1', region=top_instance, magnitude=100)

# # Mesh

elem1 = mesh.ElemType(elemCode=C3D8R)
elem2 = mesh.ElemType(elemCode=C3D6)
elem3 = mesh.ElemType(elemCode=C3D4)
part.setElementType(regions=(part.cells, ), elemTypes=(elem1, elem2, elem3))
part.seedPart(size=0.1)
part.generateMesh()

# # Create jobs
# We can use Job() to create a job:
job = mdb.Job(name='Job-1', model='Model-1')

# Then we can write the model to an input file (.inp):
job.writeInput()

# Then we can submit the job:
job.submit()
job.waitForCompletion()

# # Save the Abaqus model to a .cae file
# We can use saveAs to save the Abaqus model to a .cae file:
mdb.saveAs('compression.cae')
