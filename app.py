from math import exp
import qdarkstyle
from mainGUI import Ui_MainWindow
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QSlider
import pyqtgraph as pg
from pyqtgraph import *
import numpy as np
import pathlib
from scipy import fft
from UliEngineering.SignalProcessing.Simulation import sine_wave
from scipy.interpolate import make_interp_spline
from scipy.signal import find_peaks


class mainApp(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(mainApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.showIcon = QtGui.QIcon()
        self.showIcon.addPixmap(QtGui.QPixmap(".\\icons/show.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.hideIcon = QtGui.QIcon()
        self.hideIcon.addPixmap(QtGui.QPixmap(".\\icons/hide.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)

        self.FileName = ""
        self.ui.fsSlider.setMinimum(0)

        self.redPen = pg.mkPen(color=(255,0,0))
        self.greenPen = pg.mkPen(color=(0,255,0))
        self.bluePen = pg.mkPen(color=(0,0,255))

        self.signalsList = []
        self.signalsListYValues = []
        self.pens = [self.redPen, self.greenPen, self.bluePen]

        self.signalComposerCompinedSignalsX = np.linspace(0,2,1000)
        self.singleSignalX = np.linspace(0,2,1000)
        self.signalComposerCompinedSignalsY = [0]*1000
        self.showHideFlag = True

        self.singleSinPlotter = self.ui.singleSinGraph.plot([],[],pen = self.pens[0])
        self.composeredSignalPlotter = self.ui.composedSignalGraph.plot([],[],pen = self.pens[1])

        self.ui.frequencyInputValue.valueChanged.connect(lambda: self.updateSingleSignal())
        self.ui.magnitudeInputValue.valueChanged.connect(lambda: self.updateSingleSignal())
        self.ui.phaseInputValue.valueChanged.connect(lambda: self.updateSingleSignal())


        self.ui.addBtn.clicked.connect(lambda: self.addSignal())
        self.ui.removeBtn.clicked.connect(lambda: self.removeSignal())
        self.ui.clearAllBtn.clicked.connect(lambda: self.clearAll())
        self.ui.showHideBtn.clicked.connect(lambda: self.showOrHide())
        self.ui.readBtn.clicked.connect(lambda: self.read_file())
        self.ui.finishBtn.clicked.connect(lambda: self.moveSignal())
        self.ui.reconstructBtn.clicked.connect(lambda: self.reconstructSignal())
        self.ui.fsSlider.valueChanged.connect(lambda: self.sampleSignal())
        self.ui.saveBtn.clicked.connect(lambda: self.save())
        self.ui.openSignalComposerTapBtn.clicked.connect(lambda: self.openSignalComposerTab())

        self.mainSignalDataPlotter = self.ui.mainSignal.plot([], [])
        self.sampledPointsPlotter = self.ui.mainSignal.plot([], [], pen = None, symbol='o')

        self.ui.reconstructedSignal.addLegend(offset=(-30, 1))

        self.reconstructedPointsPlotter = self.ui.reconstructedSignal.plot([], [], pen = None, symbol='o', name = 'Points')
        self.reconstructedSignalPlotter = self.ui.reconstructedSignal.plot([], [], name = 'Signal')



    def read_file(self):

        path = QFileDialog.getOpenFileName()[0]
        self.FileName= os.path.basename(path)

        if pathlib.Path(path).suffix == ".csv":
            self.data = np.genfromtxt(path, delimiter=',')
            self.xAxisValuesOfOriginalSignal = list(self.data[:, 1])
            self.yAxisValuesOfOriginalSignal = list(self.data[:, 2])

        self.load()

    def moveSignal(self):
        self.xAxisValuesOfOriginalSignal = self.signalComposerCompinedSignalsX
        self.yAxisValuesOfOriginalSignal = self.signalComposerCompinedSignalsY
        self.load()

    def load(self):
        self.mainSignalDataPlotter.setData(self.xAxisValuesOfOriginalSignal,self.yAxisValuesOfOriginalSignal)
        self.fmax()

    def fmax(self):

        numberOfPoints = np.size(self.yAxisValuesOfOriginalSignal)
        freq = np.linspace(0, numberOfPoints, numberOfPoints)
        fourier = np.fft.fft(self.yAxisValuesOfOriginalSignal)
        fourier_magnitude = abs(fourier[0:int(numberOfPoints/2)])

        peaks = find_peaks(fourier_magnitude,height = 1)

        fMax = int(max(freq[peaks[0]]))
        print("fmax = ", fMax)


        
        self.ui.fsSlider.setMaximum(3*fMax)
        self.ui.fsSlider.setTickInterval(fMax)
        self.ui.fsSlider.setTickPosition(QSlider.TicksBelow)

    def sampleSignal(self):
        samplingFrequency = self.ui.fsSlider.value()
        # print(samplingFrequency)
        self.ui.fsSliderValShowerLabel.setText(f'Fs = {samplingFrequency}')
        signalDuration = self.xAxisValuesOfOriginalSignal[-1] - self.xAxisValuesOfOriginalSignal[0]
        signalLength = len(self.xAxisValuesOfOriginalSignal)
        if samplingFrequency > 0:
            samplingIndexPeriod = max(np.floor(signalLength / (signalDuration * samplingFrequency)).astype(int),1)
            sampledDataIndex = np.arange(0, signalLength, samplingIndexPeriod, dtype=int)

            self.sampledTime = np.array(self.xAxisValuesOfOriginalSignal)[sampledDataIndex]
            self.sampledValue = np.array(self.yAxisValuesOfOriginalSignal)[sampledDataIndex]
            self.sampledPointsPlotter.setData(self.sampledTime,self.sampledValue)
        else:
            self.sampledPointsPlotter.setData([],[])
            



    def reconstructSignal(self):
        self.reconstructedTime = np.linspace(min(self.sampledTime), max(self.sampledTime), 1000)
        spl = make_interp_spline(self.sampledTime, self.sampledValue, 2)
        self.reconstructedValue = spl(self.reconstructedTime)

        self.reconstructedSignalPlotter.setData(self.reconstructedTime, self.reconstructedValue)
        self.reconstructedPointsPlotter.setData(self.reconstructedTime, self.reconstructedValue) # <- comment

    def updateSingleSignal(self):

        self.phaseShiftValue = self.ui.phaseInputValue.value()
        self.freqValue = self.ui.frequencyInputValue.value()
        self.magnitudeValue = self.ui.magnitudeInputValue.value()

        print(self.phaseShiftValue,self.freqValue,self.magnitudeValue)

        

        # amp * sin (freq * (X + phase shift) )
        self.singleSignalY = sine_wave(frequency=self.freqValue, samplerate=1000, amplitude=self.magnitudeValue, offset=0, phaseshift = self.phaseShiftValue)

        self.singleSinPlotter.setData(self.singleSignalX,self.singleSignalY)

    def addSignal(self):

        signalName = "sine_wave_" + str(self.freqValue) + "_" + str(self.magnitudeValue) + "_" + str(self.phaseShiftValue)
        self.signalsList.append(signalName)
        self.signalsListYValues.append(self.singleSignalY)
        # print(self.signalsList)

        for IDX in range(1000):
            self.signalComposerCompinedSignalsY[IDX] += self.singleSignalY[IDX]

        self.composeredSignalPlotter.setData(self.signalComposerCompinedSignalsX,self.signalComposerCompinedSignalsY)

        self.ui.sinSignalsHolder.addItem(signalName)

    def removeSignal(self):
        IDXtoRemove = self.ui.sinSignalsHolder.currentIndex()
        self.signalsList.pop(IDXtoRemove)
        # print(self.signalsListYValues[IDXtoRemove])
        for IDX in range(1000):
            self.signalComposerCompinedSignalsY[IDX] -= self.signalsListYValues[IDXtoRemove][IDX]
        self.signalsListYValues.pop(IDXtoRemove)
        self.ui.sinSignalsHolder.clear()
        self.ui.sinSignalsHolder.addItems(self.signalsList)
        self.composeredSignalPlotter.setData(self.signalComposerCompinedSignalsX,self.signalComposerCompinedSignalsY)
        # print(IDXtoRemove)

    def clearAll(self):
        self.signalsList = []
        self.signalsListYValues = []
        self.signalComposerCompinedSignalsY = [0]*1000
        self.composeredSignalPlotter.setData([],[])
        self.ui.sinSignalsHolder.clear()
    
    def showOrHide(self):
        if (self.showHideFlag):
            self.ui.reconstructedSignal.setVisible(False)
            self.ui.showHideBtn.setText("Show Reconstructed Signal")
            self.ui.showHideBtn.setIcon(self.showIcon)

        else:
            self.ui.reconstructedSignal.setVisible(True)
            self.ui.showHideBtn.setText("Hide Reconstructed Signal")
            self.ui.showHideBtn.setIcon(self.hideIcon)

        self.showHideFlag = not(self.showHideFlag)
            

    def save(self):
        name = self.ui.nameInput.text() + ".csv"
        np.savetxt(name , [p for p in zip(self.signalComposerCompinedSignalsX, self.signalComposerCompinedSignalsY)], delimiter=',', fmt='%s')

    def openSignalComposerTab(self):
        self.ui.tabWidget.setCurrentIndex(0)



if __name__ == '__main__':      
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet())
    main = mainApp()
    main.show()
    sys.exit(app.exec_())