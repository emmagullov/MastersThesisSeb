from sys import platform as pltm
import os, platform 
from ctypes import CDLL, c_int, c_double, c_char_p, POINTER
import numpy as np
import json
import _ctypes

class ASRE_Timoshenko_model:
    """
    A class to represent an ASRE Timoshenko beam model.
    
    Attributes
    ----------
    nnode : int
        Number of node.
    meshX : np.array(dtype=np.float64)
        The x coordinates of the beam nodes. Unit: m
    meshY : np.array(dtype=np.float64)
        The y coordinates of the beam nodes. Unit: m
    meshZ : np.array(dtype=np.float64)
        The z coordinates of the beam nodes. Unit: m
    dfoot : float
        The depth of the beam. Unit: m
    bfoot : float
        The width of the beam. Unit: m
    Eb : float
        The Young's modulus of the beam. Unit: N/m^2
    EoverG : float
        The ratio between Young's modulus and the shear modulus. Unit: unitless
    ni_foot : float
        The Poisson's ratio of beam. Unit: unitless
    q_foot : float
        The uniform weight applied on the beam. Unit: N/m (Weight along unit length in the longitudinal direction)
    EsNominal : float
        The nominal elastic modulus of soil. Unit: N/m^2
    nis : float
        The Poisson's ratio of soil. Unit: unitless 
    mu_int : float
        The friction coefficient between soil and beam. Unit: unitless
    """

    def __init__(self, nnode, meshX, meshY, meshZ, dfoot, bfoot, d_NA = 0, solver = 'elasto-plastic'):
        """
        Constructs the beam with dimension properties.

        Parameters
        ----------
        nnode : int
            Number of node.
        meshX : np.array(dtype=np.float64)
            The x coordinates of the beam nodes. Unit: m
        meshY : np.array(dtype=np.float64)
            The y coordinates of the beam nodes. Unit: m
        meshZ : np.array(dtype=np.float64)
            The z coordinates of the beam nodes. Unit: m
        dfoot : float
            The depth of the beam. Unit: m
        bfoot : float
            The width of the beam. Unit: m
        d_NA : float
            The distance from beam neutural axis to ground. Unit: m
        solver : str
            The solver used in the model. Default is 'elasto-plastic'.
            Another option is 'elastic'.
        """
        self.nnode = nnode
        self.meshX = meshX
        self.meshY = meshY
        self.meshZ = meshZ
        self.dfoot = dfoot
        self.bfoot = bfoot
        self.asre_dll = self._import_dll()
        self.d_NA = d_NA
        self.solver = solver

    def _import_dll(self):
        """
        import the CDLL.
        
        Returns
        -------
        CDLL
            The CDLL.
        """
        if pltm == "linux" or pltm == "linux2":
            lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "ASREcpp", "bin", "macOS_arm", "libASRElibTimoBeam.so")
            if os.path.exists(lib_path):
                c_lib = CDLL(lib_path)
            else:
                c_lib = None
                message = f'ASRE is not precompiled for {pltm}, please compile the ASRE cpp library'
        elif pltm == "darwin":
            if platform.processor() == 'arm':
                lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "ASREcpp", "bin", "macOS_arm", "libASRElibTimoBeam.dylib")
                if os.path.exists(lib_path):
                    c_lib = CDLL(lib_path)
                else:
                    c_lib = None
                    message = f'ASRE is not precompiled for {pltm} {platform.processor()}, please compile the ASRE cpp library'
            else:
                lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "ASREcpp", "bin", "macOS", "libASRElibTimoBeam.dylib")
                if os.path.exists(lib_path):
                    c_lib = CDLL(lib_path)
                else:
                    c_lib = None
                    message = f'ASRE is not precompiled for {pltm} {platform.processor()}, please compile the ASRE cpp library'
        elif pltm == "win32":
            lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "ASREcpp", "bin", "win32", "ASRElibTimoBeam.dll")
            if os.path.exists(lib_path):
                c_lib = CDLL(lib_path)
            else:
                c_lib = None
                message = f'ASRE is not precompiled for {pltm}, please compile the ASRE cpp library'
            # c_lib = CDLL(pkg_resources.resource_filename('ASREpy', 'ASREcpp//bin//win32//ASRElib.dll'))
            # c_lib.printName()
        if c_lib is None:
            raise ImportError(message)
        c_lib.run.argtypes = [c_int, #nnode 
                              np.ctypeslib.ndpointer(dtype=np.float64), #meshX
                              np.ctypeslib.ndpointer(dtype=np.float64), #meshY
                              np.ctypeslib.ndpointer(dtype=np.float64), #meshZ
                              np.ctypeslib.ndpointer(dtype=np.float64), #dispV
                              np.ctypeslib.ndpointer(dtype=np.float64), #dispL
                              np.ctypeslib.ndpointer(dtype=np.float64), #dispT
                              c_double, #Eb
                              c_double, #EoverG
                              c_double, #EsNominal
                              c_double, #nis
                              c_double, #dfoot
                              c_double, #bfoot
                              c_double, #ni_foot
                              c_double, #mu_int
                              c_double, #qz_foot
                              c_double, #d_NA
                              c_char_p, #solver
                              c_char_p, #output
                                  POINTER(c_double), # result
                                  c_int # result_size
                            ]
        c_lib.run.restype = c_int
        return c_lib

    def set_beam_properties(self, Eb, EoverG, q_foot, d_NA = 0):
        """
        Set the beam material properties.

        Parameters
        ----------
        Eb : float
            The Young's modulus of the beam. Unit: N/m^2
        EoverG : float
            The ratio between Young's modulus and the shear modulus. Unit: unitless
        q_foot : float
            The uniform weight applied on the beam. Unit: N/m (Weight along unit
            length in the longitudinal direction)
        """
        self.Eb = Eb
        self.EoverG = EoverG
        self.q_foot = q_foot
        self.ni_foot = self.EoverG/2 - 1 #The Poisson's ratio of beam. Unit: unitless
        self.d_NA = d_NA

    def set_soil_properties(self, EsNominal, nis, mu_int):
        """
        Set the beam material properties.

        Parameters
        ----------
        EsNominal : float
            The nominal elastic modulus of soil. Unit: N/m^2
        nis : float
            The Poisson's ratio of soil. Unit: unitless 
        mu_int : float
            The friction coefficient between soil and beam. Unit: unitless
        """
        self.EsNominal = EsNominal
        self.nis = nis
        self.mu_int = mu_int
        
    def run_model(self, dispL, dispT, dispV, output = 'disp'):
        """
        Run the SSI model under greenfield displacements

        Parameters
        ----------
        dispL : float
            The nominal elastic modulus of soil. Unit: N/m^2
        dispT : float
            The Poisson's ratio of soil. Unit: unitless 
        dispV : float
            The friction coefficient between soil and beam. Unit: unitless
        output : str
            If 'disp' then save beam displacement to self.beam_disp
            self.beam_dispL is the beam disp in longitudinal direction
            self.beam_dispT is the beam disp in transverse direction
            self.beam_dispV is the beam disp in vertical direction
            If 'strain' then save beam principal strain to self.strain
            Each element in self.strain is one principal strain of the beam
            If 'strain+disp' then save both self.disp and self.strain
        
        Returns
        -------
        bool
            Return Ture if run success and False if unsuccess 
        """
        self.ouput = output
        if self.ouput == 'disp':
            result_size = self.nnode * 6
            self.result_array_ptr = (c_double * result_size)(*([0]*result_size))
        elif self.ouput == 'strain':
            result_size = 3 * (self.nnode-1) * 2
            self.result_array_ptr = (c_double * result_size)(*([0]*result_size))
        elif self.ouput == 'strain+disp':
            result_size = 3 * (self.nnode-1) * 2 + self.nnode * 6
            self.result_array_ptr = (c_double * result_size)(*([0]*result_size))
        elif self.ouput == 'strain+disp+force':
            result_size = 3 * (self.nnode-1) * 2 + self.nnode * 6 + 3 * (self.nnode-1) * 2
            self.result_array_ptr = (c_double * result_size)(*([0]*result_size))
        else:
            raise ValueError(f'output value {output} is not permitted in ASRE_Timoshenko_model')
        
        self.ouput = self.ouput.encode('utf-8')
        self.solver = self.solver.encode('utf-8')
        try:
            result = self.asre_dll.run(self.nnode, self.meshX, self.meshY, self.meshZ,
                                       dispV, dispL, dispT, self.Eb, self.EoverG,
                                       self.EsNominal, self.nis, self.dfoot,
                                       self.bfoot, self.ni_foot, self.mu_int,
                                       self.q_foot, self.d_NA, self.solver, self.ouput,
                                       self.result_array_ptr, result_size)
            self.result = result
            self.result_array_ptr = np.array(list(self.result_array_ptr))
            if self.ouput.decode('utf-8') == 'disp':
                self.beam_DispL = self.result_array_ptr[0::6]
                self.beam_DispT = self.result_array_ptr[1::6]
                self.beam_DispV = self.result_array_ptr[2::6]
                self.beam_RotaL = self.result_array_ptr[3::6]
                self.beam_RotaT = self.result_array_ptr[4::6]
                self.beam_RotaV = self.result_array_ptr[5::6]
            elif self.ouput.decode('utf-8') == 'strain':
                self.beam_strain_top = self.result_array_ptr[0:(self.nnode-1)*2]
                self.beam_strain_bottom = self.result_array_ptr[(self.nnode-1)*2:(self.nnode-1)*4]
                self.beam_strain_diagonal = self.result_array_ptr[(self.nnode-1)*4:(self.nnode-1)*6]
            elif self.ouput.decode('utf-8') == 'strain+disp':
                self.beam_strain_top = self.result_array_ptr[0:(self.nnode-1)*2]
                self.beam_strain_bottom = self.result_array_ptr[(self.nnode-1)*2:(self.nnode-1)*4]
                self.beam_strain_diagonal = self.result_array_ptr[(self.nnode-1)*4:(self.nnode-1)*6]
                result_array = self.result_array_ptr[(self.nnode-1)*6:]
                self.beam_DispL = result_array[0::6]
                self.beam_DispT = result_array[1::6]
                self.beam_DispV = result_array[2::6]
                self.beam_RotaL = result_array[3::6]
                self.beam_RotaT = result_array[4::6]
                self.beam_RotaV = result_array[5::6]
            elif self.ouput.decode('utf-8') == 'strain+disp+force':
                self.beam_strain_top = self.result_array_ptr[0:(self.nnode-1)*2]
                self.beam_strain_bottom = self.result_array_ptr[(self.nnode-1)*2:(self.nnode-1)*4]
                self.beam_strain_diagonal = self.result_array_ptr[(self.nnode-1)*4:(self.nnode-1)*6]
                result_array = self.result_array_ptr[(self.nnode-1)*6:(self.nnode-1)*6+self.nnode*6]
                self.beam_DispL = result_array[0::6]
                self.beam_DispT = result_array[1::6]
                self.beam_DispV = result_array[2::6]
                self.beam_RotaL = result_array[3::6]
                self.beam_RotaT = result_array[4::6]
                self.beam_RotaV = result_array[5::6]
                result_array = self.result_array_ptr[(self.nnode-1)*6+self.nnode*6:]
                self.moment = result_array[0:(self.nnode-1)*2]
                self.axialForce = result_array[(self.nnode-1)*2:(self.nnode-1)*4]
                self.shearForce = result_array[(self.nnode-1)*4:(self.nnode-1)*6]
            return True
        except:
            self.release_cdll_handle()
            raise RuntimeError(f'ASRE_Timoshenko_model failed to run the ASRE cpp library')
    def _write_input_file(self,  dispL, dispT, dispV, output = 'disp',
                          folder=None, filename=None):
        if filename is None:
            filename = 'input.json'
        if folder is None:
            folder = os.getcwd()
        input_json = {
            'nnode': self.nnode,
            'meshX': self.meshX.tolist(),
            'meshY': self.meshY.tolist(),
            'meshZ': self.meshZ.tolist(),
            'dispL': dispL.tolist(),
            'dispT': dispT.tolist(),
            'dispV': dispV.tolist(),
            'Eb': self.Eb,
            'EoverG': self.EoverG,
            'EsNominal': self.EsNominal,
            'nis': self.nis,
            'dfoot': self.dfoot,
            'bfoot': self.bfoot,
            'ni_foot': self.ni_foot,
            'd_NA': self.d_NA,
            'mu_int': self.mu_int,
            'q_foot': self.q_foot,
            'solver': self.solver,
            'output': output
        }
        with open(os.path.join(folder, filename), 'w') as f:
            json.dump(input_json, f, indent=2)
        return os.path.join(folder, filename)
    
    def release_cdll_handle(self):
        if self.asre_dll is None:
            pass
        else:
            lib_handle = self.asre_dll._handle
            if pltm == "win32": 
                del self.asre_dll
                _ctypes.FreeLibrary(lib_handle)
                self.asre_dll = None
            elif pltm == "darwin":
                dl = CDLL('libdl.dylib')
                dl.dlclose(lib_handle)

 
