# encoding: utf-8

from odbAccess import*
import numpy as np
import os

# 指定odb文件所在路径
workDir = R'D:\2024spring\RM_TEST\real-sqfm'
os.chdir(workDir)

# 指定odb文件
odb_file = 'RUMEIMain1.odb'
odb = openOdb(path=odb_file)

# 指定所需读取step
step = odb.steps['Step-39']
frame = step.frames[-1]

assembly = odb.rootAssembly
instance = assembly.instances['PART-1-1']

element_set = instance.elements
node_set = instance.nodes
excludedElem_set = instance.elementSets['EBATIINVER'].elements
excluded_Element_ids = set([elem.label for elem in excludedElem_set])

Stresses = frame.fieldOutputs['S'].getSubset(region=instance, position=CENTROID)

Elements_array = np.zeros((len(element_set), 9), dtype=int)
ElemStress_data = np.zeros((len(element_set), 3))
for i, elem in enumerate(element_set):
        if elem.label not in excluded_Element_ids:
            Elements_array[i, 0:] = [elem.label, elem.connectivity[0], elem.connectivity[1], elem.connectivity[2], elem.connectivity[3], 
                            elem.connectivity[4], elem.connectivity[5], elem.connectivity[6], elem.connectivity[7]]
            stress = Stresses.getSubset(region=elem, position=CENTROID)
            for v in stress.values:
                ElemStress_data[i, 0:] = [elem.label, v.maxPrincipal, v.minPrincipal]
Elements_array = Elements_array[Elements_array[:, 1] != 0]
ElemStress_data = ElemStress_data[ElemStress_data[:, 1] != 0]

maxNodeLabel = None
for node in node_set:
    if maxNodeLabel is None or node.label > maxNodeLabel:
        maxNodeLabel = node.label

coord_array = np.zeros((maxNodeLabel, 4))
Displacement_array = np.zeros((maxNodeLabel, 4))
for node in node_set:
    index = node.label - 1
    coord = node.coordinates
    coord_array[index, 0] = node.label
    coord_array[index, 1:] = coord
    displacement = frame.fieldOutputs['U'].getSubset(region=node).values[0].data
    Displacement_array[index, 0] = node.label
    Displacement_array[index, 1:] = displacement

odb.close()

Node_tecplot_path = 'Displacements.dat'
with open(Node_tecplot_path, 'w') as file:
    file.write('TITLE = RM Rockfill Dam Displacements\n')
    file.write('VARIABLES = "XCoor", "YCoor", "ZCoor", "UX", "UY", "UZ"\n')
    file.write('ZONE N=%d, E=%d\n' % (maxNodeLabel, len(Elements_array)))
    file.write('DATAPACKING = POINT, ZONETYPE = FEBRICK\n')

    for i in range(maxNodeLabel):
        file.write("%.6f %.6f %.6f %.6f %.6f %.6f\n" 
            % (coord_array[i][1], coord_array[i][2], coord_array[i][3], 
                Displacement_array[i][1], Displacement_array[i][2], Displacement_array[i][3]))
    file.write('\n')
    for i in range(len(Elements_array)):
        file.write("%d %d %d %d %d %d %d %d\n" 
            % (Elements_array[i][1], Elements_array[i][2], Elements_array[i][3], Elements_array[i][4],
                Elements_array[i][5], Elements_array[i][6], Elements_array[i][7], Elements_array[i][8]))
print("Tecplot file created at: %s/%s" % (workDir, Node_tecplot_path))

Elem_tecplot_path = 'Stresses.dat'
with open(Elem_tecplot_path, 'w') as file:
    file.write('TITLE = RM Rockfill Dam Stresses\n')
    file.write('VARIABLES = "XCoor", "YCoor", "ZCoor", "Smax", "Smin"\n')
    file.write('ZONE N=%d, E=%d\n' % (maxNodeLabel, len(Elements_array)))
    file.write('DATAPACKING = BLOCK, ZONETYPE = FEBRICK\n')
    file.write('VARLOCATION = ([4-5] = CELLCENTERED)\n')

    for i in range(maxNodeLabel):
        file.write("%.6f\n" % (coord_array[i][1]))
    file.write('\n')
    for i in range(maxNodeLabel):
        file.write("%.6f\n" % (coord_array[i][2]))
    file.write('\n')
    for i in range(maxNodeLabel):
        file.write("%.6f\n" % (coord_array[i][3]))
    file.write('\n')
    for i in range(len(ElemStress_data)):
        file.write("%.6f\n" % (ElemStress_data[i][1]/(-1e6)))
    file.write('\n')
    for i in range(len(ElemStress_data)):
        file.write("%.6f\n" % (ElemStress_data[i][2]/(-1e6)))
    file.write('\n')
    for i in range(len(Elements_array)):
        file.write("%d %d %d %d %d %d %d %d\n" 
            % (Elements_array[i][1], Elements_array[i][2], Elements_array[i][3], Elements_array[i][4],
                Elements_array[i][5], Elements_array[i][6], Elements_array[i][7], Elements_array[i][8]))
print("Tecplot file created at: %s/%s" % (workDir, Elem_tecplot_path))