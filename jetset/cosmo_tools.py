__author__ = "Andrea Tramacere"

from astropy.units import  Unit as u
from astropy import cosmology 
from astropy.cosmology import Cosmology

__all__=['Cosmo']


class  Cosmo (object):


    def __init__(self,astropy_cosmo=None,DL_cm=None,verbose=False):

        _c = None

        if DL_cm is not None and astropy_cosmo is not None:
            raise  RuntimeError('Either you provide an astropy cosmology objet, or luminosity distance in cm, or nothing')

        elif astropy_cosmo is None and DL_cm is None:
           
            _c = cosmology.Planck13

        elif astropy_cosmo is not None and DL_cm is None:

            _c = astropy_cosmo

        elif astropy_cosmo is None and DL_cm is not None:

            _c=None
            if verbose is True:
                print("using cosmo without z and only DL, should be used only for galactic objects!!")
                print("z will be fixed to zero")
        else:
            raise RuntimeError('Either you provide an astropy comsology objet, or luminosity distance in cm, or nothing')


        self._c = _c
        self._DL_cm = DL_cm

    def __repr__(self):
        if self._c is not None:
            s= '%s' % self._c
        elif self._DL_cm is not None:
            x=self._DL_cm*u('cm')

            s= 'cosmology is not defined, the luminosity distance has been set to %s'%x
        else:
            s='you have to define either an astropy cosmology model or set a luminosity distance in cm'

        return s

    def get_DL_cm(self,z=None):
        if self._c is not None:
            #THIS IS FIXING THE ERROR WITH PICKLED COSMO
            #TODO open issue on astropy!
            try:
                _d= self._c.luminosity_distance( z ).to('cm').value
            except:
                _d = self._c.luminosity_distance(z)
                _d = _d.value*u(str(_d.unit))
                _d = _d.to('cm').value
        else:
            _d = self._DL_cm.value

        return _d
    
    def _serialize_model(self):
        _model = {}
        _model['_c']=self._c.to_format('yaml')
        _model['_DL_cm'] = self._DL_cm
        return   _model 
       
    def __getstate__(self):
        return  self._serialize_model()

    def __setstate__(self,state):
        astropy_cosmo=None
        DL_cm=None
        if '_c' in state.keys():
           astropy_cosmo=Cosmology.from_format(state['_c'], format='yaml')
        if '_DL_cm' in state.keys():
            DL_cm=state['_DL_cm']
        self.__init__(astropy_cosmo=astropy_cosmo,DL_cm=DL_cm)
        

    




