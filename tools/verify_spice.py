"""Cross-check the Python model using ngspice shared library or executable."""
from pathlib import Path
import os, sys, ctypes, subprocess, json
import numpy as np
from analyze import h

ROOT=Path(__file__).resolve().parents[1]
def main():
    out=ROOT/'simulation/results';dll=os.environ.get('NGSPICE_DLL')
    text=(ROOT/'simulation/quietsense.cir').read_text();log=[]
    original=os.getcwd();os.chdir(out)
    try:
        if dll:
            directory=os.add_dll_directory(str(Path(dll).parent))
            lib=ctypes.CDLL(dll)
            CALLBACK=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_void_p)
            EXIT=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.c_bool,ctypes.c_bool,ctypes.c_int,ctypes.c_void_p)
            @CALLBACK
            def message(s,i,user):log.append(s.decode(errors='replace'));return 0
            @EXIT
            def exited(status,immediate,quit,i,user):log.append(f'controlled exit {status}');return 0
            lib.ngSpice_Init(message,message,exited,None,None,None,None)
            circuit=text.split('.control')[0]+'.end\n'
            raw=[s.encode() for s in circuit.splitlines()]
            buf=(ctypes.c_char_p*(len(raw)+1))(*raw,None)
            assert lib.ngSpice_Circ(buf)==0
            commands=['version','set wr_singlescale','set wr_vecnames','ac dec 240 1 100k','let gain_db = db(v(out))','let phase_deg = 180/PI*cph(v(out))','wrdata spice_ac.txt gain_db phase_deg','tran 1u 2m','wrdata spice_step.txt v(out)']
            for command in commands:
                code=lib.ngSpice_Command(command.encode())
                if code:raise RuntimeError((command,code))
            backend='ngspice shared library shipped with KiCad 9.0.7'
        else:
            r=subprocess.run(['ngspice','-b',str(ROOT/'simulation/quietsense.cir')],capture_output=True,text=True,check=True)
            log.append(r.stdout+r.stderr);backend='ngspice executable'
        ac=np.loadtxt('spice_ac.txt',skiprows=1)
        delta=float(np.max(np.abs(ac[:,1]-20*np.log10(abs(h(ac[:,0]))))))
        step=np.loadtxt('spice_step.txt',skiprows=1)
        A=np.array([[-20000.,10000.],[10000.,-10000.]])
        eig,V=np.linalg.eig(A);coef=np.linalg.solve(V,[-1.,-1.])
        expected=1+(V@(coef[:,None]*np.exp(eig[:,None]*step[:,0])))[1]
        step_delta=float(np.max(abs(step[:,1]-expected)))
        assert delta<1e-5,(delta,'AC mismatch')
        assert step_delta<.002,(step_delta,'transient mismatch')
        report={'backend':backend,'ac_max_gain_error_db':delta,'transient_max_error_v_for_1V_step':step_delta,'ac_pass_threshold_db':1e-5,'transient_pass_threshold_v':.002,'passed':True,'note':'Transient source has 1ns rise time; SPICE uses adaptive time steps.'}
        (ROOT/'verification/spice.json').write_text(json.dumps(report,indent=2)+'\n')
        (ROOT/'verification/spice.log').write_text('\n'.join(log)+'\n')
        print(json.dumps(report,indent=2))
    finally:os.chdir(original)
if __name__=='__main__':main()
