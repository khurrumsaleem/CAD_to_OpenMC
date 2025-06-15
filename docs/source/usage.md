# Usage

We will show a few very simple uses-cases below to get you started using CAD_to_OpenMC, starting with a simply utility script, and then some more examples showing a few of the options later.

## Simple utility script
This is the fastest way of getting up and running. A very basic script to process a file called 'geometry.step' into a geometry useful for OpenMC in the 'geometry.h5m'-file:
```python
import CAD_to_OpenMC.assembly as ab

A=ab.Assembly(['geometry.step'])
ab.mesher_config['threads']=1
ab.mesher_config['tolerance']=1e-2
ab.mesher_config['angular_tolerance']=1e-2
A.run(h5m_filename='geometry.h5m',backend='stl2')
```

This may then be included in an openmc-geometry by this snippet e.g.:
```python
import openmc
universe=openmc.DAGMCUniverse('geometry.h5m').bounded_universe(padding_distance=10)
geometry=openmc.Geometry(universe)
```
Please note that you also have to define materials according to the tags in the h5m-file for OpenMC to run, and of course create the geometry file ```geometry.step```. Some simple examples reside in the subdirectory ```examples/step_files```.

## 7 pin test case
The follwing code-snippet can now be run to explore the capabilities of Assembly/step_to_h5m. We supply a couple of example .step-files in the examples directory. In this example we'll be using a geometry with a set of 7 pin-cells.

```python
  import CAD_to_OpenMC.assembly as ab
  a=ab.Assembly()
  a.stp_files=["tests/7pin.step"]
  a.import_stp_files()
  a.solids_to_h5m()
```
as of version 0.2.6 a simpler version of this test-script may be used as we have added a small set of convenience functions. One possibility is:
```python
  import CAD_to_OpenMC.assembly as ab
  a=ab.Assembly(['tests/7pin.step'])
  a.run()
```
which will read the 7pin.step example file and output a file by the default name dagmc.h5m

as usual.

Unless anything else is specified this procedure simply uses the default CAD_to_OpenMC parameters to create meshes using the default choice of meshing backend - namely gmsh.
E.g. for the "gmsh"-backend this means sampling curves 20 times, a minimum mesh-element size of 0.1, and a maximum mesh element size of 10.
This procedure will in turn call OCP and gmsh to produce a mesh with merged surfaces in the output file "dagmc.h5m"

The other available meshing backends are based on stl-export from CadQuery (accessible by setting ```backend='stl'```, or ```backend='stl2'```) which uses the parameters ```tolerance``` and ```angular_tolerance``` to set meshing quality.
E.g. choosing the 'stl2' backend would alter the call to run to:
```python
  a.run(backend='stl2')
```
Similarly the output filename may be set using the parameter h5m_filename.

Meshing parameters are changed by means of altering entries in the ```mesher_config```-dictionary defined  in the assembly module root namespace. Like:
```python
 ab.mesher_config['min_mesh_size']=0.2
 ```

Below is a list of the available parameters and their
meanings:

<dl>
    <dt>min_mesh_size</dt>
        <dd>Minimum mesh element size (gmsh backend/mmg_refinement)</dd>
    <dt>max_mesh_size</dt>
        <dd>Maximum mesh element size (gmsh backend/mmg_refinement)</dd>
    <dt>curve_samples</dt>
        <dd>The number of point samples used to approximate a curve, 1D-mesh. (gmsh backend)</dd>
    <dt>mesh_algorithm</dt>
        <dd>Integer specifying which meshing algorithm to use (gmsh backend) 1: Adaptive algorithm - most often the most robust choice.</dd>
    <dt>vetoed</dt>
        <dd>A list of surfaces that should be excluded from meshing. Useful when some surface fails for whatever reason. Be aware that this may make your geometry non-watertight.</dd>
    <dt>threads</dt>
        <dd>The number of threads to be used to speed up the meshing algorithms. Useful for multicore-computers.</dd>
    <dt>tolerance</dt>
        <ddRelative mesh tolerance (stl/stl2 backends). Lower this to get a finer mesh.</dd>
    <dt>angular_tolerance</dt>
        <dd>Relative angular mesh tolerance (stl/stl2 backends) Lower this to get a better angular resolution.</dd>
    <dt>refine</dt>
        <dd>After the initial meshing step is done, should the mesh be refined?

This option has more than one meaning depending on which backend you have chosen.
- If the cq/stl-backend is active and the *refine* option is non-zero or True, the mesh-refinment tool (mmg)[https://www.mmgtools.org] is called in sequence on each surface.
- If the gmsh-backend is active and the *refine* option is non-zero the gmsh-refinement tool is called on the full geometry the given number of times. A value of True is the same as setting the option to 1, i.e. it triggers a single loop through the refinement algorithm.</dd>
   <dt>verbose</dt>
      <dd>Output lots of information from the mesher backends.</dd>
</dl>

As of version 0.3 We also distribute a utility script (in the scripts directory) that should be helpful in creating meshes. An example run could look like this, which furthermore sets the implicit complement to be air. (See below for more on implicit complement):
```bash
  c2omc_step2h5m tests/7pin.step --threads=1 --verbose=2 --implc=air --backend=stl2
```
For a description of all available command line options simply run
```bash
  c2omc_step2h5m --help
```
One noteable difference is that the default meshing backend is in this case 'stl2'

## meshing backends
At present four different backends exist for CAD_to_OpenMC: 'gmsh', 'stl', 'stl2', and 'db'. It is possible to add another backend should another meshing library become available.

### gmsh
The inner workings of this backend is basically a simple call to gmsh to create a 2D-mesh of the entire geometry. This has the advantage that inhenrently boundary curves are meshed only once, meaning that in theory, they can be made to account for shared surfaces without unwanted artefacts. At its present stage however there may be problems with leakage when performing transport calculation on geometries with shared surfaces. A significant drawback todoing the entire geometry all at once, is that for larger geometries memory requirements may be prohibitive.

### stl
The stl backend takes a different approach. Instead each solid object in a step geometry is triangulated on its own. The triangulation itself is performed by calls to the underlying OpenCASCADE-library through the python layer cadquery. This procedure sidesteps the problem with large geometries, as each object in handled on its own. Objects cannot overlap however, and just as the case is for the gmsh-backend, surfaces should not be coincident.

### stl2
As its name implies the stl2 backend builds on concepts from the stl backend. However a major difference lies in the fact that objects can now have coincident surfaces. This is achieved by splitting the tringulation operation further and instead perform it in a face-by-face manner. This way we may skip the operation is one face (or surface) is a part of two solids. Furthermore, when the surfaces are assembled into a h5m datafile, the surfaces may be appropriately flagged such that transport algorithms can handle moving from one to another. If this is important for your problem, then this is the backend you should use.

### db
This meshing backend is based on the DellaBella meshing algorithm. On our test cases it tends to produce meshes that are qualitatively similar to what the 'stl2'-backend will generate. In cases however it can be more reliable, and may be able to generate watertight models with less polygons, leading to smaller files.
This backend is experimental in that installation can be tricky, since it requires a very new version of cadquery-ocp (7.7.2.1), not yet available through the pip-ecosystem. It may be installed using conda/mamba, but keep in mind that you actively have to avoid reinstalling cadquery-ocp thourhg pip. This can be accomplished by means of installing the dependencies manually (look to pyproject.toml) and lastly install cad_to_openmc using ```pip install --no-deps CAD_to_OpenMC```

## tag delimiter
As of 0.3.6 it is possible to manipulate the delimiter used when extracting material tags from part names. By default the regexp used is "\s_@" meaning to split on whitespace, underscores and @. E.g. this will make parts "dr_bunsen" and "dr_beaker" be tagged with "dr". If however the method "set_tag_delim" is called on an assembly object with an argument "\s@" this results in the parts being tagged "dr_bunsen" and "dr_beaker".
```python
import CAD_to_OpenMC.assembly as ab
a=ab.Assembly()
a.set_tag_delim("\s@")
```

## implicit complement
CAD_to_OpenMC supports the notion of an implicit complement material, i.e. a material that fills all the space within the geometry which has _not_ been claimed by any part in the CAD-assembly. For instance if one wanted to submerge a pincell in in water it is possible to only define the pincell as part and set the implicit complement material to water. To do so we would use code like:
```python
import CAD_to_OpenMC.assembly as ab
a=ab.Assembly()
a.implicit_complement='water'
...
```
Of course, this means that the subsequent OpenMC transport simulation needs to define a material (with the wanted properties) named 'water'.

## Intermediate datafiles
In the process of generating an .h5m-geometry file CAD_to_OpenMC also generates a sometimes large amount of intermediary datafiles, these may be retained for debugging purposes (the default), but by setting a flag, CAD_to_OpenMC can be directed to delete them automatically once they're no longer needed. Since version 0.3 the intermediate datafiles are put in a newly created subdirectory, named <h5m_file_stem>_DATE_TIME.
The cleanup-flag is set as such:
```python
import CAD_to_OpenMC.assembly as ab
a=ab.Assembly()
a.cleanup=True
```

## Merging a set of geometries
If you have non-overlapping geometries, it can be convenient to mesh them separately, e.g. to save memory, only to merge them at a later stage. In CAD_to_OpenMC this is supported (since 0.3.1) through a utility function merge2h5m.
Imagine you have two step-files: one.step and two.step which you know to not overlap, but you would like them to belong to the same geometry/scene. In this case you may create a single h5m-file containing them both by means of the follwing procedure.
```python
import CAD_to_OpenMC.assembly as ab
One = ab.Assembly(['one.step])
One.run(backend='stl2', merge=True, h5m_filename='one.h5m')

Two = ab.Assembly(['two.step])
Two.run(backend='stl2', merge=True, h5m_filename='two.h5m')

ab.merge2h5m([One,Two],h5m_file='three.h5')
```
This will run the normal triangulization procedure for one and two separately, but also create a single h5m-file: three.h5m which contains both of the geometries.

# Advanced examples
In this section we will describe two advanced examples of real-world reactors where CAD_to_OpenMC has been used in conjunction with OpenMC (and other software) to generate results that may be compared to experimental data.
The first example is a table-top fast reactor named [GODIVA IV](https://www.tandfonline.com/doi/full/10.1080/00295639.2021.1947103), the second a model of a molten salt reactor zero-power experiment [ZPRE](https://www.osti.gov/biblio/4673343).
Note that these examples and scripts originate from different authors and therefore differ in style.

## GODIVA IV
This table-top reactor is a solid-state uranium-fueled fast reactor which is
operated with the help of fuel rods that may inserted from the bottom of the
reactor, the create "bursts" of reactivitiy. Historically its origins are a set
of GODIVA-devices so named because they are "naked". The first such devices
were assemblies of half-spherical shells of  enriched uranium. When brought
together they'd form a complete sphere close to criticality. At least in one
version the geometry included a central bore through which a uranium rod was
dropped, thus creating a short-burst of criticality.

The IV-version of this
device, which we will descrobe here, is a more controlled version with a radially symmetric geometry, and is
included in the NEA-sponsored benchmark collection: [ICBSEP](https://www.oecd-nea.org/jcms/pl_24498/international-criticality-safety-benchmark-evaluation-project-icsbep).

All scripts and necessary data may be retrieved from here: [ZENODO GODIVA VI v1](https://doi.org/10.5281/zenodo.15194864).

### Geometry conversion
The script associated with geometry conversion is very simple and listed in its entirety below:
```python
# SPDX-FileCopyrightText: (C) 2025 Erik B Knudsen
#
# SPDX-License-Identifier: BSD-3-Clause

import CAD_to_OpenMC.assembly as ab

A=ab.Assembly(['step_files/GIV_BR_detailed.step'])
B=ab.Assembly(['step_files/GIV_CR_detailed.step'])
C=ab.Assembly(['step_files/GIV_core_detailed.step'])

#fix the delimiter to keep underscores in material names
for X in (A,B,C):
	X.set_tag_delim('\s@')

#run the mesher using the 'db'-backend
A.run(backend='db', h5m_filename='GIV_BR_det.h5m')
B.run(backend='db', h5m_filename='GIV_CR_det.h5m')
C.run(backend='db', h5m_filename='GIV_core_det.h5m')
```
As noted, this script uses the 'db'-backend for surface mesh creation. Which in turn s based on the s.k. Dellabella-alogrithm.

### OpenMC-runs.
The suage example contains an object oriented approach where a reactor-object is built, which contains geometry, tallies, execution settings, etc. for OpenMC. To simply run the example with default settings, it is enough to:
```bash
python run_openmc.py
```
which will simply assemble the geometry, and do a default run. If however, you should wish to shift the control rods and/or burst rods of the reactor, this may be done by modifying line 8 of the script, i.e.:
```python
reactor = GIV_reactor('GIV_core_det.h5m', 'GIV_BR_det.h5m', 'GIV_CR_det.h5m', burst_rod_z=5.0, ctrl_rod_z=[2,2], operating_temp=800)
```

The benchmark defines 5 experimental cases, corresponding to 5 rod positions. These have been added to the model script add may be accessed by changing the instantiation-line to, e.g. for experimental case 4 (burst rod fully out, both control rods fully in):
```python
reactor = GIV_reactor('GIV_core_det.h5m', 'GIV_BR_det.h5m', 'GIV_CR_det.h5m', case=4, operating_temp=800)
```

The script additionally defines a set of general pupose tallies that mesure neutron flux as a function of spatial position or energy. Should you wish to define additional tallies please consult the [OpenMC documentation](https://docs.openmc.org).

## ZPRE
For am even more advanced example of the use of CAD_to_OpenMC and OpenMC we may
turn to the Zero Power Reactor Experiment. This was a full-scale reactor
experiment that was carried out at Oak Rodge TN in the 1960's. Copenhagen
Atomics provides a CAD-drawn model of this experiment, extracted from the
original reports and drawings from the original experiment, in the form of a
step-file. To get access simply clone the zpre github repository

```bash
git clone --branch v0.1.2 https://www.github.com/united-neux/zpre
```
or get the release from here: [ZENODO ZPRE](https://doi.org/10.5281/zenodo.15267937).

Enter the directory and run the convenience-script ```run.sh```.
The script will ask you what kind of calculation you'd like to perform.
```bash
+ PS3='ZPRE simulations: '
+ options=("k eigenvalue" "geometry plot" "geometry voxelplot" "neutron flux" "neutron flux 3d" "photon flux" "quit")
+ select opt in "${options[@]}"
1) k eigenvalue
2) geometry plot
3) geometry voxelplot
4) neutron flux
5) neutron flux 3d
6) photon flux
7) quit
ZPRE simulations:
```
If there's no surfaces meshed model to be found in the subdirectory ```h5m_files```, CAD_to_OpenMC will be run at this point. Please be aware that the settings used for this reactor requires around 20GB memory. If this is not available to you, you may e.g. edit the script to use the ```stl2```-backend instead, which is less hungry.


As a first run you might choose to ask OpenMC to simply plot the geometry of the reactor (option 2). If this is the first time you run the script, this triggers a surface-meshing operation to be performed (Be aware that by default this creates a large amount of console output - this is to be expected).
During the surface meshing operation (by default) a .vtk-file is created in addition to the .h5m-file that OpenMC (and DAGMC) needs. This is for convenience so you may inspect the created mesh using e.g. paraview, if you have access to that.
If you have paraview installed the call ```paraview h5m_files/zpre.vtk``` should yield a geometry like this ![zpre.vtk](../images/zpre_paraview.png).
The script that created the surface mesh is reproduced below.

```python
###############################################################################
# Converting step files to h5m file to be read by openmc
###############################################################################
import os
import CAD_to_OpenMC.assembly as ab
###############################################################################

# inputs
step_filepath = "./step_files/zpre.step"
compressed_path = step_filepath + ".gz"
h5m_out_filepath = os.getcwd() + '/h5m_files/zpre.h5m'

#uncompress if necessary
if not os.path.exists(step_filepath):
    os.system("gunzip -k " + compressed_path)

# mesher config
ab.mesher_config['mesh_algorithm'] = 2
ab.mesher_config['threads'] = 1
ab.mesher_config['curve_samples'] = 50
ab.mesher_config['angular_tolerance'] = 0.20
ab.mesher_config['tolerance'] = 0.3
exit()

# output
a=ab.Assembly()
a.verbose=2
a.stp_files=[step_filepath]
a.import_stp_files()
a.merge_all()
a.solids_to_h5m(backend='gmsh',h5m_filename=h5m_out_filepath)
```
Here the single step-file contains 3 distinct parts of the ZPRE-reactor, namely the core geometry, the single control-rod, and the neutron source. The source is a natural deacy driven neutron emitter, that acts as a kickstart to the fission process. Since all 3 are bundled into the same step-file and hence also the same h5m-file, positions are static.

If as indicated above option 2 (geometry plot) was chosen and the process
finished without errors, there should now be a file zpre.h5m inside the
h5m_files directory, and a set of plot_[123].png files. which correspond to
XY,XZ, and YZ-slices through the center of the reactor.
If all goes well these should look something like this:

|XY|XZ|XZ|
|:--:|:--:|:--:|
| ![plot_xy.png](../images/plot_xy.png) | ![plot_xz.png](../images/plot_xz.png) | ![plot_yz.png](../images/plot_yz.png) |

The colors are chosen arbitrarily amd automatically by the OpenMC-plotting routine, which is why the same geomtrical entity gets a different color in the slices.
```python
import matplotlib
import openmc
from materials import *

###############################################################################
#generate geometry plot of zpre (boron sleeves fully inserted)
###############################################################################

# geometry
h5m_filepath = 'h5m_files/zpre.h5m'
graveyard = openmc.Sphere(r=10000,boundary_type='vacuum')
cad_univ = openmc.DAGMCUniverse(filename=h5m_filepath,auto_geom_ids=True)
cad_cell = openmc.Cell(region=-graveyard,fill=cad_univ)
root=openmc.Universe()
root.add_cells([cad_cell])
geometry=openmc.Geometry(root)
geometry.export_to_xml()

# materials
mats = openmc.Materials([inconel,reflector,b4c,hastelloyx,stainless,brass,
                         helium,scintillator,insulation,bepo,lindsay,gold,
                         aluminum,dt,fuel,boron])
mats.export_to_xml()

#plotting geometry
plots = openmc.Plots()

x_width = 250
y_width = 250
res = 1000

#xy plot
p1 = openmc.Plot()
#p1.origin=[0,0,100]
p1.basis = 'xy'
p1.width = (x_width,y_width)
p1.pixels = (res,res)
p1.filename='plot_xy'
p1.color_by = 'material'

#xz plot
p2 = openmc.Plot()
#p2.origin=[0,0,100]
p2.basis = 'xz'
p2.width = (x_width,y_width)
p2.pixels = (res,res)
p2.filename='plot_xz'
p2.color_by = 'material'

p3 = openmc.Plot()
#p3.origin=[0,0,100]
p3.basis = 'yz'
p3.width = (x_width,y_width)
p3.pixels = (res,res)
p3.filename='plot_yz'
p3.color_by = 'material'

plots.append(p1)
plots.append(p2)
plots.append(p3)
plots.export_to_xml()

openmc.plot_geometry()
```
