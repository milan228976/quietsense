"""Generate the editable KiCad PCB and schematic. Run with KiCad's Python/pcbnew."""
from pathlib import Path
import json, uuid
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / 'hardware'; CAD.mkdir(exist_ok=True)
uid = lambda: str(uuid.uuid4())

def board(symbol_paths):
    b = p.BOARD()
    nets = {}
    for name in ['GND', 'IN', 'MID', 'OUT']:
        n = p.NETINFO_ITEM(b, '/'+name); b.Add(n); nets[name] = n
    import os, shutil, re
    lib = Path(os.environ.get('KICAD_FOOTPRINT_DIR','/usr/share/kicad/footprints'))
    parts = [
        ('J1','ВХОД / GND','Connector_PinHeader_2.54mm','PinHeader_1x02_P2.54mm_Vertical',104,94,0,['IN','GND']),
        ('J2','ВЫХОД / GND','Connector_PinHeader_2.54mm','PinHeader_1x02_P2.54mm_Vertical',141,94,0,['OUT','GND']),
        ('R1','1 кОм / 1%','Resistor_SMD','R_0805_2012Metric',114,94,0,['IN','MID']),
        ('R2','1 кОм / 1%','Resistor_SMD','R_0805_2012Metric',128,94,0,['MID','OUT']),
        ('C1','100 нФ / 5%','Capacitor_SMD','C_0805_2012Metric',120,99,270,['MID','GND']),
        ('C2','100 нФ / 5%','Capacitor_SMD','C_0805_2012Metric',134,99,270,['OUT','GND']),
    ]
    for ref, net, x, y in [('TP1','IN',108,90),('TP2','MID',120,90),('TP3','OUT',134,90),('TP4','GND',128,103)]:
        parts.append((ref,net,'TestPoint','TestPoint_Pad_D2.0mm',x,y,0,[net]))
    positions = {}
    tables=[]
    for library in ['Resistor_SMD','Capacitor_SMD','TestPoint','Connector_PinHeader_2.54mm','MountingHole']:
        target=CAD/'footprints'/(library+'.pretty');target.mkdir(parents=True,exist_ok=True)
        needed={part[3] for part in parts if part[2]==library}
        if library=='MountingHole':needed.add('MountingHole_2.7mm_M2.5')
        for original in (lib/(library+'.pretty')).glob('*.kicad_mod'):
            if original.stem not in needed:continue
            content=original.read_text()
            content=re.sub(r'\$\{KICAD9_3DMODEL_DIR\}/[^/]+/', '${KIPRJMOD}/models/',content)
            (target/original.name).write_text(content)
        tables.append(f'(lib (name "{library}") (type "KiCad") (uri "${{KIPRJMOD}}/footprints/{library}.pretty") (options "") (descr "Bundled KiCad footprint"))')
    models=lib.parent/'3dmodels'
    (CAD/'models').mkdir(exist_ok=True)
    for library,filename in [('Resistor_SMD','R_0805_2012Metric.step'),('Capacitor_SMD','C_0805_2012Metric.step'),('Connector_PinHeader_2.54mm','PinHeader_1x02_P2.54mm_Vertical.step')]:
        source=models/(library+'.3dshapes')/filename
        if source.exists():shutil.copyfile(source,CAD/'models'/filename)
    (CAD/'fp-lib-table').write_text('(fp_lib_table (version 7)'+''.join(tables)+')')
    lib=CAD/'footprints'
    for ref,val,library,foot,x,y,angle,padnets in parts:
        fp = p.FootprintLoad(str(lib / (library+'.pretty')),foot)
        if fp is None: raise RuntimeError(foot)
        fp.SetReference(ref); fp.SetValue(val); fp.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
        fp.SetOrientationDegrees(angle)
        fp.SetFPID(p.LIB_ID(library,foot))
        path=p.KIID_PATH()
        for ident in symbol_paths[ref]:path.push_back(p.KIID(ident))
        fp.SetPath(path)
        fp.Value().SetVisible(False)
        b.Add(fp)
        for pad in fp.Pads():
            n = int(pad.GetNumber())
            pad.SetNet(nets[padnets[n-1]])
            positions[(ref,n)] = (p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y))
        refx,refy=(x-2.5,y-5) if ref.startswith('J') else (x,y-2.7)
        fp.Reference().SetPosition(p.VECTOR2I(p.FromMM(refx),p.FromMM(refy)))
        fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
        fp.Reference().SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)))
        fp.Reference().SetTextThickness(p.FromMM(.12))
    for ref,x,y in [('H1',103,83),('H2',142,107)]:
        fp=p.FootprintLoad(str(lib/'MountingHole.pretty'),'MountingHole_2.7mm_M2.5')
        fp.SetReference(ref);fp.SetValue('M2.5');fp.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
        fp.SetFPID(p.LIB_ID('MountingHole','MountingHole_2.7mm_M2.5'))
        fp.SetAttributes(fp.GetAttributes() | p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
        fp.Reference().SetVisible(False);fp.Value().SetVisible(False);b.Add(fp)
    def line(a,z,net,layer=p.F_Cu,width=.4):
        t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])))
        t.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(nets[net]);b.Add(t)
    def path(net,*points):
        for a,z in zip(points,points[1:]):line(a,z,net)
    path('IN',positions['J1',1],positions['R1',1])
    path('MID',positions['R1',2],positions['R2',1])
    path('OUT',positions['R2',2],positions['J2',1])
    for ref,net,x in [('TP1','IN',108),('TP2','MID',120),('TP3','OUT',134)]:path(net,positions[ref,1],(x,94))
    for ref,net in [('C1','MID'),('C2','OUT')]:
        a=positions[ref,1];path(net,(a[0],94),a)
    for ref in ['J1','J2','C1','C2']:
        a=positions[ref,2];path('GND',a,(a[0],103))
    path('GND',(104,103),(141,103))
    for a,z in [((100,80),(145,80)),((145,80),(145,110)),((145,110),(100,110)),((100,110),(100,80))]:
        sh=p.PCB_SHAPE();sh.SetShape(p.SHAPE_T_SEGMENT);sh.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));sh.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));sh.SetLayer(p.Edge_Cuts);sh.SetWidth(p.FromMM(.05));b.Add(sh)
    for text,x,y,size in [('QUIETSENSE',123,83,1.5),('ФИЛЬТР ДАТЧИКА',123,85.5,.8),('ВХОД',104,91,.8),('ВЫХОД',141,91,.8),('GND',107.5,98,.8),('GND',138,98,.8),('2 x RC | 1 кОм / 100 нФ',120,106,.9),('РЕВ. А  /  45 x 30 мм',120,108,.8)]:
        size=max(.8,size)
        t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.12));t.SetLayer(p.F_SilkS);b.Add(t)
    p.SaveBoard(str(CAD/'quietsense.kicad_pcb'),b)
    (CAD/'placement.json').write_text(json.dumps({'pads':{f'{r}.{n}':xy for (r,n),xy in positions.items()},'outline_mm':[100,80,145,110]},indent=2))

def schematic():
    # Self-contained schematic: embedded symbols, no external symbol libraries required.
    root=uid(); symbols=[]; instances=[]; schpins={}; symbol_paths={}
    def lib(name,ref,shape,pins):
        ps=''.join(f'(pin passive line (at {x} {y} {a}) (length 2.54) (name "{n}" (effects (font (size 1 1)))) (number "{num}" (effects (font (size 1 1)))))' for num,n,x,y,a in pins)
        symbols.append(f'(symbol "QS:{name}" (pin_names (offset 0) hide) (in_bom yes) (on_board yes) (property "Reference" "{ref}" (at 0 4 0) (effects (font (size 1.27 1.27)))) (property "Value" "{name}" (at 0 -4 0) (effects (font (size 1.27 1.27)))) (symbol "{name}_0_1" {shape}) (symbol "{name}_1_1" {ps}))')
    lib('R','R','(rectangle (start -2.54 1.016) (end 2.54 -1.016) (stroke (width 0.254) (type default)) (fill (type none)))',[(1,'1',-5.08,0,0),(2,'2',5.08,0,180)])
    lib('C','C','(polyline (pts (xy -2.54 1.27) (xy 2.54 1.27)) (stroke (width .254) (type default)) (fill (type none))) (polyline (pts (xy -2.54 -1.27) (xy 2.54 -1.27)) (stroke (width .254) (type default)) (fill (type none)))',[(1,'1',0,3.81,270),(2,'2',0,-3.81,90)])
    lib('Port','J','(rectangle (start -1.27 1.27) (end 2.54 -3.81) (stroke (width .254) (type default)) (fill (type none)))',[(1,'SIG',-3.81,0,0),(2,'GND',-3.81,-2.54,0)])
    lib('Input','J','(rectangle (start -2.54 1.27) (end 1.27 -3.81) (stroke (width .254) (type default)) (fill (type none)))',[(1,'SIG',3.81,0,180),(2,'GND',3.81,-2.54,180)])
    lib('TP','TP','(circle (center 0 1) (radius 1) (stroke (width .254) (type default)) (fill (type none)))',[(1,'1',0,-2.54,90)])
    labels=[]
    def label(net,x,y):labels.append(f'(label "{net}" (at {x} {y} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid {uid()}))')
    def put(name,ref,val,x,y,pins,foot):
        x=round(round(x/1.27)*1.27,4); y=round(round(y/1.27)*1.27,4)
        ident=uid();symbol_paths[ref]=[root,ident]
        props=''.join(f'(property "{k}" "{v}" (at {x} {y+dy} 0) (effects (font (size 1.27 1.27)){hide}))' for k,v,dy,hide in [('Reference',ref,-5,''),('Value',val,5,''),('Footprint',foot,0,' hide')])
        in_bom='no' if name=='TP' else 'yes'
        instances.append(f'(symbol (lib_id "QS:{name}") (at {x} {y} 0) (unit 1) (in_bom {in_bom}) (on_board yes) (dnp no) (uuid {ident}) {props} '+''.join(f'(pin "{n}" (uuid {uid()}))' for n in range(1,len(pins)+1))+f' (instances (project "quietsense" (path "/{root}" (reference "{ref}") (unit 1)))))')
        for number,(dx,dy,net) in enumerate(pins,1):
            xx,yy=round(x+dx,3),round(y+dy,3);schpins[ref,number]=(xx,yy);label(net,xx,yy)
    put('R','R1','1 кОм / 1%',85,75,[(-5.08,0,'IN'),(5.08,0,'MID')],'Resistor_SMD:R_0805_2012Metric')
    put('R','R2','1 кОм / 1%',135,75,[(-5.08,0,'MID'),(5.08,0,'OUT')],'Resistor_SMD:R_0805_2012Metric')
    for ref,x,net in [('C1',110,'MID'),('C2',160,'OUT')]:put('C',ref,'100 нФ / 5%',x,100,[(0,-3.81,net),(0,3.81,'GND')],'Capacitor_SMD:C_0805_2012Metric')
    put('Input','J1','ВХОД / GND',50,75,[(3.81,0,'IN'),(3.81,2.54,'GND')],'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical')
    put('Port','J2','ВЫХОД / GND',195,75,[(-3.81,0,'OUT'),(-3.81,2.54,'GND')],'Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical')
    for ref,x,net in [('TP1',70,'IN'),('TP2',110,'MID'),('TP3',150,'OUT'),('TP4',190,'GND')]:put('TP',ref,net,x,130,[(0,2.54,net)],'TestPoint:TestPoint_Pad_D2.0mm')
    labels=[];wires=[];junctions=[]
    def wire(*points):
        for a,z in zip(points,points[1:]):
            wires.append(f'(wire (pts (xy {a[0]} {a[1]}) (xy {z[0]} {z[1]})) (stroke (width 0) (type default)) (uuid {uid()}))')
    signal_y=schpins['R1',1][1];gx=schpins['J1',2][0];ground_y=114.3
    mid=(schpins['C1',1][0],signal_y);out=(schpins['C2',1][0],signal_y)
    wire(schpins['J1',1],schpins['R1',1])
    wire(schpins['R1',2],mid,schpins['R2',1]);wire(mid,schpins['C1',1])
    wire(schpins['R2',2],out,schpins['J2',1]);wire(out,schpins['C2',1])
    ground_nodes=[(schpins[r,2][0],ground_y) for r in ['J1','C1','C2','J2']]
    wire(*ground_nodes)
    for ref,node in zip(['J1','C1','C2','J2'],ground_nodes):wire(schpins[ref,2],node)
    for point in [mid,out,*ground_nodes[1:-1]]:
        junctions.append(f'(junction (at {point[0]} {point[1]}) (diameter 0) (color 0 0 0 0) (uuid {uid()}))')
    for net,point in [('IN',schpins['J1',1]),('MID',mid),('OUT',out),('GND',ground_nodes[0])]:label(net,*point)
    for ref,net in [('TP1','IN'),('TP2','MID'),('TP3','OUT'),('TP4','GND')]:label(net,*schpins[ref,1])
    texts=''.join(f'(text "{s}" (at 35 {y} 0) (effects (font (size {size} {size})) (justify left)) (uuid {uid()}))' for s,y,size in [('QUIETSENSE | Пассивный фильтр датчика второго порядка',35,2),('R1 = R2 = 1 кОм; C1 = C2 = 100 нФ. Одинаковые метки соединяют цепи.',45,1.27),('Источник <= 100 Ом; нагрузка >= 100 кОм. Отдельное питание не требуется.',52,1.27),('TP1 — вход; TP2 — средняя точка; TP3 — выход; TP4 — общая земля GND.',150,1.27),('Без нагрузки: H(s) = 1 / (1 + 3sRC + (sRC)^2). Учтено взаимное влияние звеньев.',160,1.27)])
    (CAD/'QS.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "quietsense")'+''.join(symbols).replace('(symbol "QS:', '(symbol "')+')')
    (CAD/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "QS") (type "KiCad") (uri "${KIPRJMOD}/QS.kicad_sym") (options "") (descr "QuietSense passive symbols")))')
    (CAD/'quietsense.kicad_sch').write_text(f'(kicad_sch (version 20250114) (generator "quietsense") (uuid {root}) (paper "A4") (lib_symbols {"".join(symbols)}) {"".join(instances)} {"".join(labels)} {"".join(wires)} {"".join(junctions)} {texts})',encoding='utf8')
    return symbol_paths

if __name__=='__main__':board(schematic())
