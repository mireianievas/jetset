#from __future__ import absolute_import, division, print_function

#from builtins import (bytes, str, open, super, range,
#                      zip, round, input, int, pow, object, map, zip)

__author__ = "Andrea Tramacere"


import matplotlib as mpl


try:
    from matplotlib import  pyplot as plt
except:
    try:
        from matplotlib import pylab as plt

    except:
        try:
           import  pylab as plt
        except:
            raise RuntimeError('Unable to import pylab/pyplot from matplotlib')



from matplotlib import gridspec
import numpy as np
import  os
from astropy.constants import m_e,m_p,c
import matplotlib.ticker as ticker

from collections import namedtuple

from .output import section_separator,WorkPlace

from .utils import *

__all__=['PlotSED','BasePlot','PlotPdistr','PlotSpecComp','PlotSeedPhotons','PlotSpectralMultipl']

def y_ev_transf(x):
    return x - np.log10(2.417E14)

def y_ev_transf_inv(x):
    return x + np.log10(2.417E14)



def set_mpl():
    mpl.rcParams['figure.figsize'] = [12.0, 8.0]
    mpl.rcParams['figure.dpi'] = 80
    mpl.rcParams['savefig.dpi'] = 100

    mpl.rcParams['font.size'] = '14'
    mpl.rcParams['legend.fontsize'] = 'medium'
    mpl.rcParams['figure.titlesize'] = 'medium'


class  PlotSED (object):
    def __init__(self,
                 sed_data=None,
                 model=None,
                 interactive=False,
                 plot_workplace=None,
                 title='Plot',
                 frame='obs',
                 density=False,
                 figsize=(12,8)):

        check_frame(frame)

        self.frame=frame

        self.axis_kw=['x_min','x_max','y_min','y_max']
        self.interactive=interactive

        plot_workplace=plot_workplace
        self.lines_data_list=[]
        self.lines_model_list=[]
        self.lines_res_list = []

        if self.interactive is True:
            plt.ion()
            print ('running PyLab in interactive mode')

        if plot_workplace is None:
            plot_workplace=WorkPlace()
            self.out_dir=plot_workplace.out_dir
            self.flag=plot_workplace.flag
     
        else:
            self.out_dir=plot_workplace.out_dir
            self.flag=plot_workplace.flag
        
        
            self.title="%s_%s"%(title,self.flag)

        if figsize is None:
            figsize=(10,8)

        self.fig=plt.figure(figsize=figsize)

        self.gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1])

        self.sedplot= self.fig.add_subplot(self.gs[0])
        self._add_res_plot()
        
        self.set_plot_axis_labels(density=density)
        
        #if autoscale==True:
        self.sedplot.set_autoscalex_on(True)
        self.sedplot.set_autoscaley_on(True)
        self.sedplot.set_autoscale_on(True)
        self.counter=0

        self.sedplot.grid(True,alpha=0.5)

        self.sedplot.set_xlim(6, 30)
        if frame == 'obs':
           self.sedplot.set_ylim(-20, -8)

        elif frame == 'src':
            self.sedplot.set_ylim(38, 55)
        else:
            unexpetced_behaviour()

        self.secaxy = self.sedplot.secondary_xaxis('top', functions=(y_ev_transf, y_ev_transf_inv))
        self.secaxy.set_xlabel('log(E) (eV)')

        self.resplot.set_ybound(-2,2)
        try:
            if hasattr(self.fig.canvas.manager,'toolbar'):
                self.fig.canvas.manager.toolbar.update()
        except:
            pass

        if sed_data is not None :
            self.add_data_plot(sed_data,density=density)

        if model is not  None:
            self.add_model_plot(model)
        self.counter_res=0


    def _add_res_plot(self):
        self.resplot = self.fig.add_subplot(self.gs[1], sharex=self.sedplot)

        self.lx_res = 'log($ \\nu $)  (Hz)'
        self.ly_res = 'res'

        self.resplot.set_ylabel(self.ly_res)
        self.resplot.set_xlabel(self.lx_res)

        self.add_res_zeroline()

    def clean_residuals_lines(self):
        for i in range(len(self.lines_res_list)):
            self.del_residuals_line(0)

    def clean_data_lines(self):
        
        for i in range(len(self.lines_data_list)):
            self.del_data_line(0)
    
    def clean_model_lines(self):
        for i in range(len(self.lines_model_list)):
            self.del_model_line(0)
            
            
    def list_lines(self):
        if self.lines_data_list==[] and self.lines_model_list==[]:
            pass
        else:

            for ID,plot_line in enumerate(self.lines_data_list):
                print('data',ID, plot_line.get_label())

            for ID,plot_line in enumerate(self.lines_model_list):
                print ('model',ID,  plot_line.get_label())

    def del_data_line(self,line_ID):
        if self.lines_data_list==[]:
            print  ("no lines to delete ")
        else:
            print ("removing line: ",self.lines_data_list[line_ID])
            line = self.lines_data_list[line_ID]

            for item in line:
                # This removes lines
                if np.shape(item) == ():
                    item.remove()
                else:
                    # This removes containers for data with errorbars
                    for item1 in item:
                        item1.remove()

            del self.lines_data_list[line_ID]
            #self.update_legend()
            self.update_plot()

    def del_model_line(self,line_ID):

        if self.lines_model_list==[]:
            #print  "no lines to delete "
            pass
        else:

            line=self.lines_model_list[line_ID]
            line.remove()


            del self.lines_model_list[line_ID]

            self.update_plot()
            #self.update_legend()

    def del_residuals_line(self, line_ID):
        if self.lines_res_list == []:
            # print  "no lines to delete "
            pass
        else:

            line = self.lines_res_list[line_ID]
            line.remove()

            del self.lines_res_list[line_ID]

            self.update_plot()
            #self.update_legend()

    def set_plot_axis_labels(self, density=False):
        self.lx = 'log($ \\nu $)  (Hz)'

        if self.frame == 'src':

            if density is False:
                self.ly = 'log($ \\nu L_{\\nu} $ )  (erg  s$^{-1}$)'
            else:
                self.ly = 'log($   L_{\\nu} $ )  (erg  s$^{-1}$ Hz$^{-1}$)'

        elif self.frame == 'obs':
            if density is False:
                self.ly = 'log($ \\nu F_{\\nu} $ )  (erg cm$^{-2}$  s$^{-1}$)'
            else:
                    self.ly = 'log($   F{\\nu} $ )  (erg cm$^{-2}$  s$^{-1}$ Hz$^{-1}$)'

        else:
            unexpetced_behaviour()

        self.sedplot.set_ylabel(self.ly)
        self.sedplot.set_xlabel(self.lx)


    
    def add_res_zeroline(self):
        y0 = np.zeros(2)
        x0 = [0,30]
        self.resplot.plot(x0,y0,'--',color='black')
        self.update_plot()

    def rescale(self,x_min=None,x_max=None,y_min=None,y_max=None):
        self.sedplot.set_xlim(x_min,x_max)
        self.sedplot.set_ylim(y_min,y_max)

    def rescale_res(self,x_min=None,x_max=None,y_min=None,y_max=None):
        self.resplot.set_xlim(x_min,x_max)
        self.resplot.set_ylim(y_min,y_max)
        self.update_plot()
    
    def update_plot(self):
        self.fig.canvas.draw()
        #self.sedplot.relim()
        #self.sedplot.autoscale(axis='y')
        #self.sedplot.autoscale(axis='x')
        y_s = []
        x_min = []
        x_max = []
        y_min = None
        y_max = None
        if len(self.sedplot.lines)>0:

            for l in self.sedplot.lines:
                y_s.append(np.max(l.get_ydata()))
            if len(y_s) > 0:
                y_min = min(y_s) - 3
                y_max = max(y_s) + 1
            else:
                self.sedplot.autoscale(axis='y')
            if y_min is not None and y_max is not None:
                self.sedplot.set_ylim(y_min, y_max)
                for l in self.sedplot.lines:
                    x=np.array(l.get_xdata())[np.array(l.get_ydata()) >= y_min]
                    if len(x)>0:
                        x_min.append(np.min(x))
                        x_max.append(np.max(x))
                if len(x_min)>0  and  len(x_max)>0:
                    self.sedplot.set_xlim(min(x_min) - 1, max(x_max) + 1)
        else:
            self.sedplot.relim()
            self.sedplot.autoscale(axis='y')
            self.sedplot.autoscale(axis='x')
        self.sedplot.xaxis.set_major_locator(ticker.MultipleLocator(2))
        self.update_legend()
        self.fig.tight_layout()

    def update_legend(self,label=None):

        _handles=[]

        if self.lines_data_list!=[] and self.lines_data_list is not None:
            _handles.extend(self.lines_data_list)

        if self.lines_model_list!=[] and self.lines_model_list is not None:
            _handles.extend(self.lines_model_list)

        for h in _handles[:]:
            if h._label is  None:
                _handles.remove(h)
            elif h._label.startswith('_line'):
                _handles.remove(h)
            else:
                 pass

        self.sedplot.legend(handles=_handles,loc='center left', bbox_to_anchor=(1.0, 0.5), ncol=1, prop={'size':10})




    def add_model_plot(self, model, label=None, color=None, line_style=None, flim=None,auto_label=True,fit_range=None,density=False, update=True):

        try:
            x, y = model.get_model_points(log_log=True, frame = self.frame)
        except Exception as e:
            #print("a",e)
            try:
                x, y = model.SED.get_model_points(log_log=True, frame = self.frame)
            except Exception as e:
                print("SED missing", e)
                raise RuntimeError (model, "!!! Error has no SED instance or something wrong in get_model_points()",e)

        if density is True:
            y=y-x
        if line_style is None:
            line_style = '-'

        if label is None and auto_label is True:
            if model.name is not None:
                label = model.name
            else:
                label = 'line %d' % self.counter

        if flim is not None:

            msk=y>np.log10(flim)
            x=x[msk]
            y=y[msk]
        else:
            pass

        if fit_range is not None:
            msk1 = x < fit_range[1]
            msk2 = x > fit_range[0]

            x = x[msk1 * msk2]
            y = y[msk1 * msk2]

        line, = self.sedplot.plot(x, y, line_style, label=label,color=color,linewidth=1.0)


        self.lines_model_list.append(line)

        if update is True:
            #self.update_legend()
            self.update_plot()

        self.counter += 1

    def add_data_plot(self,sed_data,label=None,color=None,autoscale=True,fmt='o',ms=4,mew=0.5,fit_range=None, density = False):


        try:
            x,y,dx,dy,=sed_data.get_data_points(log_log=True,frame=self.frame, density=density)
        except Exception as e:
            raise RuntimeError("!!! ERROR failed to get data points from", sed_data,e)
            

        if dx is None:
            dx=np.zeros(len(sed_data.data['nu_data']))
        

        if dy is None:
            dy=np.zeros(len(sed_data.data['nu_data']))

        UL = sed_data.data['UL']

        if label is None:
            if sed_data.obj_name is not None  :
                label=sed_data.obj_name
            else:
                label='line %d'%self.counter

        if fit_range is not None:
            msk1 = x < fit_range[1]
            msk2 = x > fit_range[0]

            x = x[msk1 * msk2]
            y = y[msk1 * msk2]
            dx= dx[msk1 * msk2]
            dy = dy[msk1 * msk2]
            UL=UL[msk1 * msk2]

        line = self.sedplot.errorbar(x, y, xerr=dx, yerr=dy, fmt=fmt
                                     , uplims=UL,label=label,ms=ms,mew=mew,color=color)

        self.lines_data_list.append(line)

        self.counter+=1
        #self.update_legend()
        self.update_plot()
        

    def add_xy_plot(self,x,y,label=None,color=None,line_style=None,autoscale=False):

        if line_style is None:
            line_style='-'
           

        if label is None:
            label='line %d'%self.counter

        line, = self.sedplot.plot(x, y, line_style,label=label)

        self.lines_model_list.append(line)

        self.counter+=1

        #self.update_legend()
        self.update_plot()


    def add_residual_plot(self,model,data,label=None,color=None,filter_UL=True,fit_range=None):

        if self.counter_res == 0:
            self.add_res_zeroline()
        #print('bbbbb')
        if data is not None:

            x,y=model.get_residuals(log_log=True,data=data,filter_UL=filter_UL)

            if fit_range is not None:
                msk1 = x<fit_range[1]
                msk2 =x>fit_range[0]

                x=x[msk1*msk2]
                y=y[msk1*msk2]
            #print('aaaaaaa',fit_range,x)
            line = self.resplot.errorbar(x, y, yerr=np.ones(x.size), fmt='+',color=color)
            self.lines_res_list.append(line)
            self.counter_res += 1
        else:
            pass

        self.update_plot()


    def add_text(self,lines):
        self.PLT.focus(0,0)
        x_min, x_max = self.sedplot.get_xlim()
        y_min, y_max = self.sedplot.get_ylim()
        t=''
        for line in lines:
            t+='%s \\n'%line.strip()
        self.PLT.text(t,font=10,charsize=0.6,x=x_min-1.5,y=y_min-2.85)
        self.PLT.redraw()


    def save(self,filename=None):
        if filename is None:
            wd=self.out_dir
            filename = 'jetset_fig.png'

        else:
            wd=''

        outname = os.path.join(wd,filename)
        self.fig.savefig(outname)

    def show(self):
        self.fig.show()




class BasePlot(object):

    def __init__(self,figsize=(8,6),dpi=120):
        self.fig, self.ax = plt.subplots(figsize=figsize,dpi=dpi)

    def rescale(self, x_min=None, x_max=None, y_min=None, y_max=None):
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)

    def update_plot(self):
        self.fig.canvas.draw()
        self.ax.relim()
        self.ax.autoscale(axis='y')
        self.ax.legend()
        self.fig.tight_layout()



class PlotSpectralMultipl(BasePlot):
    def __init__(self):
        super(PlotSpectralMultipl, self).__init__()

        secax = self.ax.secondary_xaxis('top', functions=(y_ev_transf, y_ev_transf_inv))
        secax.set_xlabel('log(E) (eV)')


    def plot(self,nu,y,y_label,y_min=None,y_max=None,label=None,line_style=None,color=None):

        self.ax.plot(np.log10(nu), np.log10(y),label=label,ls=line_style,color=color)
        self.ax.set_xlabel(r'log($ \nu $)  (Hz)')
        self.ax.set_ylabel(y_label)
        self.ax.set_ylim(y_min, y_max)
        self.ax.legend()
        self.update_plot()




class  PlotPdistr (BasePlot):

    def __init__(self,figsize=(8,6),dpi=120,injection=False,loglog=True):
        super(PlotPdistr, self).__init__(figsize=figsize,dpi=dpi)
        self.loglog=loglog
        self.injection = injection

    def _set_variable(self,gamma,n_gamma,particle,energy_unit,pow=None):

        energy_plot=False
        if energy_unit == 'gamma':
            energy_name = '\gamma'
            energy_units=''
        else:
            energy_name='E'
            energy_units= '%s'%energy_unit
            energy_plot=True

        if  energy_plot is False:
            x=gamma
            y=n_gamma

        else:

            if particle=='electrons':
                x = gamma*(m_e*c*c).to(energy_unit).value
                y = n_gamma * 1.0/(m_e*c*c).to(energy_unit).value
            elif particle=='protons':
                x = gamma * (m_p * c * c).to(energy_unit).value
                y = n_gamma * 1.0 / (m_p * c * c).to(energy_unit).value
            else:
                raise  RuntimeError('particle ',particle, 'not implemented')

        m = y > 0
        x=np.copy(x)
        y=np.copy(y)

        if pow is not None:
            y[m] = y[m]* np.power( x[m], pow)

        if self.loglog is True:
            x[m] = np.log10( x[m])
            y[m] = np.log10(y[m])

        return x[m], y[m], energy_name,energy_units



    def _set_xy_label(self,energy_name,energy_units,pow):
        if energy_units != '':
            _e = '(%s)' % energy_units
        else:
            _e = ''

        if self.loglog is True:
            self.ax.set_xlabel(r'log($%s$)  %s' % (energy_name, _e))
        else:
            self.ax.set_xlabel(r'$%s$  %s' % (energy_name, _e))

        if energy_units != '':
            _e = '%s^{-1}' % energy_units
        else:
            _e = ''

        n_str = 'n($%s$)'%energy_name
        if pow is not None:
            n_str = 'n($%s$) $%s^{%d}$' % (energy_name,energy_name,pow)
        if self.injection is False:

            if self.loglog is True:
                self.ax.set_ylabel(r'log(%s)   ($cm^{-3} %s$) ' % (n_str, _e))
            else:
                self.ax.set_ylabel(r'%s   ($cm^{-3} %s$) ' % (n_str, _e))
        else:
            if self.loglog is True:
                self.ax.set_ylabel(r'log(Q$_{inj}$($%s$))   ($cm^{-3} s^{-1} %s$)' % (energy_name,_e))
            else:
                self.ax.set_ylabel(r'Q$_{inj}$($%s$)   ($cm^{-3} s^{-1} %s$)' % (energy_name,_e))

    def _plot(self,x,y,c=None,lw=None,label=None):
        if self.loglog is True:
            self.ax.plot(x, y, c=c, lw=lw, label=label)
        else:
            self.ax.loglog(x, y,c=c, lw=lw, label=label)

    def plot_distr(self,gamma,n_gamma,y_min=None,y_max=None,x_min=None,x_max=None,particle='electrons',energy_unit='gamma',label=None):

        x,y,energy_name,energy_units=self._set_variable(gamma,n_gamma,particle,energy_unit)

        if label is None:
            label=particle
        self._plot(x,y,label=label)
        self._set_xy_label(energy_name,energy_units,pow=None)
        self.update_plot()
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_xlim(x_min, x_max)


    def plot_distr2p(self, gamma, n_gamma, y_min=None, y_max=None, x_min=None, x_max=None,particle='electrons',energy_unit='gamma',label=None):
        if label is None:
            label=particle

        x, y, energy_name, energy_units = self._set_variable(gamma, n_gamma, particle, energy_unit,pow=2)
        self._plot(x,y,label=label)
        self._set_xy_label(energy_name, energy_units,pow=2)
        self.update_plot()
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_xlim(x_min, x_max)

    def plot_distr3p(self,gamma,n_gamma,y_min=None,y_max=None,x_min=None,x_max=None,particle='electrons',energy_unit='gamma', label=None):
        if label is None:
            label = particle

        x, y, energy_name, energy_units = self._set_variable(gamma, n_gamma, particle, energy_unit, pow=3)
        self._plot(x,y,label=label)
        self._set_xy_label(energy_name, energy_units,pow=3)
        self.update_plot()
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_xlim(x_min, x_max)


    def update_plot(self):
        self.fig.canvas.draw()
        self.ax.relim()
        self.ax.autoscale(axis='y')
        self.ax.autoscale(axis='x')
        self.ax.legend()
        self.fig.tight_layout()


class  PlotTempEvEmitters (PlotPdistr):

    def __init__(self,figsize=(8,6),dpi=120,loglog=True):
        super(PlotTempEvEmitters, self).__init__(figsize=figsize,dpi=dpi,loglog=loglog,)


    def _plot_distr(self,temp_ev,particle='electrons',energy_unit='gamma',pow=None,plot_Q_inj=True):
        for ID in range(1, temp_ev.parameters.NUM_SET.val - 1):
            x, y, energy_name, energy_units = self._set_variable(temp_ev.gamma, temp_ev.N_gamma[ID], particle, energy_unit, pow=pow)
            self._plot(x,y,c='g',lw=0.1,label=None)
        #print('==> a')
        x, y, energy_name, energy_units = self._set_variable(temp_ev.gamma, temp_ev.N_gamma[0], particle, energy_unit, pow=pow)
        self._plot(x, y, c='black', lw=2,label='Start')
        #print('==> b')
        x, y, energy_name, energy_units = self._set_variable(temp_ev.gamma, temp_ev.N_gamma[-1], particle, energy_unit, pow=pow)
        self._plot(x, y, c='blue', lw=2,label='Stop')
        self._set_xy_label(energy_name, energy_units,pow=pow)
        #print('==> c')
        y = temp_ev.Q_inj.n_gamma_e * temp_ev._temp_ev.deltat
        x = temp_ev.Q_inj.gamma_e
        if plot_Q_inj is True:
            if pow is not None:
                y=y*np.power(x,pow)

            self._plot(x,y, c='red', lw=1, label='$Q_{inj}$ deltat')
        #print('==> d')

        self.ax.legend()

    def plot_distr(self, temp_ev, energy_unit='gamma',plot_Q_inj=True,pow=None):
        self._plot_distr(temp_ev,particle='electrons',energy_unit=energy_unit,pow=pow,plot_Q_inj=plot_Q_inj)

    def plot_distr2p(self, temp_ev, energy_unit='gamma',plot_Q_inj=True):
        self._plot_distr(temp_ev,particle='electrons',energy_unit=energy_unit,pow=2,plot_Q_inj=plot_Q_inj)

    def plot_distr3p(self, temp_ev, energy_unit='gamma',plot_Q_inj=True):
        self._plot_distr(temp_ev,particle='electrons',energy_unit=energy_unit,pow=3,plot_Q_inj=plot_Q_inj)

class  PlotTempEvDiagram (BasePlot):

    def __init__(self,figsize=(8,6),dpi=120):
        super(PlotTempEvDiagram, self).__init__(figsize=figsize,dpi=dpi)


    def plot(self,duration,T_acc_start,T_acc_stop,T_inj_start,T_inj_stop):
        self.ax.hlines(1, T_acc_start, T_acc_stop, label='Inj. start/stop', colors='b')
        self.ax.hlines(2, T_inj_start, T_inj_stop, label='Acc. start/stop', colors='g')
        self.ax.hlines(0, 0, duration, label='duration', colors='black')
        self.ax.set_xlim(-0.5, duration)
        self.ax.set_ylim(-0.5,3)
        self.ax.legend()



class  PlotSpecComp (BasePlot):

    def __init__(self):
        super(PlotSpecComp, self).__init__()

    def plot(self,nu,nuFnu,y_min=None,y_max=None):

        self.ax.plot(np.log10(nu), np.log10(nuFnu))
        self.ax.set_xlabel(r'log($ \nu $)  (Hz)')
        self.ax.set_ylabel(r'log($ \nu F_{\nu} $ )  (erg cm$^{-2}$  s$^{-1}$)')
        self.ax.set_ylim(y_min, y_max)
        self.update_plot()



class  PlotSeedPhotons (BasePlot):

    def __init__(self):
        super(PlotSeedPhotons, self).__init__()

    def plot(self,nu,nuFnu,y_min=None,y_max=None):

        self.ax.plot(np.log10(nu), np.log10(nuFnu))
        self.ax.set_xlabel(r'log($ \nu $)  (Hz)')
        self.ax.set_ylabel(r'log(n )  (photons cm$^{-3}$  Hz$^{-1}$  ster$^{-1}$)')
        self.ax.set_ylim(y_min, y_max)
        self.update_plot()
