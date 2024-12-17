import math
import pygame as pg
from pygame.locals import *
import sys
from dataclasses import dataclass
from typing import List
from random import randint
sys.setrecursionlimit(10000000)

pg.init()
clock = pg.time.Clock()

surf = pg.display.set_mode((800, 800), vsync=1)
white = (255,255,255)
black = (0,0,0)
green = (0,255,0)
red = (255,0,0)
blue = (0,0,255)
  
@dataclass
class Point:
  x: int
  y: int
  def __getitem__(this, i: int):
    if i==0: return this.x
    elif i==1: return this.y
    else: raise ValueError("Tried to access index that isn't 0 or 1 for a point")
  def draw(this,color=(0,255,0), radius=5):
    pg.draw.circle(surf,color, this.tup(), radius)
  def tup(this):
    return this.x, this.y
  def __hash__(this):
    return hash((this.x,this.y))
  
class KdTree:
  k = 2
  def __init__(this, points: List[Point], x_min, x_max, y_min, y_max, depth=0):
    this.points = points
    this.depth = depth
    this.x_min = x_min
    this.x_max = x_max
    this.y_min = y_min
    this.y_max = y_max
    n = len(points)
    if n <= 0:  # No points
      this.point = None
      this.left = None
      this.right = None
      return
    
    if n == 1:  # 1 point
      this.point = points[0]
      this.left = None
      this.right = None
      return
    
    axis = depth % 2
    
    sortedPoints = sorted(points, key=lambda point: point[axis])
    m = n//2
    this.point = sortedPoints[m]
    x, y = this.point.tup()
    this.split = x if axis == 0 else y
    if axis == 0:  # vert split
      left_boundary = (x_min, x, y_min, y_max)
      right_boundary = (x, x_max, y_min, y_max)
    else:  # hori split
      # pg.draw.line(SURF, (0, 0, 255), (x_min, y), (x_max, y), 1)
      # update boundaries for children
      left_boundary = (x_min, x_max, y_min, y)
      right_boundary = (x_min, x_max, y, y_max)
    this.left = None
    this.right = None
    if m > 0:
      this.left = KdTree(sortedPoints[:n//2], *left_boundary, depth=depth+1)
    if n - m > 0:
      this.right = KdTree(sortedPoints[n//2+1:], *right_boundary, depth=depth+1)
  
  def isLeaf(this):
    return this.left is None and this.right is None
  
  def traverse(this, orig, dir, tStart, tEnd):
    '''traverse kd tree'''
    if this.isLeaf():
      if this.point:
        return rectIntersect(this.point, orig, dir)
      return 1e9
    
    axis = this.depth % 2
    dk = dir[axis]
    ok = orig[axis]
    if dk != 0:
      t = (this.split - ok) / dk
      
      pg.draw.line(surf, red, (orig.x + tStart * dir[0], orig.y + tStart * dir[1]), (orig.x + t * dir[0], orig.y + t * dir[1]), 3)
      pg.draw.line(surf, red, (orig.x + tStart * dir[0], orig.y + tStart * dir[1]), (orig.x + tEnd * dir[0], orig.y + tEnd * dir[1]), 3)
      pg.draw.circle(surf, red, (orig.x + tStart * dir[0], orig.y + tStart * dir[1]), 5)
      # pg.draw.circle(surf, green, (orig.x + t * dir[0], orig.y + t * dir[1]), 5)
      pg.draw.circle(surf, blue, (orig.x + tEnd * dir[0], orig.y + tEnd * dir[1]), 5)
    else: return 1e9
    
    inter =  rectIntersect(this.point, orig, dir)
    if inter <= t: return inter
    
    if dk > 0:  # Positive direction
      near, far = this.left, this.right
    else:       # Negative direction
        near, far = this.right, this.left

      
    
    if far and t <= tStart:
      return far.traverse(orig, dir, tStart, tEnd)
    elif near and t >= tEnd:
      print("near")
      return near.traverse(orig, dir, tStart, tEnd)
    else:
      print("both")
      if near:
        tHit = near.traverse(orig, dir, tStart, t)
        if tHit <= t: return tHit
      if far:
        return far.traverse(orig, dir, t, tEnd)
      return 1e9
  
  def intersection(this, orig: Point, dir):
    '''find t-start and t-end for the bounding box given a line'''
    rox, roy = orig.tup()
    rdx, rdy = dir
    if rdx == rdy == 0: # can happen for one frame when user changes the location of the origin using mouse
      return None
    if rdx != 0:
      t1x = (this.x_min - rox) / rdx
      t2x = (this.x_max - rox) / rdx
      t1x, t2x = min(t1x, t2x), max(t1x, t2x)
    else: # vertical line
      t1y = (this.y_min - roy) / rdy
      t2y = (this.y_max - roy) / rdy
      return t1y, t2y

    if rdy != 0:
      t1y = (this.y_min - roy) / rdy
      t2y = (this.y_max - roy) / rdy
      t1y, t2y = min(t1y, t2y), max(t1y, t2y)
    else: # horizontal line
      t1x = (this.x_min - rox) / rdx
      t2x = (this.x_max - rox) / rdx
      return t1x, t2x
    
    start = max(t1x, t1y)
    end = min(t2x, t2y)
    
    return start, end
  
  def draw(this):
    '''draw kdtree boundaries'''
    if this.isLeaf():
      return
    if this.depth % 2 == 0:
      pg.draw.line(surf, white, (this.split, this.y_min), (this.split, this.y_max), this.depth//2 + 1)
    else:
      pg.draw.line(surf, white, (this.x_min, this.split), (this.x_max, this.split), this.depth//2 + 1)
    if this.left:
      this.left.draw()
    if this.right:
      this.right.draw()

points: List[Point] = []
rects: List[pg.rect.Rect] = []

def normalize(vector):
  magnitude = math.sqrt(vector[0]**2 + vector[1]**2)
  if magnitude == 0: magnitude = 0.001 # # can happen for one frame when user changes the location of the origin using mouse
  return (vector[0] / magnitude, vector[1] / magnitude)

def rectIntersect(point: Point, orig: Point, dir):
  rox, roy = orig.tup()
  rdx, rdy = dir
  # print(rdx, rdy)
  if rdx == rdy == 0: # can happen when user changes the location of the origin using mouse
    return None
  if rdx != 0:
    t1x = (point.x - rox) / rdx
    t2x = (point.x + 30 - rox) / rdx
    t1x, t2x = min(t1x, t2x), max(t1x, t2x)
  else: # vertical line
    t1y = (point.y - roy) / rdy
    t2y = (point.y + 30 - roy) / rdy
    return t1y

  if rdy != 0:
    t1y = (point.y - roy) / rdy
    t2y = (point.y + 30 - roy) / rdy
    t1y, t2y = min(t1y, t2y), max(t1y, t2y)
  else: # horizontal line
    t1x = (point.x - rox) / rdx
    t2x = (point.x + 30 - rox) / rdx
    return t1x
  
  start = max(t1x, t1y)
  end = min(t2x, t2y)
  if start <= end:
    # pg.draw.circle(surf, green, (point.x + t1x * dir[0], point.y + t1y * dir[1]), 3)
    # pg.draw.circle(surf, green, (point.x + t2x * dir[0], point.y + t2y * dir[1]), 3)
    pg.draw.circle(surf, red, (orig.x + start * dir[0], orig.y + start * dir[1]), 5)
    # pg.draw.circle(surf, red, (orig.x + end * dir[0], orig.y + end * dir[1]), 3)
    return start
  else: return 1e9


def newRect(point: Point):
  return pg.rect.Rect(point.x, point.y, 30, 30)

orig: Point = Point(400,400)

font = pg.font.Font(None, 40)

while 1:
  surf.fill((0,0,0))
  mpos = Point(*pg.mouse.get_pos())
  
  fpstext = font.render(str(round(clock.get_fps(), 2)), True, white)
  pointstext = font.render(str(len(points)), True, white)
  
  for rect in rects:
    pg.draw.rect(surf, blue, rect, 1)
  
  kdtree = KdTree(points, 0, 800, 0, 800)
  kdtree.draw()
  orig.draw(color=white,radius=3)
  
  dx = mpos.x - orig.x
  dy = mpos.y - orig.y
  d = dx, dy
  d = normalize(d)
  inter = kdtree.intersection(orig, d)
  if inter:
    start, end = inter
    kdtree.traverse(orig, d, start, end)
  
  for point in points:
    point.draw()
    # rectIntersect(point, orig, d)
  
  keys = pg.key.get_pressed()
  for event in pg.event.get():
    if event.type == QUIT:
      pg.quit()
      sys.exit()
    if pg.mouse.get_pressed()[0]: 
      points.append(mpos)
      rects.append(newRect(mpos))
      kdtree = KdTree(points, 0, 800, 0, 800)
    if pg.mouse.get_pressed()[2]:
      orig = mpos
    if keys[pg.K_BACKSPACE]:
      points.clear()
      rects.clear()
      kdtree = KdTree(points, 0, 800, 0, 800)
    if keys[pg.K_r]:
      for i in range(100):
        newpoint = Point(randint(0, 799), randint(0, 799))
        points.append(newpoint)
        rects.append(newRect(newpoint))
  surf.blit(fpstext, (5, 5))
  surf.blit(pointstext, (5, 40))
  pg.display.flip()
  clock.tick(60)