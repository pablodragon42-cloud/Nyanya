# Procedural ambient score + transition whooshes (original, generated).
import numpy as np, soundfile as sf
from scipy.signal import lfilter, butter, sosfilt
SR=44100; DUR=106.0; N=int(SR*DUR); t=np.arange(N)/SR
rng=np.random.default_rng(3); L=np.zeros(N); R=np.zeros(N)
midi=lambda m:440*2**((m-69)/12)
def add(sig,start,g=1.0,pan=0.0):
    i=int(start*SR); sig=sig[:max(0,N-i)]
    L[i:i+len(sig)]+=sig*g*np.sqrt((1-pan)/2); R[i:i+len(sig)]+=sig*g*np.sqrt((1+pan)/2)
def env(n,a,r):
    e=np.ones(n); na,nr=int(a*SR),int(r*SR); e[:na]=np.linspace(0,1,na); e[-nr:]*=np.linspace(1,0,nr); return e
def lp(x,f,o=2): return sosfilt(butter(o,f,'low',fs=SR,output='sos'),x)
def hp(x,f,o=2): return sosfilt(butter(o,f,'high',fs=SR,output='sos'),x)
def padv(notes,start,dur,g,cut=1100):
    n=int(dur*SR); tt=np.arange(n)/SR; s=np.zeros(n)
    for m in notes:
        for d in (-0.005,0,0.006):
            ph=(tt*midi(m)*(1+d))%1; s+=2*ph-1
    s=lp(s/len(notes)/3,cut)*env(n,2.0,2.5)
    s*=1+0.15*np.sin(2*np.pi*0.2*tt)
    add(s,start,g,-0.35); add(np.roll(s,int(0.017*SR)),start,g*0.9,0.35)
# chord plan (narration time +1s)
prog=[([50,57,62,65],0),([46,53,58,62],8),([41,53,57,60],16),([48,55,60,64],24),
      ([50,57,62,65],32),([46,53,58,62],40),([43,50,55,58],48),([45,52,57,61],56),
      ([50,57,62,65],64),([46,53,58,62],72),([41,53,57,60],80),([48,55,60,64],88),([50,57,62,66],96)]
for notes,st in prog:
    padv(notes,st,10.5 if st<96 else 10.0,0.16)
    padv([notes[0]-12],st,10.5 if st<96 else 10.0,0.10,cut=300)
# shimmering arpeggio bells in the middle part
for k in range(0,int(96/0.5)):
    st=k*0.5
    if st<6: continue
    notes,_=[p for p in prog if p[1]<=st][-1]
    m=notes[k%4]+24; n=int(1.6*SR); tt=np.arange(n)/SR
    b=np.sin(2*np.pi*midi(m)*tt)*np.exp(-tt*3.2)+0.3*np.sin(2*np.pi*midi(m)*2.01*tt)*np.exp(-tt*5)
    add(b,st,0.022*(0.6+0.4*np.sin(k*0.7)),np.sin(k*1.3)*0.6)
# heartbeat in intro & finale
for st in np.arange(0.4,7.0,0.85).tolist()+np.arange(93.6,104,0.85).tolist():
    for o,g in ((0,1),(0.22,0.6)):
        n=int(0.35*SR); tt=np.arange(n)/SR; s=np.sin(2*np.pi*(55-20*tt)*tt)*np.exp(-tt*14)
        add(s,st+o,0.35*g)
# whooshes at scene changes
for b in [6.4,12.95,17.65,26.45,37.8,45.6,51.5,61.4,78.0,88.4,92.6]:
    n=int(1.6*SR); tt=np.arange(n)/SR; x=rng.standard_normal(n)
    sweep=np.exp(-((tt-0.8)/0.35)**2)
    y=lp(hp(x,300),2500)*sweep
    add(y,b+1.0-0.8,0.05,0.0)
mix=np.stack([L,R],1)
fade=np.ones(N); fi=int(1.0*SR); fo=int(3.0*SR); fade[:fi]=np.linspace(0,1,fi); fade[-fo:]=np.linspace(1,0,fo)
mix*=fade[:,None]; mix/=np.abs(mix).max()*1.12
sf.write('music.wav',mix.astype(np.float32),SR)
print('ok')
