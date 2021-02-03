from PyQt5 import QtWidgets, uic, QtCore, QtGui
from pyqtgraph import PlotWidget, TextItem
import pyqtgraph as pg
import sys, os
import numpy as np
import errormodel as em
import json
from scipy.interpolate import griddata, interp1d

VERSION = '1.1'

KHZ = 2*np.pi*1e3
MHZ = 2*np.pi*1e6

SLDR_ID_GRADIENT = 0
SLDR_ID_POWER = 1
SLDR_ID_ENOISE = 2
SLDR_ID_BAMBIENT = 3
SLDR_ID_VNOISE = 4
SLDR_ID_NUXY = 5
SLDR_ID_CHI = 6
SLDR_ID_SA = 7
SLDR_ID_NBAR = 8
SLDR_ID_SYMFLUC = 9

CBOX_ARCH_ID_CHIP = 0
CBOX_ARCH_ID_MACRO = 1

CBOX_VNOISE_ID_CORR = 0
CBOX_VNOISE_ID_UNCORR = 0

C1 = '#00478F'
C2 = '#C34242'
C3 = '#FF9912'
C4 = '#3CAEA3'
COLORS = [C1, C2, C3, C4, 'k']

def resource_path(relative_path):
    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    path_to_dat = os.path.abspath(os.path.join(bundle_dir, relative_path))
    return path_to_dat
    
CHIP_PRESET_FILE = resource_path("presets\\chip_preset.json")
MACRO_PRESET_FILE = resource_path("presets\\macro_preset.json")

with open(CHIP_PRESET_FILE) as json_file:
    CHIP_PRESET_DATA = json.load(json_file)
with open(MACRO_PRESET_FILE) as json_file:
    MACRO_PRESET_DATA = json.load(json_file)
    
WINDOW_UI_FILE = resource_path('window.ui')
   
class Trace:
    
    curves = []
    errors = []
    NU_C_LIST = np.linspace(100, 500, 100)*KHZ
    hide = False
    update = False
    active = False
    point = None
    table = {"tgate" : 0, "numin" : 0, "errmin" : 1, "ndot" : 0}
    
    params = {}
    
    def __init__(self):
        return None
                
    def updateErrors(self, errors):
        self.errors = errors
        
    def updateTable(self, tgate = 0, numin = 0, errmin = 1, ndot = 0) :
        if self.update :
            self.table = {"tgate" : tgate, "numin" : numin, "errmin" : errmin, "ndot" : ndot}
    
    def plotTrace(self) :
        if self.hide : 
            for curve in self.curves : 
                curve.setData([300], [1])
            self.point.setData([300], [1])   
        elif self.update : 
            for curve, err in zip(self.curves, self.errors) :
                curve.setData(self.NU_C_LIST/KHZ, err)
            self.point.setData([self.table["numin"]/KHZ], [self.table["errmin"]])


class MainWindow(QtWidgets.QMainWindow):

            
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
               
        #Load the UI Page     
        uic.loadUi(WINDOW_UI_FILE, self)    
        self.setWindowTitle('Hydra - 1.0')         
        
        # Innitialize Traces
        self.active_trace = 0
        self.traces = [Trace(), Trace(), Trace(), Trace()]
        self.traces[self.active_trace].active = True
        self.traces[self.active_trace].update = True
        
        self.comboBoxTraceNum.currentIndexChanged.connect(lambda : self.toggle_traces())
        self.radioBtnTraceUpdate.toggled.connect(lambda : self.trace_update())
        self.radioBtnTraceHide.toggled.connect(lambda : self.trace_hide() )
        
        # Innitialize  Graph
        self.NU_C_LIST = np.linspace(100, 500, 100)*KHZ
        self.init_graph()
        
        # Innitialize all slider and their labels
        self.init_sliders()
        
        # Innitialize Radio buttons
        self.radioBtnShowOffRes.toggled.connect(lambda : self.update_offres_radio())
        self.radioBtnIncludeOffErr.toggled.connect(lambda : self.update_offres_radio())
        self.radioBtnPulseShaping.toggled.connect(lambda : self.update_offres_radio())
        self.radioBtnOptFid.toggled.connect(lambda : self.toggle_optfid_btn())
        self.radioBtnAmpNoise.toggled.connect(lambda : self.toggle_ampnoise_btn())
        self.radioBtnCCWNoise.toggled.connect(lambda : self.toggle_ccwnoise_btn())
        self.radioBtnSymFluc.toggled.connect(lambda : self.toggle_symfluc_btn())
    
        # Innitialize Table Info 
        self.tableInfo.setRowCount(4)
        self.tableInfo.setColumnCount(2)
        self.tableInfo.setItem(0,0, QtWidgets.QTableWidgetItem("Fidelity"))
        self.tableInfo.setItem(1,0, QtWidgets.QTableWidgetItem("Optimal nu"))
        self.tableInfo.setItem(2,0, QtWidgets.QTableWidgetItem("Gate Time"))
        self.tableInfo.setItem(3,0, QtWidgets.QTableWidgetItem("STR Heating Rate"))
            
        # Innitialize combo boxes
        self.comboBoxArchitecture.currentIndexChanged.connect(lambda : self.update_graph())
        self.comboBoxVNoise.currentIndexChanged.connect(lambda : self.update_graph())
        self.comboBoxVibMode.currentIndexChanged.connect(lambda : self.update_graph())
            
        # Innitialize Menubar items
        self.actionLoadChip.triggered.connect(lambda : self.load_presets(CHIP_PRESET_DATA))
        self.actionLoadMacro.triggered.connect(lambda : self.load_presets(MACRO_PRESET_DATA))
        self.actionSavePresetFile.triggered.connect(lambda : self.save_preset_file())
        self.actionLoadPresetFile.triggered.connect(lambda : self.load_preset_file())
        
        # Initialize legend and update graph
        self.init_legend()
        self.update_graph()
    
    def get_pens(self, color) :
        return [pg.mkPen(color=color, width = 2, style=QtCore.Qt.CustomDashLine, dash=[1, 2]),
                pg.mkPen(color=color, width = 2, style=QtCore.Qt.CustomDashLine, dash=[3, 12]),
                pg.mkPen(color=color, width = 2, style=QtCore.Qt.CustomDashLine, dash=[6, 6]),
                pg.mkPen(color=color, width = 2, style=QtCore.Qt.CustomDashLine, dash=[25, 4]),
                pg.mkPen(color=color, width = 2, style=QtCore.Qt.DashDotLine),
                pg.mkPen(color=color, width = 2, style=QtCore.Qt.DashDotDotLine),
                pg.mkPen(color=color, width = 3)]
    
    def trace_hide(self) :
        self.traces[self.active_trace].hide = self.radioBtnTraceHide.isChecked()
        self.traces[self.active_trace].plotTrace()
        self.update_graph()
        
    def trace_update(self) :
        self.traces[self.active_trace].update = self.radioBtnTraceUpdate.isChecked()
        self.traces[self.active_trace].plotTrace()
        self.update_graph()
        
    def toggle_traces(self) :
                
        self.traces[self.active_trace].params = self.save_presets()
        
        self.active_trace = self.comboBoxTraceNum.currentIndex()
        self.radioBtnTraceUpdate.setChecked(self.traces[self.active_trace].update)
        self.radioBtnTraceHide.setChecked(self.traces[self.active_trace].hide)
        
        if not self.traces[self.active_trace].active :
            self.traces[self.active_trace].active = True
            self.traces[self.active_trace].curves = [self.graphWidget.plot([1], [1], pen=pen) for pen in self.get_pens(COLORS[self.active_trace])]
            self.traces[self.active_trace].point = self.graphWidget.plot([0], [1], pen= pg.mkPen(None), brush = 'k', symbol = 'o')
        
        else :
            params = self.traces[self.active_trace].params
            self.load_presets(params)
            
            
    def toggle_optfid_btn(self) :
        self.sliderFixNu.setEnabled(not self.radioBtnOptFid.isChecked())
        self.update_graph()
    
    def toggle_ampnoise_btn(self) :
        self.sliderChi.setEnabled(self.radioBtnAmpNoise.isChecked())
        self.update_graph()
        
    def toggle_ccwnoise_btn(self) :
        self.sliderSA.setEnabled(self.radioBtnCCWNoise.isChecked())
        self.update_graph()
        
    def toggle_symfluc_btn(self) :
        self.sliderSymFluc.setEnabled(self.radioBtnSymFluc.isChecked())
        self.update_graph()
    
    def save_preset_file(self) :
    
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File', '', '*.json')[0]
         
        try : 
            preset_data = self.save_presets()
            
            with open(filename, 'w') as f:
                json.dump(preset_data, f)
                
        except : 
            print('Error : Save presets to file failed')
        
        
    def load_preset_file(self) :
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Load File', '', '*.json')[0]
        
        try :
            with open(filename) as f:
                preset_data = json.load(f)
            
            self.load_presets(preset_data)
        
        except : 
            print('Error : Load preset file failed')
            
            
    def save_presets(self) :
        
        dzB = self.sliderGradient.value()
        Om = self.sliderPower.value()
        nuSE = (self.sliderENoise.value()/10)
        SBa = (self.sliderBAmbient.value()/10)
        SV = (self.sliderVNoise.value()/10)
        nuXY = self.sliderNuXY.value()/10
        chi = self.sliderChi.value()/10
        SA = self.sliderSA.value()/10
        nbar = self.sliderNbar.value()/10
        sym_fluc = self.sliderSymFluc.value()
        
        arch = self.comboBoxArchitecture.currentIndex()
        vnoise = self.comboBoxVNoise.currentIndex()
        vmode = self.comboBoxVibMode.currentIndex()
        
        toggle_amp_noise = self.radioBtnAmpNoise.isChecked()
        toggle_ccw_noise = self.radioBtnCCWNoise.isChecked()
        toggle_sym_fluc = self.radioBtnSymFluc.isChecked()
        
        return {"version" : version,
                "slider" : { "dzB" : dzB, "Om" : Om, "nuSE" : nuSE, "SBa" : SBa,
                             "SV" : SV, "nuXY" : nuXY, 'chi' : chi, 'SA' : SA, 
                             'nbar' : nbar, 'symfluc' : sym_fluc},
                "toggles" : {'amp_noise' : toggle_amp_noise, 'ccw_noise' : toggle_ccw_noise, 'sym_fluc' : toggle_sym_fluc},
                "architecture" : arch,"vnoise" : vnoise,"vib_mode" : vmode}
    
    def load_presets(self, data) :
       
        self.sliderGradient.setValue(data['slider']['dzB'])
        self.labelGradient.setText(str(data['slider']['dzB']) + ' T/m')
        
        self.sliderPower.setValue(data['slider']['Om'])
        self.labelPower.setText(str(data['slider']['Om']) + ' KHz')
        
        self.sliderENoise.setValue(int(data['slider']['nuSE']*10))
        self.labelENoise.setText(str('%.2E'%(10**(data['slider']['nuSE']))))
        
        self.sliderBAmbient.setValue(int(data['slider']['SBa']*10))
        self.labelBAmbient.setText(str('%.2E'%(10**(data['slider']['SBa']))))
        
        self.sliderVNoise.setValue(int(data['slider']['SV']*10))
        self.labelVNoise.setText(str('%.2E'%(10**(data['slider']['SV']))))
        
        self.sliderNuXY.setValue(int(data['slider']['nuXY']*10))
        self.labelNuXY.setText(str(data['slider']['nuXY']) + ' MHz')
        
        self.sliderChi.setValue(int(data['slider']['chi']*10))
        self.labelChi.setText(str('%.2E'%(10**(data['slider']['chi']))))
        
        self.sliderSA.setValue(int(data['slider']['SA']*10))
        self.labelSA.setText(str('%.2E'%(10**(data['slider']['SA']))))
        
        self.sliderNbar.setValue(int(data['slider']['nbar']*10))
        self.labelNbar.setText(str('%.2f'%(10**(data['slider']['nbar']))))
        
        self.sliderSymFluc.setValue(int(data['slider']['symfluc']))
        self.labelSymFluc.setText(str(data['slider']['symfluc']))
        
        self.comboBoxArchitecture.setCurrentIndex(data['architecture'])
        self.comboBoxVNoise.setCurrentIndex(data['vnoise'])
        self.comboBoxVibMode.setCurrentIndex(data['vib_mode'])
        
        self.radioBtnAmpNoise.setChecked(data['toggles']['amp_noise'])
        self.radioBtnCCWNoise.setChecked(data['toggles']['ccw_noise'])
        self.radioBtnSymFluc.setChecked(data['toggles']['sym_fluc'])
            
        return 0
    
    def update_table(self, err_min, nu_min, tgate, ndot) :
    
        self.tableInfo.setItem(0,1, QtWidgets.QTableWidgetItem('%.3f'%((1 - err_min)*100) + ' %'))
        self.tableInfo.setItem(1,1, QtWidgets.QTableWidgetItem('%.1f'%(nu_min/KHZ) + ' KHZ'))
        self.tableInfo.setItem(2,1, QtWidgets.QTableWidgetItem('%.3f'%(tgate*1e3) + ' ms')) 
        self.tableInfo.setItem(3,1, QtWidgets.QTableWidgetItem('%.3f'%ndot))
    
    def update_offres_radio(self) :
        
        show_offres = self.radioBtnShowOffRes.isChecked()
        inc_offres_err = self.radioBtnIncludeOffErr.isChecked()
        pulse_shaping = self.radioBtnPulseShaping.isChecked()
        
        if not show_offres :
            self.radioBtnIncludeOffErr.setChecked(False)
        
        self.update_graph()
    
    def init_legend(self) :
        
        self.legendWidget.setBackground(None)
        
        pos_list  = [[[0.5, 2], [8, 8]],
                     [[0.5, 2], [2, 2]],
                     [[4.5, 6], [8, 8]],
                     [[4.5, 6], [2, 2]],
                     [[8.5, 10], [8, 8]],
                     [[8.5, 10], [2, 2]]]
                     
        for pos, pen in zip(pos_list, self.get_pens(COLORS[0])) : 
            self.legendWidget.plot(pos[0], pos[1], pen = pen)
                 
        label_names = ['Heating', 'Decoherence', 'Kerr coupling', 'Off-res', 'Amp noise', 'Trap fluc']
        text_items = [pg.TextItem(name, (0, 0, 0), anchor = (0, 0.5)) for name in label_names]
        
        pos_list = [(2.3, 8), (2.3, 2),
                    (6.3, 8), (6.3, 2),
                    (10.3, 8), (10.3, 2)]
        
        for ti, pos in zip(text_items, pos_list) :
            ti.setPos(pos[0], pos[1])
            self.legendWidget.addItem(ti)
               
        self.legendWidget.setXRange(0, 12, padding = 0)
        self.legendWidget.setYRange(0, 10, padding = 0)
        
        self.legendWidget.getPlotItem().hideAxis('bottom')
        self.legendWidget.getPlotItem().hideAxis('left')
        
        
    def init_graph(self) :
    
           
        self.graphWidget.setBackground(None)
                
        self.graphWidget.plot([self.NU_C_LIST[0]/KHZ, self.NU_C_LIST[-1]/KHZ], [1e-2, 1e-2], pen=pg.mkPen('#666666', width=1, style=QtCore.Qt.DashLine))
        self.graphWidget.plot([self.NU_C_LIST[0]/KHZ, self.NU_C_LIST[-1]/KHZ], [1e-4, 1e-4], pen=pg.mkPen('#666666', width=1, style=QtCore.Qt.DashLine))
        
        self.traces[0].curves = [self.graphWidget.plot([0], [0], pen=pen) for pen in self.get_pens(COLORS[0])]
        self.traces[0].errors = [[0], [0], [0], [0], [0], [0], [0]]
        self.traces[0].point = self.graphWidget.plot([0], [1], pen= pg.mkPen(None), brush = 'k', symbol = 'o')
        
        self.graphWidget.plot([300], [2e-1])
        self.graphWidget.plot([300], [1e-5])
        
        self.graphWidget.setLogMode(False, True)
        
        self.graphWidget.setLabel('left', 'Infidelity')
        self.graphWidget.setLabel('bottom', 'COM Frequency', 'KHZ')
        self.graphWidget.setXRange(100, 520, padding=0)
        self.graphWidget.setYRange(-5, -1, padding=0.02)
        
    
    def update_graph(self) :
        
        architecture = self.comboBoxArchitecture.currentIndex()
        if self.comboBoxVNoise.currentIndex() == CBOX_VNOISE_ID_CORR :
            if architecture is CBOX_ARCH_ID_CHIP :
                g_factor = em.G_FACTOR_CHIP
            if architecture is CBOX_ARCH_ID_MACRO :
                g_factor = em.G_FACTOR_MACRO
        else :
            g_factor = 0
            
        vib_mode = self.comboBoxVibMode.currentIndex()
        include_amp_noise = self.radioBtnAmpNoise.isChecked()
        include_ccw_noise = self.radioBtnCCWNoise.isChecked()
        include_symfluc_noise = self.radioBtnSymFluc.isChecked()
        
        show_offres = self.radioBtnShowOffRes.isChecked()
        inc_offres_err = self.radioBtnIncludeOffErr.isChecked()
        pulse_shaping = self.radioBtnPulseShaping.isChecked() and show_offres
        
        dzB = self.sliderGradient.value()
        Om = self.sliderPower.value()* KHZ
        nuSE = 10**(self.sliderENoise.value()/10)
        SBa = 10**(self.sliderBAmbient.value()/10)
        SV = 10**(self.sliderVNoise.value()/10)
        NuXY = self.sliderNuXY.value()/10*MHZ
        nbar = 10**(self.sliderNbar.value()/10)
        
        if include_amp_noise :
            chi = 10**(self.sliderChi.value()/10)
        else : chi = 0
        
        if include_ccw_noise :
            SA = 10**(self.sliderSA.value()/10)
        else : SA = 0
        
        if include_symfluc_noise :
            sym_fluc = 2*np.pi* self.sliderSymFluc.value()
        else : sym_fluc = 0
        
        err_h, err_d, err_k, err_o, err_a, err_s = em.compute_total_errors(self.NU_C_LIST, Om, dzB, nuSE, SBa, SV, NuXY, 
                                                pulse_shaping = pulse_shaping, g_factor = g_factor, 
                                                vib_mode = vib_mode, chi = chi, dx = 1e-9, SA = SA,
                                                nbar = nbar, sym_fluc = sym_fluc)
        err_tot = err_h + err_d + err_a + err_s
        
        if vib_mode is em.VIB_MODE_AXIAL_STR : err_tot += err_k
        else : err_k = [0] * len(err_k)
        
        if inc_offres_err and show_offres: err_tot += err_o
        elif not show_offres : err_o = [0]*len(err_o)  
       
        if self.radioBtnOptFid.isChecked() : 
            err_min, nu_min = em.optimizeFidelity(self.NU_C_LIST, err_tot)
        else :
            interp_func = interp1d(self.NU_C_LIST, err_tot, kind='linear')
            nu_min = self.sliderFixNu.value()*KHZ
            err_min = interp_func(nu_min)
       
        tgate = em.compute_tgate(nu_min, dzB, Om)
        
        if vib_mode is em.VIB_MODE_AXIAL_STR :
            ndot = em.ndot_STR(nu_min, nu_min*np.sqrt(3), em.DIST_ELECTRODE, nuSE)
            tgate = em.compute_tgate(nu_min*np.sqrt(3), dzB, Om)
        elif vib_mode is em.VIB_MODE_AXIAL_COM :
            ndot = em.ndot_COM(nu_min, nuSE)
            tgate = em.compute_tgate(nu_min, dzB, Om)
            
            
        self.update_table(err_min, nu_min, tgate, ndot)
        
        #self.opt_point.setData([nu_min/KHZ], [err_min])
        
        self.traces[self.active_trace].updateTable(tgate = tgate, numin = nu_min, errmin = err_min, ndot = ndot)
        self.traces[self.active_trace].updateErrors([err_h, err_d, err_k, err_o, err_a, err_s, err_tot])
        self.traces[self.active_trace].plotTrace()
        
             
    def init_sliders(self) :
        
        
        self.sliderGradient.setMinimum(25)
        self.sliderGradient.setMaximum(200)
        
        self.sliderPower.setMinimum(25)
        self.sliderPower.setMaximum(150)
        
        self.sliderENoise.setMinimum(-80)
        self.sliderENoise.setMaximum(-40)
        
        self.sliderBAmbient.setMinimum(-260)
        self.sliderBAmbient.setMaximum(-200)
        
        self.sliderVNoise.setMinimum(-200)
        self.sliderVNoise.setMaximum(-120)
        
        self.sliderNuXY.setMinimum(10)
        self.sliderNuXY.setMaximum(50)
        
        self.sliderFixNu.setMinimum(100)
        self.sliderFixNu.setMaximum(500)
        self.sliderFixNu.setValue(300)
        
        self.sliderChi.setMinimum(-40)
        self.sliderChi.setMaximum(-10)
        self.sliderChi.setValue(-20)
        
        self.sliderSA.setMinimum(-180)
        self.sliderSA.setMaximum(-60)
        
        self.sliderNbar.setMinimum(-10)
        self.sliderNbar.setMaximum(10)
        
        self.sliderSymFluc.setMinimum(0)
        self.sliderSymFluc.setMaximum(100)
           
        self.sliderGradient.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_GRADIENT))
        self.sliderPower.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_POWER))
        self.sliderENoise.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_ENOISE))
        self.sliderBAmbient.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_BAMBIENT))
        self.sliderVNoise.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_VNOISE))
        self.sliderNuXY.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_NUXY))
        self.sliderChi.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_CHI))
        self.sliderSA.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_SA))
        self.sliderNbar.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_NBAR))
        self.sliderSymFluc.valueChanged.connect(lambda : self.update_sldr_label(SLDR_ID_SYMFLUC))
        
        self.sliderFixNu.valueChanged.connect(lambda : self.update_graph())
        
        with open(CHIP_PRESET_FILE) as json_file:
            data = json.load(json_file)
            
        self.load_presets(data)
        
    def update_sldr_label(self, sldr_id = 0) :
        
        if sldr_id is SLDR_ID_GRADIENT :
            dzB = self.sliderGradient.value()
            self.labelGradient.setText(str(dzB) + ' T/m')
        
        elif sldr_id is SLDR_ID_POWER :
            Om = self.sliderPower.value()
            self.labelPower.setText(str(Om) + ' KHz')
        
        elif sldr_id is SLDR_ID_ENOISE :
            nuSE = self.sliderENoise.value()
            self.labelENoise.setText(str('%.2E'%(10**(nuSE/10))))
        
        elif sldr_id is SLDR_ID_BAMBIENT :
            SBa = self.sliderBAmbient.value()
            self.labelBAmbient.setText(str('%.2E'%(10**(SBa/10))))
        
        elif sldr_id is SLDR_ID_VNOISE :
            SV = self.sliderVNoise.value()
            self.labelVNoise.setText(str('%.2E'%(10**(SV/10))))
        
        elif sldr_id is SLDR_ID_NUXY :
            NuXY = self.sliderNuXY.value()
            self.labelNuXY.setText(str(NuXY/10) + ' MHz')
        
        elif sldr_id is SLDR_ID_CHI : 
            chi = self.sliderChi.value()
            self.labelChi.setText(str('%.2E'%(10**(chi/10))))
    
        elif sldr_id is SLDR_ID_SA : 
            SA = self.sliderSA.value()
            self.labelSA.setText(str('%.2E'%(10**(SA/10))))
            
        elif sldr_id is SLDR_ID_NBAR : 
            nbar = self.sliderNbar.value()
            self.labelNbar.setText(str('%.2f'%(10**(nbar/10))))
            
        elif sldr_id is SLDR_ID_SYMFLUC : 
            symfluc = self.sliderSymFluc.value()
            self.labelSymFluc.setText(str(symfluc))
            
        self.update_graph()

        
def main():
    app = QtWidgets.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':         
    main()
    
    