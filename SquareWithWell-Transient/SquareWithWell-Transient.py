## SquareWithWell-Transient.py
# This script creates a square domain with the dimension
# 1000 m x 1000 m, with a well in the center (500,500).
# The top (y=1000) and bottom (y=0) sides of the domain 
# are no-flow boundaries, and the left (x=0) and right (x=1000)
# sides are constant head boundaries at 100 m. The well 
# pumps are a rate of 5000 m3/day for 100 days, then stops
# for 100 days.
#
# Using default units of ITMUNI=4 (days) and LENUNI=2 (meters)

import numpy as np
import flopy 
import itertools

# where is your MODFLOW-2005 executable?
path2mf = 'C:/Users/Sam/Dropbox/Work/Models/MODFLOW/MF2005.1_12/bin/mf2005.exe'

# Assign name and create modflow model object
modelname = 'SquareWithWell-Transient'
mf = flopy.modflow.Modflow(modelname, exe_name=path2mf)

# Model domain and grid definition
Lx = 1000.
Ly = 1000.
ztop = 100.
zbot = 0.
nlay = 1
nrow = 50
ncol = 100
delr = Lx / ncol
delc = Ly / nrow
delv = (ztop - zbot) / nlay
x_coord = np.linspace(delr/2, Lx-delr/2, num=ncol)
y_coord = np.linspace(Ly-delc/2, delc/2, num=nrow)
botm = np.linspace(ztop, zbot, nlay + 1)
hk = 1.
vka = 1.
sy = 0.1
ss = 1.e-4
laytyp = 1

# define boundary conditions: 1 everywhere except 
# left and right edges, which are -1
ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
ibound[:,:,(0,ncol-1)] = -1.0

# initial conditions
strt = 100. * np.ones((nlay, nrow, ncol), dtype=np.float32)

# Time step parameters
nper = 2
perlen = [100,100]
nstp = [100,100]
steady = [False,False]

# Flopy objects
dis = flopy.modflow.ModflowDis(mf, nlay, nrow, ncol, delr=delr, delc=delc,
                               top=ztop, botm=botm[1:],
                               nper=nper, perlen=perlen, nstp=nstp, steady=steady)
bas = flopy.modflow.ModflowBas(mf, ibound=ibound, strt=strt)
lpf = flopy.modflow.ModflowLpf(mf, hk=hk, vka=vka, sy=sy, ss=ss, laytyp=laytyp)
pcg = flopy.modflow.ModflowPcg(mf)

# set up pumping well
r_well = round(nrow/2)
c_well = round(ncol/2)
wel_sp1 = [[0, r_well, c_well, -1000]]
wel_sp2 = [[0, r_well, c_well, 0]]
stress_period_data = {0: wel_sp1,
                      1: wel_sp2}
wel = flopy.modflow.ModflowWel(mf, stress_period_data=stress_period_data)

# Output control
oc = flopy.modflow.ModflowOc(mf, save_every=True, compact=True)

# Write the model input files
mf.write_input()

# Run the model
success, mfoutput = mf.run_model(silent=True, pause=False, report=True)
if not success:
    raise Exception('MODFLOW did not terminate normally.')

# Imports
import matplotlib.pyplot as plt
import flopy.utils.binaryfile as bf

# Create the headfile object
headobj = bf.HeadFile(modelname+'.hds', text='head')

# get data
time = headobj.get_times()[0]
head = headobj.get_data(totim=time)
extent = (x_coord[0],x_coord[ncol-1],y_coord[0],y_coord[nrow-1])

# Well point
wpt = (float(round(ncol/2)+0.5)*delr, float(round(nrow/2)+0.5)*delc)

# plot of head
plt.subplot(2,1,1)
plt.imshow(head[0,:,:], extent=extent, cmap='BrBG')
plt.colorbar()
plt.plot(wpt[0], wpt[1], lw=0, marker='o', markersize=8,
             markeredgewidth=0.5,
             markeredgecolor='black', 
             markerfacecolor='none', 
             zorder=9)

# cross-section (L-R) of head through the well
plt.subplot(2,1,2)
plt.plot(x_coord, head[0,r_well,:])
plt.show()

# timeseries
idx = (0, r_well, c_well)
ts = headobj.get_ts(idx)
plt.subplot(1, 1, 1)
ttl = 'Head at cell ({0},{1},{2})'.format(idx[0] + 1, idx[1] + 1, idx[2] + 1)
plt.title(ttl)
plt.xlabel('time')
plt.ylabel('head')
plt.plot(ts[:, 0], ts[:, 1])
plt.show()