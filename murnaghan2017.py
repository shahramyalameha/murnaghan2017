#!/bin/env python
import shutil
import os 
import sys
import glob
import numpy as np

def main():
    """
    Sets up and runs lattice parameter sweep.

    The generate_lattice_constants function is provided for convenience.
    Alternatively, abc can be created manually. It should be
    an Nx3 numpy array.
    for 2d materials, it is best not to vary layer spacing, so setting 
    two_dim=True will leave lattice paramter c fixed during sweep
    abc = generate_lattice_constants(abc_guess, max_pert, N, two_dim=True)
    """
    # User inputs
    angles = [90, 90,120]  # lattice vector angles: alpha, beta, gamma
    abc_guess = [4, 4, 6]  # lattice parameters guess: a, b, c 
    max_pert = 0.05  # max perturbation of lattice parameters
    N = 7 # number of steps in lattice parameter sweep
    energy_driver = 'abinit'  # dft code to use

    # Set up and run lattice parameter sweep
    abc = generate_lattice_constants(abc_guess, max_pert, N)  # or create abc manually
    raw_energy_data = run_energy_calculations(abc, angles, energy_driver)
    write_results(raw_energy_data)

    # Fit energy/volume data to Murnaghan equation of state
    fit_data = murnaghan_fit(raw_energy_data)

    # optionally, plot data
    # maybe_plot_or_something()


def generate_lattice_constants(abc_guess, max_pert, N, two_dim=False):
    """
    generates an Nx3 numpy array containing the three lattice constants for each energy calculation. 
    Each value will range from (1-max_pert)*abc_guess[i] to (1+max_pert)*abc_guess[i].

    two_dim: if true, will only scale abc_guess[0] and abc_guess[1].
        Useful for 2d materials where layer spacing should remain constant.
    abc_guess: guess of lattice constants a, b, and c (list or numpy array)
    max_pert: the amount to perturb the lattice constants, eg. 0.05 means +-5%
    N: number of steps 
    """
    abc_guess = np.array(abc_guess)
    pert_list = np.linspace(1-max_pert, 1+max_pert, N)
    abc = np.array([pert*abc_guess for pert in pert_list])
    if two_dim:
        abc[:,2] = abc_guess[2] # third lattice parameter not varied
    return abc


def run_energy_calculations(abc, angles, energy_driver):
    """
    Uses DFT code to calculate energy at each of the lattice constants specified.

    For each lattice constant in sweep, sets up directory and runs dft code in that directory.
    """  
    # remove old work directories
    for f in glob.glob('workdir.*'):
        shutil.rmtree(f)
    
    # run dft calculations and return calculated energies
    main_dir = os.getcwd()
    energy_list_hartree = []
    for i,s in enumerate(abc):
        dir_name = 'workdir.'+str(i)
        os.mkdir(dir_name)
        os.chdir(dir_name)
        # preprocess_file(s, angles, template_file, energy_driver)
        # run_dft
        os.chdir(main_dir)
        #energy_list_hartree.append(abinit_get_energy())
    return energy_list_hartree

def fit_to_murnaghan(vol_array, E_array):
        ### first, fit a parabola to the data
        # y = ax^2 + bx + c
        a, b, c = np.polyfit(vol_array, E_array, 2)
        #
        # the parabola does not fit the data very well, but we can use it to get
        # some analytical guesses for other parameters.
        # V0 = minimum energy volume, or where dE/dV=0
        # E = aV^2 + bV + c
        # dE/dV = 2aV + b = 0
        # V0 = -b/2a
        # E0 is the minimum energy, which is:
        # E0 = aV0^2 + bV0 + c
        # B is equal to V0*d^2E/dV^2, which is just 2a*V0
        # and from experience we know Bprime_0 is usually a small number like 4
        V0_guess = -b/(2*a)
        E0_guess = a*V0_guess**2. + b*V0_guess + c
        B0_guess = 2.*a*V0_guess
        BP_guess = 4.

        murnpars_guess = [E0_guess, B0_guess, BP_guess, V0_guess]
        murnpars = leastsq(objective, murnpars_guess, args=(E_array,vol_array))
        return murnpars

def run_abinit():
    #call abinit
    with open('log', 'w') as log_fout, open('files','r') as files_fin:
        #subprocess.call(['srun', '-n', '64', 'abinit'], stdin=files_fin, stdout=log_fout)
        subprocess.call(['abinit'], stdin=files_fin, stdout=log_fout)
 
    # read energy from log
    energy = abinit_get_energy()

def abinit_get_energy():
    with open('log', 'r') as log_fin:
        for line in log_fin.readlines():
            if ' etotal ' in line:
                abinit_energy_hartree = np.float(line.split()[1])
    return abinit_energy_hartree

def read_energy_results():
    """
    gets total energy from abinit output in all wrokdirs
    """
    pass


def preprocess_file(s, angles, template_file, energy_driver):
    """
    wraps the specific file preprocess functions for different dft codes
    """
    if energy_driver=='abinit':
        _preprocess_file_abinit(s, angles, template_file)
    else:
        raise ValueError('Unknown energy driver specified')


def _preprocess_file_abinit(s, angles, template_file):
    """
    writes abinit.in from template and appends lattice vector lengths (acell) and angles (angdeg)
    """
    shutil.copy2(template_file, 'abinit.in')
    with open('abinit.in', 'a') as f:
        f.write('acell ' + ' '.join([str(float(n)) for n in s]) + '\n')
        f.write('angdeg ' + ' '.join([str(float(n)) for n in angles]) + '\n')

    
def write_results(raw_energy_data):
    """ 
    writes raw energy data from dft runs.
    The raw data input should have a,b,c,E for each run
    """
    pass
