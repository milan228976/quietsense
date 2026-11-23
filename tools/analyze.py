"""Dependency-light CAE: nodal AC, exact state-space step, seeded tolerance analysis."""
from pathlib import Path
import json, csv
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation'/'results'; DATA.mkdir(parents=True,exist_ok=True)
IMG=ROOT/'docs'/'images'; IMG.mkdir(parents=True,exist_ok=True)
BG='#0c1424'; FG='#e5edf8'; MUTED='#8ea5bf'; BLUE='#57c8ff'; GREEN='#69e0b6'; GOLD='#ffc66b'
def font(n):
    for f in ['C:/Windows/Fonts/segoeui.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        if Path(f).exists():return ImageFont.truetype(f,n)
    return ImageFont.load_default()
def canvas(title,sub):
    im=Image.new('RGB',(1600,1000),BG);d=ImageDraw.Draw(im)
    d.text((75,40),'QUIETSENSE  /  ИНЖЕНЕРНЫЙ ПРОЕКТ',font=font(19),fill=GREEN)
    d.text((75,85),title,font=font(40),fill=FG);d.text((75,150),sub,font=font(21),fill=MUTED)
    return im,d
def graph(d,box,xlim,ylim,xticks,yticks,log=False):
    l,t,r,b=box
    def xy(x,y):
        if log:x=np.log10(x)
        return l+(x-xlim[0])/(xlim[1]-xlim[0])*(r-l),b-(y-ylim[0])/(ylim[1]-ylim[0])*(b-t)
    for x,label in xticks:
        xx,_=xy(x,ylim[0]);d.line((xx,t,xx,b),fill='#23344b',width=1);d.text((xx-20,b+14),str(label),font=font(18),fill=MUTED)
    for y in yticks:
        _,yy=xy(10**xlim[0] if log else xlim[0],y);d.line((l,yy,r,yy),fill='#23344b',width=1);d.text((l-52,yy-11),str(y).replace('.',','),font=font(18),fill=MUTED)
    return xy
def curve(d,xy,x,y,color,width=4):d.line([xy(float(a),float(b)) for a,b in zip(x,y)],fill=color,width=width)
def h(f,r1=1000.,r2=1000.,c1=1e-7,c2=1e-7,rs=0.,rl=np.inf):
    # Eliminate node MID from the actual two-node Kirchhoff equations.
    s=2j*np.pi*f;g1=1/(r1+rs);g2=1/r2;gl=1/rl
    return g1*g2/((g1+g2+s*c1)*(g2+gl+s*c2)-g2*g2)
def cutoff(r1=1000.,r2=1000.,c1=1e-7,c2=1e-7,rs=0.,rl=np.inf):
    lo=np.full(np.broadcast(r1,r2,c1,c2).shape,1.);hi=lo*1e5
    target=abs(h(0,r1,r2,c1,c2,rs,rl))/np.sqrt(2)
    for _ in range(45):
        mid=np.sqrt(lo*hi);above=abs(h(mid,r1,r2,c1,c2,rs,rl))>target;lo=np.where(above,mid,lo);hi=np.where(above,hi,mid)
    return np.sqrt(lo*hi)
def main():
    f=np.logspace(0,5,1201);hh=h(f);db=20*np.log10(abs(hh));phase=np.angle(hh,deg=True)
    closed=1/(1+3j*2*np.pi*f*1e-4+(1j*2*np.pi*f*1e-4)**2)
    assert np.max(abs(hh-closed))<1e-12
    rng=np.random.default_rng(20261123);n=10000
    rr=rng.uniform(.99,1.01,(2,n))*1000;cc=rng.uniform(.95,1.05,(2,n))*1e-7
    fc=cutoff(*rr,*cc);nom=float(cutoff());q=np.percentile(fc,[2.5,50,97.5])
    A=np.array([[-20000.,10000.],[10000.,-10000.]]);eig,V=np.linalg.eig(A)
    t=np.linspace(0,.002,1601);coef=np.linalg.solve(V,np.array([-1.,-1.]));out=np.real_if_close(1+(V@(coef[:,None]*np.exp(eig[:,None]*t)))[1])
    settle=float(t[np.where(out>=.99)[0][0]])
    assert np.all(np.diff(out)>=-1e-12) and abs(out[0])<1e-12
    cases={}
    for name,rs,rl in [('ideal',0,np.inf),('recommended',100,100000),('heavy_10k_load',100,10000)]:
        cases[name]={'source_ohm':rs,'load_ohm':None if np.isinf(rl) else rl,'dc_gain':float(abs(h(0,rs=rs,rl=rl))),'cutoff_hz_relative_to_dc':float(cutoff(rs=rs,rl=rl)),'gain_10khz_db':float(20*np.log10(abs(h(10000,rs=rs,rl=rl))))}
    report={'method':'Complex nodal AC and exact eigendecomposition of linear state space; not a SPICE run','nominal_cutoff_hz':nom,'gain_10khz_db':float(20*np.log10(abs(h(10000)))),'step_99_percent_ms':settle*1000,'monte_carlo':{'n':n,'seed':20261123,'distribution':'Independent uniform R +/-1%, C +/-5%; unloaded, Rs=0','p2_5_median_p97_5_hz':q.tolist(),'observed_min_max_hz':[float(fc.min()),float(fc.max())]},'corners_hz':{'all_RC_high':float(cutoff(1010,1010,105e-9,105e-9)),'all_RC_low':float(cutoff(990,990,95e-9,95e-9))},'load_cases':cases,'checks':{'closed_form_max_complex_error':float(np.max(abs(hh-closed))),'monotonic_step':True,'unloaded_dc_gain':float(abs(h(0)))}}
    (DATA/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
    for name,headers,cols in [('ac.csv',['frequency_hz','gain_db','phase_deg'],[f,db,phase]),('step.csv',['time_s','vout_for_1V_step'],[t,out]),('monte_carlo.csv',['r1_ohm','r2_ohm','c1_f','c2_f','cutoff_hz'],[*rr,*cc,fc])]:
        with (DATA/name).open('w',newline='') as o:w=csv.writer(o);w.writerow(headers);w.writerows(zip(*cols))
    im,d=canvas('Два полюса. С учётом взаимной нагрузки.','Частотная характеристика пассивной RC-цепи. R1 = R2 = 1 кОм; C1 = C2 = 100 нФ.')
    xy=graph(d,(140,310,1480,780),(0,5),(-75,2),[(10**i,f'{10**i:g}') for i in range(6)],[0,-15,-30,-45,-60,-75],True)
    curve(d,xy,f,db,BLUE)
    loaded=20*np.log10(abs(h(f,rs=100,rl=1e5)));curve(d,xy,f,loaded,GOLD,3)
    xx,yy=xy(nom,-3.0103);d.ellipse((xx-7,yy-7,xx+7,yy+7),fill=GREEN)
    d.text((140,207),f'Срез −3 дБ: {nom:.1f} Гц'.replace('.',','),font=font(28),fill=GREEN)
    d.text((850,207),f'На 10 кГц: {report["gain_10khz_db"]:.1f} дБ'.replace('.',','),font=font(28),fill=FG)
    d.text((140,263),'Голубая: идеальная цепь. Золотая: источник 100 Ом, нагрузка 100 кОм.',font=font(21),fill=GOLD)
    d.text((580,835),'Частота, Гц • логарифмическая шкала',font=font(22),fill=MUTED)
    d.text((50,230),'дБ',font=font(21),fill=MUTED)
    d.text((100,920),'CAE: узловой расчёт • 1 201 точка • результат совпал с аналитической формулой',font=font(21),fill=MUTED)
    im.save(IMG/'02-ac-response.png')
    im,d=canvas('Переходный процесс без перерегулирования','Точное решение линейной модели при скачке входа 0 → 1 В. Идеальный источник; выход без нагрузки.')
    xy=graph(d,(140,290,1480,780),(0,2),(0,1.05),[(v,str(v).replace('.',',')) for v in [0,.5,1,1.5,2]],[0,.25,.5,.75,1])
    curve(d,xy,t*1000,out,GREEN);d.text((140,210),f'Установление до 99%: {settle*1000:.3f} мс'.replace('.',','),font=font(29),fill=GREEN)
    d.text((50,250),'В',font=font(21),fill=MUTED)
    d.text((610,840),'Время, мс',font=font(22),fill=MUTED);d.text((100,920),'Паразитные параметры и импульсная нагрузка входа АЦП в эту модель не включены.',font=font(21),fill=MUTED)
    im.save(IMG/'03-step-response.png')
    im,d=canvas('Как допуски меняют частоту среза?','10 000 прогонов • R: ±1% • C: ±5% • равномерные независимые допуски • фиксированная выборка')
    counts,edges=np.histogram(fc,bins=50)
    xy=graph(d,(140,290,1480,780),(550,650),(0,float(counts.max()*1.2)),[(v,str(v)) for v in [550,575,600,625,650]],[0,100,200,300,400])
    for i,count in enumerate(counts):
        x1,y1=xy(edges[i],count);x2,y2=xy(edges[i+1],0);d.rectangle((x1+1,y1,x2-1,y2),fill=BLUE)
    d.text((140,210),f'Центральные 95% результатов: {q[0]:.1f}–{q[2]:.1f} Гц'.replace('.',','),font=font(28),fill=GREEN)
    d.text((40,250),'Число прогонов',font=font(18),fill=MUTED)
    d.text((600,840),'Частота среза, Гц',font=font(22),fill=MUTED)
    d.text((100,920),'Результат для заданных допусков; статистический интервал не гарантирует выход годных.',font=font(20),fill=MUTED)
    im.save(IMG/'04-tolerances.png')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
