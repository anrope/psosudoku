#!/usr/bin/python

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from psosudoku import *
import sys
import random
import cProfile
import time

#overall entry point
def main(argv):
	app = QApplication(sys.argv)
	
	w = MainWindow()
	w.show()
	#cProfile.runctx('app.exec_()',globals(),locals(),'profile')
	#sys.exit()
	sys.exit(app.exec_())

#takes a filename, reads a sudoku in and returns a string
def readSudokuFromFile(infile):
	try:
		f = open(infile, 'r')
	except IOError as err:
		print("<<{0}>>".format(e))
		f = open("./puzzle1.txt", 'r')
	
	initpuzzle = [[None for i in range(9)] for j in range(9)]
	i = 0
	for line in f:
		initpuzzle[i] = line.split()
		i = i + 1
	return initpuzzle

#separate (from the gui) thread to do the actual PSO processing
class psothread(QThread):	
	def __init__(self,parent=None):
		QThread.__init__(self,parent)
		self.pause = True
		self.finished = False
		self.infile = "./puzzle1.txt"
		self.nparticles = 150
		self.weights = [.9, .4, .5]
		self.lazythreshold = 5
		self.timestamp = 0
		
	#run() is the entry point of the thread, contains our main processing loop
	def run(self):
		random.seed()
		
		#read in the file set by the gui
		initpuzzle = readSudokuFromFile(self.infile)
		
		#initialize our swarm based on gui input fields
		s = swarm(initpuzzle, self.nparticles, self.weights, self.lazythreshold)
		
		#hand the gui a reference to the new swarm, and tell the gui to redraw
		self.emit(SIGNAL("updateswarm"), s)
		self.emit(SIGNAL("initpso"))
		
		#loop until gui asks for a reset
		while not self.finished:
			self.emit(SIGNAL("pausepso"), self.pause)
			#processing loop runs as long as pause button isn't toggled on
			if not self.pause:
				#QThread.msleep(10)
				#optimize() runs the main loop of the particle swarm optimization
				s.optimize()
				#tell the gui we finished an optimization iteration
				self.emit(SIGNAL("updatepso"))
				#grab a timestamp and report it to the gui
				timestamp = time.time()
				self.emit(SIGNAL("timepso"),timestamp - self.timestamp)
				self.timestamp = timestamp
			#if paused, just sleep
			else:
				QThread.msleep(500)
		self.emit(SIGNAL("endpso"))

	def setInfile(self, infile):
		self.infile = infile
		
	def setWeights(self, w):
		self.weights = w
		
	def setNparticles(self, p):
		self.nparticles = p
	
	def setLazyThreshold(self, l):
		self.lazythreshold = l
	
	#toggle paused state
	def pausePso(self):
		if self.pause:
			self.pause = False
		else:
			self.pause = True
			
	#handles resetting pso
	def resetPso(self):
		if not self.finished:
			self.finished = True
		else:
			self.finished = False
	
#main window for our gui
class MainWindow(QMainWindow):	
	def __init__(self, *args):
		QWidget.__init__(self, *args)
		
		#initialize current particle to display to 0
		self.currentParticle = 0
		
		#intialize a pso worker thread
		self.p = psothread()
		
		#
		self.particlemodel = ParticleModel(self)
		self.particleview = QTableView()
		self.particleview.setModel(self.particlemodel)
		self.particleview.resizeColumnsToContents()
		self.particleview.resizeRowsToContents()
		width = self.particleview.horizontalHeader().length() + 24
		self.particleview.setMaximumWidth(width)
		self.particleview.setMinimumWidth(width)
		
		self.puzzlemodel = PuzzleModel(self)
		self.puzzleview = QTableView()
		self.puzzleview.setSelectionMode(QAbstractItemView.NoSelection)
		self.puzzleview.setModel(self.puzzlemodel)
		for i in range(9):
			self.puzzleview.setColumnWidth(i,55)
		self.puzzleview.resizeRowsToContents()
		width = self.puzzleview.horizontalHeader().length() + 20
		height = self.puzzleview.verticalHeader().length() + 27
		self.puzzleview.setMaximumWidth(width)
		self.puzzleview.setMinimumWidth(width)
		self.puzzleview.setMaximumHeight(height)
		self.puzzleview.setMinimumHeight(height)
		
		self.velmodel = PuzzleModel(self)
		self.velview = QTableView()
		self.velview.setSelectionMode(QAbstractItemView.NoSelection)
		self.velview.setModel(self.velmodel)
		for i in range(9):
			self.velview.setColumnWidth(i,55)
		self.velview.resizeRowsToContents()
		width = self.velview.horizontalHeader().length() + 20
		height = self.velview.verticalHeader().length() + 27
		self.velview.setMaximumWidth(width)
		self.velview.setMinimumWidth(width)
		self.velview.setMaximumHeight(height)
		self.velview.setMinimumHeight(height)
		
		self.pbestmodel = PuzzleModel(self)
		self.pbestview = QTableView()
		self.pbestview.setSelectionMode(QAbstractItemView.NoSelection)
		self.pbestview.setModel(self.pbestmodel)
		for i in range(9):
			self.pbestview.setColumnWidth(i,55)
		self.pbestview.resizeRowsToContents()
		width = self.pbestview.horizontalHeader().length() + 20
		height = self.pbestview.verticalHeader().length() + 27
		self.pbestview.setMaximumWidth(width)
		self.pbestview.setMinimumWidth(width)
		self.pbestview.setMaximumHeight(height)
		self.pbestview.setMinimumHeight(height)
		
		self.gbestmodel = PuzzleModel(self)
		self.gbestview = QTableView()
		self.gbestview.setSelectionMode(QAbstractItemView.NoSelection)
		self.gbestview.setModel(self.gbestmodel)
		for i in range(9):
			self.gbestview.setColumnWidth(i,55)
		self.gbestview.resizeRowsToContents()
		width = self.gbestview.horizontalHeader().length() + 20
		height = self.gbestview.verticalHeader().length() + 27
		self.gbestview.setMaximumWidth(width)
		self.gbestview.setMinimumWidth(width)
		self.gbestview.setMaximumHeight(height)
		self.gbestview.setMinimumHeight(height)
		
		self.puzzlelabel = QLabel(QString("Puzzle 0"))
		self.vellabel = QLabel(QString("Velocity 0"))
		self.pbestlabel = QLabel(QString("Personal Best"))
		self.gbestlabel = QLabel(QString("Global Best"))
		self.lazythreshlabel = QLabel(QString("Laziness Threshold"))
		self.nparticleslabel = QLabel(QString("Number of Particles"))
		self.velweightlabel = QLabel(QString("Velocity Weight"))
		self.personalweightlabel = QLabel(QString("Personal Best Weight"))
		self.globalweightlabel = QLabel(QString("Global Best Weight"))
		self.filelabel = QLabel(QString("Input File"))
		self.timelabel = QLabel(QString("Elapsed Time"))
		self.particletimelabel = QLabel(QString("Elapsed Time per Particle"))
		
		self.lazythreshedit = QLineEdit(QString(str(self.p.lazythreshold)))
		self.lazythreshedit.setMaximumWidth(75)
		self.nparticlesedit = QLineEdit(QString(str(self.p.nparticles)))
		self.nparticlesedit.setMaximumWidth(75)
		self.velweightedit = QLineEdit(QString(str(self.p.weights[0])))
		self.velweightedit.setMaximumWidth(75)
		self.personalweightedit = QLineEdit(QString(str(self.p.weights[1])))
		self.personalweightedit.setMaximumWidth(75)
		self.globalweightedit = QLineEdit(QString(str(self.p.weights[2])))
		self.globalweightedit.setMaximumWidth(75)
		self.fileedit = QLineEdit(QString(str(self.p.infile)))
		self.fileedit.setMaximumWidth(200)
		
		self.resetbutton = QPushButton(QString("Reset"))
		self.pausebutton = QPushButton(QString("Run"))
		
		self.puzzlecheck = QCheckBox("Decimal")
		self.velcheck = QCheckBox("Decimal")
		self.pbestcheck = QCheckBox("Decimal")
		self.gbestcheck = QCheckBox("Decimal")
		
		settingswidget = QWidget(self)
		settingslayout = QGridLayout(settingswidget)
		
		lazythreshwidget = QWidget(settingswidget)
		lazythreshlayout = QHBoxLayout(lazythreshwidget)
		lazythreshlayout.addWidget(self.lazythreshlabel,alignment=Qt.AlignLeft)
		lazythreshlayout.addWidget(self.lazythreshedit,alignment=Qt.AlignLeft)
		settingslayout.addWidget(lazythreshwidget,0,1,1,1)
		
		nparticleswidget = QWidget(settingswidget)
		nparticleslayout = QHBoxLayout(nparticleswidget)
		nparticleslayout.addWidget(self.nparticleslabel,alignment=Qt.AlignLeft)
		nparticleslayout.addWidget(self.nparticlesedit,alignment=Qt.AlignLeft)
		settingslayout.addWidget(nparticleswidget,1,1,1,1)
		
		velweightwidget = QWidget(settingswidget)
		velweightlayout = QHBoxLayout(velweightwidget)
		velweightlayout.addWidget(self.velweightlabel,alignment=Qt.AlignLeft)
		velweightlayout.addWidget(self.velweightedit,alignment=Qt.AlignLeft)
		settingslayout.addWidget(velweightwidget,0,0,1,1)
		
		personalweightwidget = QWidget(settingswidget)
		personalweightlayout = QHBoxLayout(personalweightwidget)
		personalweightlayout.addWidget(self.personalweightlabel,alignment=Qt.AlignLeft)
		personalweightlayout.addWidget(self.personalweightedit,alignment=Qt.AlignLeft)
		settingslayout.addWidget(personalweightwidget,1,0,1,1)
		
		globalweightwidget = QWidget(settingswidget)
		globalweightlayout = QHBoxLayout(globalweightwidget)
		globalweightlayout.addWidget(self.globalweightlabel,alignment=Qt.AlignLeft)
		globalweightlayout.addWidget(self.globalweightedit,alignment=Qt.AlignLeft)
		settingslayout.addWidget(globalweightwidget,2,0,1,1)
		
		filewidget = QWidget(settingswidget)
		filelayout = QHBoxLayout(filewidget)
		filelayout.addWidget(self.filelabel,alignment=Qt.AlignLeft)
		filelayout.addWidget(self.fileedit,alignment=Qt.AlignLeft)
		settingslayout.addWidget(filewidget,2,1,1,1)
		
		timewidget = QWidget(settingswidget)
		timelayout = QHBoxLayout(timewidget)
		timelayout.addWidget(self.timelabel,alignment=Qt.AlignLeft)
		settingslayout.addWidget(timewidget,0,2,1,1)
		
		particletimewidget = QWidget(settingswidget)
		particletimelayout = QHBoxLayout(particletimewidget)
		particletimelayout.addWidget(self.particletimelabel,alignment=Qt.AlignLeft)
		settingslayout.addWidget(particletimewidget,1,2,1,1)
		
		buttonwidget = QWidget(settingswidget)
		buttonlayout = QHBoxLayout(buttonwidget)
		buttonlayout.addWidget(self.resetbutton,alignment=Qt.AlignRight)
		buttonlayout.addWidget(self.pausebutton,alignment=Qt.AlignRight)
		settingslayout.addWidget(buttonwidget,2,2,1,1)
		
		puzzlewidget = QWidget(self)
		puzzlelayout = QVBoxLayout(puzzlewidget)
		headingwidget = QWidget(puzzlewidget)
		headinglayout = QHBoxLayout(headingwidget)
		headinglayout.addWidget(self.puzzlelabel)
		headinglayout.addWidget(self.puzzlecheck)
		puzzlelayout.addWidget(headingwidget)
		puzzlelayout.addWidget(self.puzzleview)
		
		velwidget = QWidget(self)
		vellayout = QVBoxLayout(velwidget)
		headingwidget = QWidget(velwidget)
		headinglayout = QHBoxLayout(headingwidget)
		headinglayout.addWidget(self.vellabel)
		headinglayout.addWidget(self.velcheck)
		vellayout.addWidget(headingwidget)
		vellayout.addWidget(self.velview)
		
		pbestwidget = QWidget(self)
		pbestlayout = QVBoxLayout(pbestwidget)
		headingwidget = QWidget(pbestwidget)
		headinglayout = QHBoxLayout(headingwidget)
		headinglayout.addWidget(self.pbestlabel)
		headinglayout.addWidget(self.pbestcheck)
		pbestlayout.addWidget(headingwidget)
		pbestlayout.addWidget(self.pbestview)
		
		gbestwidget = QWidget(self)
		gbestlayout = QVBoxLayout(gbestwidget)
		headingwidget = QWidget(gbestwidget)
		headinglayout = QHBoxLayout(headingwidget)
		headinglayout.addWidget(self.gbestlabel)
		headinglayout.addWidget(self.gbestcheck)
		gbestlayout.addWidget(headingwidget)
		gbestlayout.addWidget(self.gbestview)

		centralwidget = QWidget(self)
		gridlayout = QGridLayout(centralwidget)
		gridlayout.addWidget(self.particleview,0,0,4,1)
		gridlayout.addWidget(puzzlewidget,0,1,1,1)
		gridlayout.addWidget(velwidget,1,1,1,1)
		gridlayout.addWidget(pbestwidget,1,2,1,1)
		gridlayout.addWidget(gbestwidget,0,2,1,1)
		gridlayout.addWidget(settingswidget,3,1,1,2)
		
		self.setCentralWidget(centralwidget)
		
		self.connect(self.p, SIGNAL("updateswarm"), self.updateSwarm)
		
		self.connect(self.p, SIGNAL("initpso"), self.initPso)
		
		self.connect(self.p, SIGNAL("updatepso"), self.updatePso)
		self.connect(self.puzzlemodel, SIGNAL("updatepso"), self.updatePso)
		self.connect(self.velmodel, SIGNAL("updatepso"), self.updatePso)
		self.connect(self.pbestmodel, SIGNAL("updatepso"), self.updatePso)
		self.connect(self.gbestmodel, SIGNAL("updatepso"), self.updatePso)
		self.connect(self, SIGNAL("updatepso"), self.updatePso)
		
		self.connect(self.p, SIGNAL("timepso"), self.timePso)
		
		self.connect(self.pausebutton, SIGNAL("clicked()"), self.p.pausePso)
		self.connect(self.p, SIGNAL("pausepso"), self.pausePso)
		
		self.connect(self.particleview, SIGNAL("clicked(const QModelIndex&)"), self.changeParticle)
		
		self.connect(self.resetbutton, SIGNAL("clicked()"), self.p.resetPso)
		self.connect(self.p, SIGNAL("endpso"), self.resetPso)
		
		self.connect(self.puzzlecheck, SIGNAL("toggled(bool)"), self.puzzlemodel.setDecimal)
		self.connect(self.velcheck, SIGNAL("toggled(bool)"), self.velmodel.setDecimal)
		self.connect(self.pbestcheck, SIGNAL("toggled(bool)"), self.pbestmodel.setDecimal)
		self.connect(self.gbestcheck, SIGNAL("toggled(bool)"), self.gbestmodel.setDecimal)
		
		self.p.start()
	
	def changeParticle(self, p):
		if type(p) is int:
			self.currentParticle = p
		else:
			self.currentParticle = p.row()
		self.puzzlelabel.setText(QString("Puzzle {0}".format(self.currentParticle)))
		self.vellabel.setText(QString("Velocity {0}".format(self.currentParticle)))
		#self.emit(SIGNAL("updatepso"))
		self.particlemodel.setParticle(self.currentParticle)
		self.particleview.clearSelection()
		
		self.puzzlemodel.setValid(self.swarm.particles[self.currentParticle].valid)
		self.puzzlemodel.setData(self.swarm.particles[self.currentParticle].sudoku.puzzle)
		
		self.velmodel.setValid(self.swarm.particles[self.currentParticle].valid)
		self.velmodel.setData(self.swarm.particles[self.currentParticle].velocity)
		
		self.pbestlabel.setText("Personal Best (Particle {0}: {1})".format(self.currentParticle, self.swarm.particles[self.currentParticle].personalbest))
		self.pbestmodel.setValid(self.swarm.particles[self.currentParticle].personalbestvalid)
		self.pbestmodel.setData(self.swarm.particles[self.currentParticle].personalbestposition)
		
		self.gbestlabel.setText("Global Best (Particle {0}: {1})".format(self.swarm.globalbestparticle,self.swarm.globalbest))
		self.gbestmodel.setValid(self.swarm.globalbestvalid)
		self.gbestmodel.setData(self.swarm.globalbestposition)
		
	def updateSwarm(self, s):
		self.swarm = s
		
	def timePso(self, elapsed):
		self.timelabel.setText("Elapsed Time: {0}s".format(round(elapsed,5)))
		self.particletimelabel.setText("Elapsed Time: {0}s/particle".format(round(elapsed/self.swarm.nparticles,5)))
	
	def resetPso(self):
		self.p.wait()
		self.p.resetPso()
		self.p.setInfile(self.fileedit.text())
		self.p.setNparticles(int(self.nparticlesedit.text()))
		self.p.setWeights([float(self.velweightedit.text()), float(self.personalweightedit.text()), float(self.globalweightedit.text())])
		self.p.setLazyThreshold(int(self.lazythreshedit.text()))
		self.p.start()
	
	def pausePso(self, paused):
		if paused:
			self.pausebutton.setText(QString("Run"))
			self.pausebutton.setStyleSheet("background: rgb(44,204,4)")
		else:
			self.pausebutton.setText(QString("Pause"))
			self.pausebutton.setStyleSheet("background: rgb(255,44,30)")
		
	def initPso(self):
		self.particlemodel.setData(self.swarm)
		
		self.puzzlemodel.setMask(self.swarm.particles[0].sudoku.puzzlemask)
		self.puzzlemodel.setValid(self.swarm.particles[self.currentParticle].valid)
		self.puzzlemodel.setData(self.swarm.particles[self.currentParticle].sudoku.puzzle)
		
		self.velmodel.setMask(self.swarm.particles[0].sudoku.puzzlemask)
		self.velmodel.setValid(self.swarm.particles[self.currentParticle].valid)
		self.velmodel.setData(self.swarm.particles[self.currentParticle].velocity)
		
		self.pbestmodel.setMask(self.swarm.particles[0].sudoku.puzzlemask)
		self.pbestmodel.setValid(self.swarm.particles[0].personalbestvalid)
		self.pbestmodel.setData(self.swarm.particles[0].personalbestposition)
		
		self.gbestmodel.setMask(self.swarm.particles[0].sudoku.puzzlemask)
		self.gbestmodel.setValid(self.swarm.globalbestvalid)
		self.gbestmodel.setData(self.swarm.globalbestposition)
		
		self.particlemodel.emit(SIGNAL("layoutChanged()"))
		self.puzzlemodel.emit(SIGNAL("layoutChanged()"))
		self.velmodel.emit(SIGNAL("layoutChanged()"))
		self.pbestmodel.emit(SIGNAL("layoutChanged()"))
		self.gbestmodel.emit(SIGNAL("layoutChanged()"))
		
	def updatePso(self):
		#self.particlemodel.setData(self.swarm)
		#self.particlemodel.setParticle(self.currentParticle)
		
		self.puzzlemodel.setValid(self.swarm.particles[self.currentParticle].valid)
		#self.puzzlemodel.setData(self.swarm.particles[self.currentParticle].sudoku.puzzle)

		self.velmodel.setValid(self.swarm.particles[self.currentParticle].valid)
		#self.velmodel.setData(self.swarm.particles[self.currentParticle].velocity)
		
		self.pbestlabel.setText("Personal Best (Particle {0}: {1})".format(self.currentParticle, self.swarm.particles[self.currentParticle].personalbest))
		self.pbestmodel.setValid(self.swarm.particles[self.currentParticle].personalbestvalid)
		self.pbestmodel.setData(self.swarm.particles[self.currentParticle].personalbestposition)
		
		self.gbestlabel.setText("Global Best (Particle {0}: {1})".format(self.swarm.globalbestparticle,self.swarm.globalbest))
		self.gbestmodel.setValid(self.swarm.globalbestvalid)
		self.gbestmodel.setData(self.swarm.globalbestposition)
		
		#self.particlemodel.reset()
		#self.puzzlemodel.reset()
		#self.velmodel.reset()
		#self.pbestmodel.reset()
		#self.gbestmodel.reset()
		
		self.particlemodel.emit(SIGNAL("layoutChanged()"))
		self.puzzlemodel.emit(SIGNAL("layoutChanged()"))
		self.velmodel.emit(SIGNAL("layoutChanged()"))
		self.pbestmodel.emit(SIGNAL("layoutChanged()"))
		self.gbestmodel.emit(SIGNAL("layoutChanged()"))
		
class ParticleModel(QAbstractTableModel):
	def __init__(self, parent=None, *args):
		QAbstractTableModel.__init__(self, parent, *args)
		self.arraydata = [[None, None, None]]
		self.currentParticle = 0
		
	def rowCount(self, parent=QModelIndex()):
		return len(self.arraydata)
		
	def columnCount(self, parent):
		return len(self.arraydata[0])
		
	def setData(self, data):
		self.arraydata = data
		
	def setParticle(self, p):
		self.currentParticle = p
		
	def data(self, index, role):
		if not index.isValid():
			return QVariant()
		elif role == Qt.BackgroundRole and index.row() == self.currentParticle:
			return QVariant(QColor(115,255,117))
		elif role != Qt.DisplayRole:
			return QVariant()
		return QVariant(self.arraydata[index.row()][index.column()])
		
	def headerData(self, col, orientation, role):
		header = ['Particle', 'Fitness', 'PBest']
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return QVariant(header[col])
		return QVariant()

class PuzzleModel(QAbstractTableModel):
	def __init__(self, parent=None, *args):
		QAbstractTableModel.__init__(self, parent, *args)
		self.arraydata = [[0 for j in range(9)] for i in range(9)]
		self.validdata = ["none"]
		self.puzzlemask = [[0 for j in range(9)] for i in range(9)]
		self.outputdecimal = False

	def rowCount(self, parent):
		return len(self.arraydata)

	def columnCount(self, parent):
		return len(self.arraydata[0])
		
	def setDecimal(self, decimal):
		self.outputdecimal = decimal
		self.emit(SIGNAL("updatepso"))
		
	def setValid(self, valid):
		self.validdata = valid
		
	def setData(self, data):
		self.arraydata = data
		
	def setMask(self, mask):
		self.puzzlemask = mask
		
	def isMasked(self, index):
		if self.puzzlemask[index.row()][index.column()]:
			return True
		else:
			return False
		
	def	validArea(self, index):
		for i in range(len(self.validdata)):
			if self.validdata[i].find("row") != -1:
				if self.validdata[i].find(str(index.row())) != -1:
					return True
			elif self.validdata[i].find("col") != -1:
				if self.validdata[i].find(str(index.column())) != -1:
					return True
			elif self.validdata[i].find("square") != -1:
				if self.validdata[i].find("{0},{1}".format(index.row()/3, index.column()/3)) != -1:
					return True
		return False

	def data(self, index, role):
		if not index.isValid():
			return QVariant()
		elif role == Qt.BackgroundRole and self.isMasked(index):
			return QVariant(QColor(255,196,92))
		elif role == Qt.BackgroundRole and self.validArea(index):
			return QVariant(QColor(118,182,255))
		elif role == Qt.BackgroundRole:
			return QVariant(QColor(Qt.white))
		elif role != Qt.DisplayRole:
			return QVariant()
		elif self.outputdecimal:
			return QVariant(round(self.arraydata[index.row()][index.column()],3))
		else:
			return QVariant(int(round(self.arraydata[index.row()][index.column()])))

if __name__ == "__main__":
	main(sys.argv)