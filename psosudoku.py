#!/usr/bin/python

import sys
import random
import signal

#generic function for printing out a 9x9 list of lists
def str2d(p):
	puzzlestring = ""
	for i in range(9):
		puzzle = [int(round(p[i][j])) for j in range(9)]
		puzzlestring += "{p[0]} {p[1]} {p[2]} | {p[3]} {p[4]} {p[5]} | {p[6]} {p[7]} {p[8]}\n".format(p=puzzle)
		if i in [2,5]:
			puzzlestring += "----------------------\n"
	return puzzlestring.replace('None',' ')

#sudoku class represents a sudoku as a
#completed puzzle and a puzzlemask that
#defines which cells are unchangeable
class sudoku:
	puzzledim = 9
	puzzle = None
	puzzlemask = None
	
	#sudoku constructor
	#creates structures for the puzzle and puzzlemask based on the input string
	def __init__(self,initpuzzle):
		self.puzzle = [[None for i in range(self.puzzledim)] for j in range(self.puzzledim)]
		self.puzzlemask = [[None for i in range(self.puzzledim)] for j in range(self.puzzledim)]
		for i in range(self.puzzledim):
			for j in range(self.puzzledim):
				#an "x" in the input file indicates an unset value
				if initpuzzle[i][j] == 'x':
					self.puzzlemask[i][j] = False
					self.puzzle[i][j] = random.randint(1,self.puzzledim)
				#a set value in the input file is a set value in the puzzle
				else:
					self.puzzlemask[i][j] = True
					self.puzzle[i][j] = int(initpuzzle[i][j])

	#returns a human readable representation of the sudoku
	def __str__(self):
		puzzlestring = ""
		for i in range(self.puzzledim):
			puzzle = [int(round(self.puzzle[i][j])) for j in range(self.puzzledim)]
			puzzlestring += "{p[0]} {p[1]} {p[2]} | {p[3]} {p[4]} {p[5]} | {p[6]} {p[7]} {p[8]}\n".format(p=puzzle)
			if i in [2,5]:
				puzzlestring += "----------------------\n"
		return puzzlestring.replace('None',' ')
	
	#fills the puzzle with random integers
	def fillPuzzle(self):
		for i in range(self.puzzledim):
			for j in range(self.puzzledim):
				self.setElement(i,j,random.randint(1,self.puzzledim))
	
	#returns a deep copy of the puzzle (avoids reference issues)
	def copyPuzzle(self):
		return [[self.puzzle[i][j] for j in range(self.puzzledim)] for i in range(self.puzzledim)]
	
	#element setting function that considers the puzzlemask
	def setElement(self, x, y, num):
		if self.puzzlemask[x][y] == False:
			self.puzzle[x][y] = num
			
	#returns element (x,y)
	def getElement(self, x, y):
		return self.puzzle[x][y]
	
	#returns a list of the requested row
	def getRow(self, row):
		return self.puzzle[row]
		
	#returns a list of the requested column
	def getCol(self, col):
		return [self.puzzle[i][col] for i in range(self.puzzledim)]
		
	#returns a 2d list of a 3x3 square
	def getSquare(self, x, y):
		startx = 3*x
		endx = startx+3
		starty = 3*y
		endy = starty+3
		return [self.puzzle[i][j] for j in range(starty,endy) for i in range(startx,endx)]
	
	#first shot at fitness evaluation
	#sums the number of valid rows, columns, and squares
	def getValid(self):
		valid = []
		
		for i in range(self.puzzledim):
			values = self.getRow(i)
			values = set([int(round(values[j])) for j in range(self.puzzledim)])
			if len(values) == self.puzzledim:
				valid.append("row {0}".format(i))
			
			values = self.getCol(i)
			values = set([int(round(values[j])) for j in range(self.puzzledim)])
			if len(values) == self.puzzledim:
				valid.append("col {0}".format(i))
		
		for i in range(3):
			for j in range(3):
				values = self.getSquare(i,j)
				values = set([int(round(values[k])) for k in range(self.puzzledim)])
				if len(values) == self.puzzledim:
					valid.append("square {0},{1}".format(i,j))
		
		return valid
		
	#second shot at fitness evaluation
	#sums the number of valid rows, columns, and squares.
	#weights squares heavier than rows or columns.
	#adds a point for each cell that satisfies multiple constraints.
	def getValidCells(self):
		valid = []
		fitness = 0
		squaresrows = []
		squarescols = []
		rows = []
		cols = []
		
		#determine number of valid squares
		for i in range(3):
			for j in range(3):
				values = self.getSquare(i,j)
				values = set([int(round(values[k])) for k in range(self.puzzledim)])
				if len(values) == self.puzzledim:
					squaresrows.append(i)
					squarescols.append(j)
					valid.append("square {0},{1}".format(i,j))
					fitness += 10
		
		#determine number of valid rows and columns
		for i in range(self.puzzledim):
			values = self.getRow(i)
			values = set([int(round(values[j])) for j in range(self.puzzledim)])
			if len(values) == self.puzzledim:
				valid.append("row {0}".format(i))
				rows.append(i)
			
			values = self.getCol(i)
			values = set([int(round(values[j])) for j in range(self.puzzledim)])
			if len(values) == self.puzzledim:
				valid.append("col {0}".format(i))
				cols.append(i)
		
		#determine number of row-square intersecting cells
		for i in range(len(rows)):
			fitness += squaresrows.count(rows[i]/3) * 3
		
		#determine number of column-square intersecting cells
		for i in range(len(cols)):
			fitness += squarescols.count(cols[i]/3) * 3
		
		#determine fitness
		fitness += len(rows)*9 + len(cols)*9 + len(rows) * len(cols)
		
		return (valid, fitness)

class particle:
	fitness = None
	sudoku = None
	valid = None
	velocity = None
	personalbest = 0
	personalbestposition = None
	personalbestvalid = []
	globalbest = 0
	globalbestposition = None
	globalbestvalid = []
	lazy = 0
	
	def __init__(self, sudoku, weights, lazythreshold):
		self.sudoku = sudoku
		self.weights = weights
		self.lazythreshold = lazythreshold
		self.velocity = [[0 for i in range(self.sudoku.puzzledim)] for j in range(self.sudoku.puzzledim)]
		#self.velocity = [[random.uniform(-8,8) for i in range(self.sudoku.puzzledim)] for j in range(self.sudoku.puzzledim)]
		self.personalbestposition = self.sudoku.copyPuzzle()
		#self.personalbestposition = [[0 for i in range(self.sudoku.puzzledim)] for j in range(self.sudoku.puzzledim)]
		self.globalbestposition = [[0 for i in range(self.sudoku.puzzledim)] for j in range(self.sudoku.puzzledim)]
		#self.personalbestposition = [[random.uniform(1,9) for i in range(self.sudoku.puzzledim)] for j in range(self.sudoku.puzzledim)]
		#self.globalbestposition = [[random.uniform(1,9) for i in range(self.sudoku.puzzledim)] for j in range(self.sudoku.puzzledim)]
		self.updateFitness()
		
	def __str__(self):
		return self.sudoku.__str__()
		
	def updateLazy(self):
		if self.fitness == self.globalbest:
			self.lazy += 1
			if self.lazy >= self.lazythreshold:
				self.sudoku.fillPuzzle()
				self.personalbestposition = self.sudoku.copyPuzzle()
		else:
			self.lazy = 0
	
	def updateFitness(self):
		#self.valid = self.sudoku.getValid()
		self.valid, self.fitness = self.sudoku.getValidCells()
		#self.fitness = len(self.valid)
		if self.fitness > self.personalbest:
			self.personalbest = self.fitness
			self.personalbestposition = self.sudoku.copyPuzzle()
			self.personalbestvalid = self.valid
			if self.fitness > self.globalbest:
				self.globalbest = self.fitness
				self.globalbestposition = self.sudoku.copyPuzzle()
				self.globalbestvalid = self.valid
	
	def updateVelocity(self):
		for i in range(self.sudoku.puzzledim):
			for j in range(self.sudoku.puzzledim):
				t1 = self.weights[0] * self.velocity[i][j]
				t2 = self.weights[1] * random.uniform(0,1) * (self.personalbestposition[i][j] - self.sudoku.puzzle[i][j])
				t3 = self.weights[2] * random.uniform(0,1) * (self.globalbestposition[i][j] - self.sudoku.puzzle[i][j])
				self.velocity[i][j] = t1 + t2 + t3
				if self.velocity[i][j] > 2:
					self.velocity[i][j] = -2
				if self.velocity[i][j] < -2:
					self.velocity[i][j] = 2
				
	def updatePosition(self):
		for i in range(self.sudoku.puzzledim):
			for j in range(self.sudoku.puzzledim):
				self.sudoku.setElement(i,j,self.sudoku.getElement(i,j)+self.velocity[i][j])
				if self.sudoku.getElement(i,j) >= 9.5:
					self.sudoku.setElement(i,j,1)
				if self.sudoku.getElement(i,j) < .5:
					self.sudoku.setElement(i,j,9)
				
class swarm:
	globalbestparticle = None
	globalbestposition = None
	globalbestvalid = None
	globalbest = 0
	particles = []
	nparticles = 0
	
	def __init__(self, initpuzzle, particles, weights, lazythreshold):
		self.nparticles = particles
		self.particles = [particle(sudoku(initpuzzle), weights, lazythreshold) for i in range(self.nparticles)]
		self.globalbestposition = self.particles[0].globalbestposition
		self.globalbestparticle = 0
		self.updateGlobalBest()
		
	def __len__(self):
		return self.nparticles
		
	def __getitem__(self,index):
		return [index, self.particles[index].fitness, self.particles[index].personalbest]
		
	def __str__(self):
		string = ""
		for p in range(self.nparticles):
			string += "Particle {0} fitness: {1}\n".format(p,self.particles[p].fitness)
		return string
		
	def particleList(self):
		return ["Particle {0}".format(p) for p in range(self.nparticles)]
		
	def updateGlobalBest(self):
		best = self.globalbest
		for p in range(self.nparticles):
			if self.particles[p].globalbest > best:
				best = self.particles[p].globalbest
				self.globalbestposition = self.particles[p].globalbestposition
				self.globalbestvalid  = self.particles[p].globalbestvalid
				self.globalbestparticle = p
				
		self.globalbest = best
		for p in range(self.nparticles):
			self.particles[p].globalbest = best
			self.particles[p].globalbestposition = self.globalbestposition
			self.particles[p].globalbestvalid = self.globalbestvalid
			
	def optimize(self):
		for p in range(self.nparticles):
			self.particles[p].updateVelocity()
			self.particles[p].updatePosition()
			self.particles[p].updateFitness()
			self.particles[p].updateLazy()
		self.updateGlobalBest()
			
def diepretty(signal, frame):
	print "\n"
	print s.globalbest
	print s.globalbestvalid
	print str2d(s.globalbestposition)
	sys.exit(0)
		
def main(argv):
	random.seed()
	
	signal.signal(signal.SIGINT, diepretty)
	
	f = open(argv[1], 'r')
	initpuzzle = [[None for i in range(9)] for j in range(9)]
	i = 0
	for line in f:
		initpuzzle[i] = line.split()
		i = i + 1
	
	global s
	s = swarm(initpuzzle, 100, [.7, .5, .4])
	
	i = 0
	while s.globalbest < 243:
		s.optimize()
		if i%10 == 0:
			print ">>>>>>> iteration {0} <<<<<<<".format(i)
			print s
			#print "Particle 0:"
			#print s.particles[0].sudoku
			#print s.globalbest
			#for j in range(s.nparticles):
				#print str2d(s.particles[j].velocity)
				#print "Particle {0}:".format(j)
				#print s.particles[j].sudoku
			#print "Global best (fitness {0}):".format(s.globalbest)
			#print str2d(s.globalbestposition)
		i += 1
	
#main(sys.argv)	
