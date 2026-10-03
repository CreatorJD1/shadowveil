const {openRig,renderPose}=require('./lib');const fs=require('fs');
(async()=>{const {b,pg,errs}=await openRig('apose');
const info=await pg.evaluate(()=>({ha:R.handAngles?Object.keys(R.handAngles):null,twist:R.twist?Object.keys(R.twist):null,hs:window.RigTwist?.handState('L'),feet:R.feet&&Object.keys(R.feet)}));console.log(JSON.stringify(info).slice(0,1500));
const T=[['rest',{}],['ShL+',{ShoulderL:1}],['ShL-',{ShoulderL:-1}],['ShR+',{ShoulderR:1}],['ElL+',{ElbowL:1}],['ElR+',{ElbowR:1}],['HipL+',{HipL:1}],['HipR+',{HipR:1}],['Lean+',{BodyLean:1}],['Tilt+',{HeadTilt:1}],['Nod+',{HeadNod:1}],['WrL+',{WristL:1}],['WTwL+',{WristTwistL:1}],['WTwL.5',{WristTwistL:0.5}],['NeckTw+',{NeckTwist:1}],['KneeL+',{KneeL:1}]];
fs.mkdirSync('/tmp/bmdirs',{recursive:true});
for(const [t,vv] of T){const r=await renderPose(pg,vv);fs.writeFileSync('/tmp/bmdirs/'+t+'.png',Buffer.from(r.url.split(',')[1],'base64'))}
console.log('errs',errs);await b.close()})();
