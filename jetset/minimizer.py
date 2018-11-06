

"""
===================================================================
Module: minimizer
===================================================================

This module contains all the classes necessary to estimate the phenomenlogical
characterization of the SED, such as spectral indices, peack frequenicies
and fluxes




Classes and Inheritance Structure
-------------------------------------------------------------------

.. inheritance-diagram:: BlazarSEDFit.minimizer
   


Classes relations
----------------------------------------------

.. figure::  classes_minimizer.png
   :align:   center     


  

.. autosummary::
    

   fit_SED
   eval_SED
   residuals_SED
   
    
Module API
-------------------------------------------------------------------

"""

from __future__ import absolute_import, division, print_function

from builtins import (bytes, str, open, super, range,
                      zip, round, input, int, pow, object, map, zip)

__author__ = "Andrea Tramacere"

from itertools import cycle


import scipy as sp

import numpy as np

import os

import sys

from scipy.stats import chi2

import iminuit
#from iminuit.frontends import ConsoleFrontend
#from iminuit.frontends import console

from scipy.optimize import leastsq

from scipy.optimize import least_squares,curve_fit

from leastsqbound.leastsqbound import  leastsqbound


from .output import section_separator,WorkPlace,makedir





__all__=['FitResults','fit_SED','Minimizer','LSMinimizer','LSBMinimizer','MinutiMinimizer','ModelMinimizer']





class FitResults(object):
    """
    Class to store the fit results 
    
    Parameters
     
    
    Members
    :ivar fit_par: fit_par
    :ivar info: info
    :ivar mesg: mesg
    :ivar success: success
    :ivar chisq: chisq
    :ivar dof: dof
    :ivar chisq_red: chisq_red
    :ivar null_hyp_sig: null_hyp_sig
    :ivar fit_report: ivar get_report()
    -------
    
    """
    
    def __init__(self,name,
                 parameters,
                 calls,
                 mesg,
                 success,
                 chisq,
                 dof,
                 chisq_red,
                 null_hyp_sig,
                 wd,
                 chisq_no_UL=None,
                 dof_no_UL=None,
                 chisq_red_no_UL=None,
                 null_hyp_sig_no_UL=None):

        self.name=name
        self.parameters=parameters
        self.calls=calls
        self.mesg=mesg
        self.success=success
        self.chisq=chisq
        self.dof=dof
        self.chisq_red=chisq_red
        self.null_hyp_sig=null_hyp_sig

        self.chisq_no_UL = chisq_no_UL
        self.dof_no_UL = dof_no_UL
        self.chisq_red_no_UL = chisq_red_no_UL
        self.null_hyp_sig_no_UL = null_hyp_sig_no_UL

        self.fit_report=self.get_report()
        self.wd=wd
         

    def get_report(self):
        out=[]
        out.append("")        
        out.append("**************************************************************************************************")
        out.append("Fit report")
        out.append("")
        out.append("Model: %s"%self.name)
        pars_rep=self.parameters.show_pars(getstring=True)
        for string in pars_rep:
            out.append(string)
        
        out.append("")
        out.append("converged=%s"%self.success)
        out.append("calls=%d"%self.calls)
        out.append("mesg=%s"%self.mesg)
        out.append("dof=%d"%self.dof)
        out.append("chisq=%f, chisq/red=%f null hypothesis sig=%f"%(self.chisq,self.chisq_red,self.null_hyp_sig))
        if self.dof_no_UL is not None:
            out.append("")
            out.append("stats without the UL")
            out.append("dof  UL=%d" % self.dof_no_UL)
            out.append(
                "chisq=%f, chisq/red=%f null hypothesis sig=%f" % (self.chisq_no_UL, self.chisq_red_no_UL, self.null_hyp_sig_no_UL))
            out.append("")
        out.append("")
        out.append("best fit pars")
        
        pars_rep=self.parameters.show_best_fit_pars(getstring=True)
        for string in pars_rep:
            out.append(string)
            
        #for pi in range(len(self.fit_par)):
            #print pi,covar
        #    out.append("par %2.2d, %16s"%(pi,self.fit_par[pi].get_bestfit_description()))  
        #out.append("-----------------------------------------------------------------------------------------")
        out.append("**************************************************************************************************")    
        out.append("")
        return out
        
    
    def show_report(self):
        for text in self.fit_report:
        
            print (text)
    
    def save_report(self,wd=None,name=None):
        if wd is None:
            wd=self.wd
        
        if name is None:
            name='best_fit_report_%s'%self.name+'.txt'
        
            
        outname='%s/%s'%(wd,name)
         
        outfile=open(outname,'w')
    
        
        for text in self.fit_report:
        
            print(text,file=outfile)
            
        outfile.close()










class ModelMinimizer(object):


    def __init__(self,minimizer_type):
        __accepted__ = ['leastsqbound', 'minuit', 'least_squares']


        if minimizer_type == 'leastsqbound':
            self.minimizer=LSBMinimizer(self)

        elif minimizer_type=='least_squares':
            self.minimizer=LSMinimizer(self)

        elif minimizer_type=='minuit':
            self.minimizer=MinutiMinimizer(self)

        elif minimizer_type not in __accepted__:
            raise RuntimeError('minimizer ', minimizer_type, 'not accepted, please choose among', __accepted__)

        else:
            raise RuntimeError('minimizer factory failed')

        print('minimizer',minimizer_type)


    def _prepare_fit(self,fit_Model,SEDdata,nu_fit_start,nu_fit_stop,fitname=None,fit_workplace=None,loglog=False,silent=False,get_conf_int=False,use_facke_err=False,use_UL=False):

        if fitname is None:
            fitname = fit_Model.name + '_' + WorkPlace.flag


        if fit_workplace is None:
            fit_workplace = WorkPlace()
            out_dir = fit_workplace.out_dir + '/' + fitname + '/'
        else:
            out_dir = fit_workplace.out_dir + '/' + fitname + '/'

        makedir(out_dir)

        for model in fit_Model.components:
            if model.model_type == 'jet':
                model.set_path(out_dir)

        if SEDdata.data['dnuFnu_data'] is None:
            SEDdata.data['dnuFnu_data'] = np.ones(SEDdata.data['nu_data'].size)

        # filter data points
        msk1 = SEDdata.data['nu_data'] > nu_fit_start
        msk2 = SEDdata.data['nu_data'] < nu_fit_stop
        msk_zero_error = SEDdata.data['dnuFnu_data'] > 0.0
        # msk = s.array([(el>nu_fit_start) and (el<nu_fit_stop) for el in SEDdata.data['nu_data']])
        # print msk1.size,msk2.size,SEDdata.data['UL'].size
        if use_UL == True:
            msk = msk1 * msk2 * msk_zero_error

        else:
            msk = msk1 * msk2 * msk_zero_error*~SEDdata.data['UL']

        UL = SEDdata.data['UL'][msk]

        if loglog == False:
            nu_fit = SEDdata.data['nu_data'][msk]
            nuFnu_fit = SEDdata.data['nuFnu_data'][msk]
            if use_facke_err == False:
                err_nuFnu_fit = SEDdata.data['dnuFnu_data'][msk]
            else:
                err_nuFnu_fit = SEDdata.data['dnuFnu_facke'][msk]
        else:
            nu_fit = SEDdata.data['nu_data_log'][msk]
            nuFnu_fit = SEDdata.data['nuFnu_data_log'][msk]
            err_nuFnu_fit = SEDdata.data['dnuFnu_data_log'][msk]
            if use_facke_err == False:
                err_nuFnu_fit = SEDdata.data['dnuFnu_data_log'][msk]
            else:
                err_nuFnu_fit = SEDdata.data['dnuFnu_facke_log'][msk]


        if silent == False:
            print("filtering data in fit range = [%e,%e]" % (nu_fit_start, nu_fit_stop))
            print("data length", nu_fit.size)

        # print nu_fit,len(nu_fit)

        # set starting value of parameters
        for par in fit_Model.parameters.par_array:
            if get_conf_int == True:
                par.set_fit_initial_value(par.best_fit_val)
            else:
                par.set_fit_initial_value(par.val)

        fit_par_free = [par for par in fit_Model.parameters.par_array if par.frozen == False]

        pinit = [par.get_fit_initial_value() for par in fit_par_free]

        # bounds
        free_pars = 0

        for pi in range(len(fit_Model.parameters.par_array)):

            if fit_Model.parameters.par_array[pi].frozen == False:
                free_pars += 1

        if silent == False:
            print(section_separator)
            print("*** start fit process ***")
            print("initial pars: ")

            fit_Model.parameters.show_pars()


        self.out_dir=out_dir
        self.pinit=pinit
        self.free_pars=free_pars
        self.fit_par_free=fit_par_free
        self.nu_fit=nu_fit
        self.nuFnu_fit=nuFnu_fit
        self.err_nuFnu_fit=err_nuFnu_fit
        self.fit_Model=fit_Model
        self.loglog=loglog
        self.UL=UL

    def fit(self,fit_Model,
            SEDdata,
            nu_fit_start,
            nu_fit_stop,
            fitname=None,
            fit_workplace=None,
            loglog=False,
            silent=False,
            get_conf_int=False,
            max_ev=0,
            use_facke_err=False,
            use_UL=False,
            skip_minimizer=False):

        self._prepare_fit( fit_Model, SEDdata, nu_fit_start, nu_fit_stop, fitname=fitname, fit_workplace=fit_workplace,
                     loglog=loglog, silent=silent, get_conf_int=get_conf_int, use_facke_err=use_facke_err,use_UL=use_UL)


        if skip_minimizer == False:
            self.minimizer.fit(self,max_ev=max_ev,use_UL=use_UL)
        else:
            pass


        return self.get_fit_results(fit_Model,nu_fit_start,nu_fit_stop,fitname,loglog=loglog,silent=silent)

    def get_fit_results(self, fit_Model, nu_fit_start, nu_fit_stop, fitname, silent=False, loglog=False):
        for pi in range(len(self.fit_par_free)):
            self.fit_par_free[pi].set(val=self.minimizer.pout[pi])
            self.fit_par_free[pi].best_fit_val = self.minimizer.pout[pi]
            self.fit_par_free[pi].best_fit_err = self.minimizer.errors[pi]
        best_fit = FitResults(fitname,
                              fit_Model.parameters,
                              self.minimizer.calls,
                              self.minimizer.mesg,
                              self.minimizer.success,
                              self.minimizer.chisq,
                              self.minimizer.dof,
                              self.minimizer.chisq_red,
                              self.minimizer.null_hyp_sig,
                              self.out_dir,
                              chisq_no_UL=self.minimizer.chisq_no_UL,
                              dof_no_UL=self.minimizer.dof_no_UL,
                              chisq_red_no_UL=self.minimizer.chisq_red_no_UL,
                              null_hyp_sig_no_UL=self.minimizer.null_hyp_sig_no_UL)

        if silent == False:
            best_fit.show_report()

        fit_Model.set_nu_grid(nu_min=nu_fit_start, nu_max=nu_fit_stop)
        fit_Model.eval(fill_SED=True, loglog=loglog, phys_output=True)

        res_bestfit = self.minimizer.residuals_Fit(self.minimizer.pout,
                                                 self.fit_par_free,
                                                 self.nu_fit,
                                                 self.nuFnu_fit,
                                                 self.err_nuFnu_fit,
                                                 self.fit_Model,
                                                 self.loglog,
                                                 self.UL)

        if loglog == True:
            fit_Model.SED.fill(nu_residuals=np.power(10, self.nu_fit), residuals=res_bestfit)
        else:
            fit_Model.SED.fill(nu_residuals=self.nu_fit, residuals=res_bestfit)


        if silent == False:
            print(section_separator)

        return best_fit



class Minimizer(object):

    def __init__(self,model):
        self.model=model
        self._progress_iter = cycle(['|', '/', '-', '\\'])

    def fit(self,model,max_ev=None,use_UL=False):
        self.use_UL = use_UL
        self.calls=0
        self.res_check=None
        self.molde=model
        self._fit(max_ev,use_UL=use_UL)
        self._fit_stats()
        self._set_fit_errors()



    def _fit_stats(self):
        self.dof = len(self.model.nu_fit) - self.model.free_pars
        self.chisq = self.get_chisq()
        self.chisq_red = self.chisq / float(self.dof)
        self.null_hyp_sig = 1.0 - chi2.cdf(self.chisq, self.dof)
        if self.use_UL==True:
            self.dof_no_UL = len(self.model.nu_fit) - self.model.free_pars - self.model.UL.sum()
            self.use_UL=False
            self.chisq_no_UL = self.get_chisq()
            self.use_UL = True
            self.chisq_red_no_UL = self.chisq_no_UL / float(self.dof_no_UL)
            self.null_hyp_sig_no_UL=1.0 - chi2.cdf(self.chisq_no_UL, self.dof_no_UL)
        else:
            self.dof_no_UL = None
            self.chisq_red_no_UL = None
            self.chisq_no_UL=None
            self.null_hyp_sig_no_UL=None
        self.success = True
        self.status = 1

    def _set_fit_errors(self):
        if self.covar is None:
            print("!Warning, no covariance matrix produced")
            self.errors = np.zeros(len(self.pout))
        else:
            self.errors = [np.sqrt(np.fabs(self.covar[pi, pi]) * self.chisq_red) for pi in range(len(self.model.fit_par_free))]



    def _UL_likelihood(self,y_UL,y_model,y_err):
        y = (y_UL - y_model) / (np.sqrt(2) *y_err)
        #print('->,log arg',y,sp.special.erf(y))
        x=0.5*(1.0+sp.special.erf(y))
        x[x==0]=1E-200
        return  np.log(x)

    def _progess_bar(self, _res_sum, res_UL):
        if np.mod(self.calls, 10) == 0 and self.calls != 0:
            print("\r%s minim function calls=%d, chisq=%f UL part=%f" % (next(self._progress_iter),self.calls, _res_sum, -2.0*np.sum(res_UL)), end="")



    def residuals_Fit(self,p, fit_par, nu_data, nuFnu_data, err_nuFnu_data, best_fit_SEDModel, loglog,UL,chisq=False,use_UL=False):
        #hide_cursor()

        _warn=False
        for pi in range(len(fit_par)):
            fit_par[pi].set(val=p[pi])
            if np.isnan(p[pi]):
                _warn=True
                print('warning nan for par',pi,' old paramter value was',self._par_check[pi])

        if _warn==True:
            best_fit_SEDModel.show_pars()
            print('res_sum',self._res_sum_chekc)
            print('res_chekc', self._res_chekc)
            print('res_UL_chekc', self._res_UL_chekc)


        model = best_fit_SEDModel.eval(nu=nu_data, fill_SED=False, get_model=True, loglog=loglog)

        res_no_UL = (nuFnu_data[~UL] - model[~UL]) / (err_nuFnu_data[~UL])

        res_UL=[0]
        if UL.sum()>0 and use_UL == True:
            res_UL=self._UL_likelihood(nuFnu_data[UL],model[UL],err_nuFnu_data[UL])



        _res=(nuFnu_data  - model ) / (err_nuFnu_data )


        _res_sum = np.sum(res_no_UL * res_no_UL) - 2.0*np.sum(res_UL)

        self._res_sum_chekc=_res_sum
        self._res_chekc = _res
        self._res_UL_chekc = res_UL
        self._par_check=p

        self.calls +=1


        self._progess_bar(_res_sum, res_UL)
        print("\r", end="")

        if chisq==True:
            res=_res_sum
        else:
            res=_res

        #print('res', res, chisq,use_UL)
        #show_cursor()

        return res





class LSBMinimizer(Minimizer):

    def __init__(self, model):
        super(LSBMinimizer, self).__init__(model)

    def _fit(self, max_ev,use_UL=False):
        bounds = [(par.fit_range_min, par.fit_range_max) for par in self.model.fit_par_free]

        pout, covar, info, mesg, success = leastsqbound(self.residuals_Fit,
                                                        self.model.pinit,
                                                        args=(self.model.fit_par_free,
                                                              self.model.nu_fit,
                                                              self.model.nuFnu_fit,
                                                              self.model.err_nuFnu_fit,
                                                              self.model.fit_Model,
                                                              self.model.loglog,
                                                              self.model.UL),
                                                        xtol=5.0E-8,
                                                        ftol=5.0E-8,
                                                        full_output=1,
                                                        bounds=bounds,
                                                        maxfev=max_ev)

        self.mesg = mesg
        self.covar = covar
        self.chisq =  sum(info["fvec"] * info["fvec"])

        self.pout = pout

    def get_chisq(self):
        return self.chisq


class LSMinimizer(Minimizer):

    def __init__(self,model ):
        super(LSMinimizer, self).__init__(model)


    def _fit(self,max_ev,use_UL=False):
        bounds = ([-np.inf if par.fit_range_min is None else par.fit_range_min for par in self.model.fit_par_free],
                  [np.inf if par.fit_range_max is None else par.fit_range_max for par in self.model.fit_par_free])



        fit = least_squares(self.residuals_Fit,
                            self.model.pinit,
                            args=(self.model.fit_par_free,
                                  self.model.nu_fit,
                                  self.model.nuFnu_fit,
                                  self.model.err_nuFnu_fit,
                                  self.model.fit_Model,
                                  self.model.loglog,
                                  self.model.UL),

                            xtol=1.0E-8,
                            ftol=1.0E-8,
                            jac='3-point',
                            loss='cauchy',
                            f_scale=0.01,
                            bounds=bounds,
                            max_nfev=None if max_ev == 0 else max_ev,
                            verbose=2)

        self.covar=np.linalg.inv(2 * np.dot(fit.J.T, fit.J))
        self.chisq=sum(fit.fun * fit.fun)
        self.mesg = fit.message
        self.pout = fit.x

    def get_chisq(self):
        return self.chisq




class MinutiMinimizer(Minimizer):

    def __init__(self,model):

        super(MinutiMinimizer, self).__init__(model)



    def _fit(self,max_ev=None,use_UL=False):
        bounds = [(par.fit_range_min, par.fit_range_max) for par in self.model.fit_par_free]
        self._set_minuit_func(self.model.pinit, bounds)
        max_nfev = 10000 if (max_ev == 0 or max_ev == None) else max_ev
        self.minuit_fun.migrad(ncall=max_nfev)
        self.pout = [self.minuit_fun.values[k] for k in self.minuit_fun.values.keys()]
        self.mesg = ''

    def _set_fit_errors(self):
        self.errors = [self.minuit_fun.errors[k] for k in self.minuit_fun.errors.keys()]





    def _set_minuit_func(self, p_init, bounds):
        p_names = ['par_{}'.format(_) for _ in range(len(p_init))]
        p_bound_names = ['limit_par_{}'.format(_) for _ in range(len(p_init))]
        kwdarg = {}
        for n, p, bn, b in zip(p_names, p_init, p_bound_names, bounds):
            kwdarg[n] = p
            kwdarg[bn] = b

        #print('dict', kwdarg)

        self.minuit_fun = iminuit.Minuit(
            fcn=self.chisq_func,
            forced_parameters=p_names,
            pedantic=False,
            **kwdarg,
            frontend=None)

    def chisq_func(self, *p):
        self.p = p
        return self.residuals_Fit(p,
                          self.model.fit_par_free,
                          self.model.nu_fit,
                          self.model.nuFnu_fit,
                          self.model.err_nuFnu_fit,
                          self.model.fit_Model,
                          self.model.loglog,
                          self.model.UL,
                          chisq=True,
                          use_UL=self.use_UL)



    def get_chisq(self):
        #print ('p',self.p)
        return self.chisq_func(*self.p)


def fit_SED(fit_Model, SEDdata, nu_fit_start, nu_fit_stop, fitname=None, fit_workplace=None, loglog=False, silent=False,
            get_conf_int=False, max_ev=0, use_facke_err=False, minimizer='minuit', use_UL=False):
    mm = ModelMinimizer(minimizer)
    return mm.fit(fit_Model,
                  SEDdata,
                  nu_fit_start,
                  nu_fit_stop,
                  fitname=fitname,
                  fit_workplace=fit_workplace,
                  loglog=loglog,
                  silent=silent,
                  get_conf_int=get_conf_int,
                  max_ev=max_ev,
                  use_facke_err=use_facke_err,
                  use_UL=use_UL)
