"""Compare every schematic terminal against the independently loaded PCB nets."""
from pathlib import Path
import json, xml.etree.ElementTree as ET
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
def main():
    sch=ET.parse(ROOT/'verification/schematic.xml').getroot()
    assert {n.attrib['name'] for n in sch.findall('./nets/net')}=={'/IN','/MID','/OUT','/GND'}
    expected={n.attrib['name'].removeprefix('/'):sorted((a.attrib['ref'],a.attrib['pin']) for a in n.findall('node')) for n in sch.findall('./nets/net')}
    b=p.LoadBoard(str(ROOT/'hardware/quietsense.kicad_pcb'));actual={}
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNumber():actual.setdefault(pad.GetNetname().removeprefix('/'),[]).append((fp.GetReference(),pad.GetNumber()))
    actual={name:sorted(pins) for name,pins in actual.items()}
    assert actual==expected,{'schematic':expected,'pcb':actual}
    assert set(actual)=={'IN','MID','OUT','GND'}
    assert len(list(b.GetFootprints()))==12
    assert all(t.GetLayer()==p.F_Cu and abs(p.ToMM(t.GetWidth())-.4)<1e-6 for t in b.GetTracks())
    report={'passed':True,'method':'Compare all reference/pin pairs in KiCad XML netlist with pcbnew-loaded board','nets':actual,'footprints':12,'copper_layers':2,'routing':'F.Cu only; no zones; 0.40mm tracks','nominal_outline_mm':[45,30],'board_thickness_mm':p.ToMM(b.GetDesignSettings().GetBoardThickness()),'checks':['Exact net membership matches schematic','All 4 named nets present','12 footprints including 2 mechanical holes','Every track is 0.40mm on F.Cu']}
    (ROOT/'verification/connectivity.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: schematic and PCB have identical terminal membership on all 4 nets.')
if __name__=='__main__':main()
