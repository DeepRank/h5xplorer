import numpy as np
import h5py

f5 = h5py.File('basemap.hdf5','w')

for imap in range(10):

	nlats = 2*np.random.randint(25,50)+1
	nlons = 2*nlats + 1


	delta = 2.*np.pi/(nlons-1)
	lats = (0.5*np.pi-delta*np.indices((nlats,nlons))[0,:,:])
	lons = (delta*np.indices((nlats,nlons))[1,:,:])



	aW = np.random.rand()
	f1W = np.random.randint(6)
	f2W = np.random.randint(6)
	pW = np.random.randint(8)
	wave = aW*(np.sin(f1W*lats)**pW * np.cos(f2W*lons))

	aM= np.random.rand()
	f1M = np.random.randint(6)
	f2M = np.random.randint(6)
	pM = np.random.randint(4)
	mean = aM*np.cos(f1M*lats)*((np.sin(f2M*lats))**pM + 2.)

	grpname = 'map_%03d' %imap
	grp = f5.create_group(grpname)
	grp.create_dataset('mean',data=mean)
	grp.create_dataset('wave',data=wave)

f5.close()

