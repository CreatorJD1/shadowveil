import sys; from seg import *; from defs import D
v,side=sys.argv[1],sys.argv[2]
H=dict(D[v][side]); R=segment_hand(v,H); overlay(v,H,R,s=int(sys.argv[3]) if len(sys.argv)>3 else 5,out=f'ov_{v}_{side}.png')
