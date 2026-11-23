"""Render genuine KiCad SVG exports and create Russian portfolio summary cards."""
from pathlib import Path
import os,json
from PIL import Image,ImageDraw
from analyze import canvas,font,FG,MUTED,GREEN,BLUE,BG

ROOT=Path(__file__).resolve().parents[1];IMG=ROOT/'docs/images'
def main():
    if os.name=='nt' and os.environ.get('KICAD_BIN'):
        handle=os.add_dll_directory(os.environ['KICAD_BIN'])
    import cairosvg
    for src,name,width in [('docs/schematic/quietsense.svg','05-schematic.png',2400),('docs/pcb-layout.svg','06-layout.png',1800)]:
        cairosvg.svg2png(url=str(ROOT/src),write_to=str(IMG/name),output_width=width)
    # Crop only page frame/title block; electrical drawing and all design notes remain intact.
    im=Image.open(IMG/'05-schematic.png').convert('RGB');w,h=im.size
    im.crop((int(w*.1),int(h*.12),int(w*.91),int(h*.79))).save(IMG/'05-schematic.png')
    # Keep transparent native geometry, add an opaque dark background for GitHub.
    im=Image.open(IMG/'06-layout.png').convert('RGBA');back=Image.new('RGBA',im.size,BG);back.alpha_composite(im);back.convert('RGB').save(IMG/'06-layout.png')
    report=json.loads((ROOT/'simulation/results/summary.json').read_text())
    erc=json.loads((ROOT/'verification/erc.json').read_text(encoding='utf8'))
    drc=json.loads((ROOT/'verification/drc.json').read_text(encoding='utf8'))
    conn=json.loads((ROOT/'verification/connectivity.json').read_text())
    spice=json.loads((ROOT/'verification/spice.json').read_text())
    assert sum(len(s.get('violations',[])) for s in erc['sheets'])==0
    assert not drc['violations'] and not drc.get('unconnected_items',[])
    assert conn['passed'] and spice['passed']
    im,d=canvas('Проверено перед публикацией','Результаты программных проверок ревизии А. Физический прототип пока не изготовлен.')
    rows=[('CAD • схема','ERC: 0 нарушений'),('CAD • плата','DRC: 0 нарушений; 0 неподключённых цепей'),('Связность','Все выводы схемы совпадают с платой'),('CAE • независимая проверка',f'ngspice: ошибка АЧХ < {spice["ac_max_gain_error_db"]:.1e} дБ'.replace('.',',')),('CAE • допуски','10 000 прогонов + крайние случаи'),('CAM • производство','Gerber + Excellon + BOM + координаты монтажа')]
    for i,(a,b) in enumerate(rows):
        y=240+i*100;d.rounded_rectangle((75,y,1525,y+78),radius=12,fill='#15243a')
        d.text((105,y+22),a,font=font(23),fill=MUTED);d.text((570,y+22),b,font=font(23),fill=GREEN)
    d.text((85,912),'Отчёты сохранены в verification/ • KiCad 9.0.7 • ngspice 45.2',font=font(22),fill=MUTED)
    im.save(IMG/'07-verification.png')
    im=Image.new('RGB',(1600,900),BG);d=ImageDraw.Draw(im)
    d.text((60,55),'QUIETSENSE',font=font(54),fill=FG)
    d.text((60,135),'Фильтр аналогового датчика',font=font(29),fill=GREEN)
    d.text((60,190),'CAD → CAE → CAM',font=font(31),fill=BLUE)
    for i,s in enumerate(['Плата KiCad: 45 × 30 мм',f'Частота среза: {report["nominal_cutoff_hz"]:.1f} Гц'.replace('.',','),'Расчёт, ngspice и допуски','Файлы для производства','Русская документация']):d.text((60,295+i*72),s,font=font(27),fill=FG)
    photo=Image.open(IMG/'01-board.png').convert('RGB');photo.thumbnail((910,710))
    im.paste(photo,(650,140))
    d.text((60,805),'УЧЕБНЫЙ ПРОЕКТ • РЕВ. А • БЕЗ ФИЗИЧЕСКИХ ИЗМЕРЕНИЙ',font=font(22),fill=MUTED)
    im.save(IMG/'00-cover.png')
    print('Russian PNG previews and cover created from CAD exports and verification reports.')
if __name__=='__main__':main()
