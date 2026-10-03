import json
F=json.load(open('../work/fit.json'))['fit']
fist=lambda s,c=1:{f'Hand{s}{f}':c for f in ['Thumb','Index','Middle','Ring','Pinky']}
X={
'1':dict(HeadNod=-1,HeadTilt=-0.5,EyeLOpen=0,EyeROpen=0,MouthOpen=1,MouthForm=1,HandLSpread=0.8,HandRSpread=0.8,HandLThumbSpread=0.6,HandRThumbSpread=0.6),
'2':dict(HeadNod=0.3,HeadTilt=-0.3,EyeLOpen=0.7,EyeROpen=0.7,EyeBallX=0.8,MouthOpen=0,MouthForm=-0.5,**fist('L'),**fist('R',0.3)),
'3':dict(HeadTilt=0.2,MouthOpen=0.1,MouthForm=0.6,**fist('L',0.3),**fist('R',0.3)),
'4':dict(HeadNod=-1,HeadTilt=-0.6,MouthOpen=1,MouthForm=0.6,EyeBallX=0.4,EyeBallY=-0.6,**fist('L'),**fist('R')),
'5':dict(HeadNod=0.3,MouthOpen=1,MouthForm=-0.2,EyeLOpen=0.85,EyeROpen=0.85,**fist('L'),**fist('R')),
'6':dict(HeadNod=1,HeadTilt=0.5,EyeLOpen=0.55,EyeROpen=0.55,EyeBallY=0.7,EyeBallX=-0.2,MouthOpen=0.05,MouthForm=-0.6,**fist('L',0.25),**fist('R',0.25)),
}
jobs=[dict(name='rest_apose',view='apose',values={}),dict(name='rest_tpose',view='tpose',values={}),
      dict(name='signtest_apose',view='apose',values=dict(ShoulderL=0.5,ElbowL=0.5,HipL=0.5,ShoulderR=0.5,HipR=0.5,BodyLean=0.5,HeadTilt=0.5))]
for i,f in F.items():
    jobs.append(dict(name=f'b{i}_legal',view=f['view'],values={**f['legal'],**X[i]}))
    if f['clamp_residual_deg']: jobs.append(dict(name=f'b{i}_stress',view=f['view'],stress=True,values={**f['stress'],**X[i]}))
json.dump(jobs,open('../work/jobs.json','w'),indent=1); json.dump(X,open('../work/extras.json','w'),indent=1); print(len(jobs))
