"""Re-run KiCad checks and production exports. No shell, no suppressed failures."""
from pathlib import Path
import subprocess, os

ROOT=Path(__file__).resolve().parents[1]
CLI=os.environ.get('KICAD_CLI','kicad-cli')
def run(*args):
    r=subprocess.run([CLI,*map(str,args)],cwd=ROOT,text=True,capture_output=True)
    if r.returncode:
        raise RuntimeError(' '.join(map(str,args))+'\n'+r.stdout+r.stderr)
    return r.stdout+r.stderr
def main():
    v=ROOT/'verification';v.mkdir(exist_ok=True)
    m=ROOT/'manufacturing';(m/'gerber').mkdir(exist_ok=True,parents=True);(m/'drill').mkdir(exist_ok=True)
    s=ROOT/'hardware/quietsense.kicad_sch';b=ROOT/'hardware/quietsense.kicad_pcb'
    log=[run('version')]
    log.append(run('sch','erc','--exit-code-violations','--format','json','-o',v/'erc.json',s))
    log.append(run('pcb','drc','--schematic-parity','--exit-code-violations','--format','json','-o',v/'drc.json',b))
    log.append(run('sch','export','svg','-o',ROOT/'docs/schematic',s))
    log.append(run('sch','export','pdf','-o',ROOT/'docs/schematic.pdf',s))
    log.append(run('sch','export','netlist','--format','kicadxml','-o',v/'schematic.xml',s))
    log.append(run('pcb','export','gerbers','-o',str(m/'gerber')+os.sep,'-l','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts',b))
    log.append(run('pcb','export','drill','--generate-map','--map-format','svg','-o',str(m/'drill')+os.sep,b))
    log.append(run('pcb','export','pos','--format','csv','--units','mm','--side','front','--smd-only','-o',m/'placement-top.csv',b))
    log.append(run('pcb','export','svg','--mode-single','--page-size-mode','2','--exclude-drawing-sheet','-l','F.Cu,F.Silkscreen,Edge.Cuts','-o',ROOT/'docs/pcb-layout.svg',b))
    (v/'export.log').write_text('\n'.join(log),encoding='utf8')
    print('ERC, DRC and CAM exports completed.')
if __name__=='__main__':main()
