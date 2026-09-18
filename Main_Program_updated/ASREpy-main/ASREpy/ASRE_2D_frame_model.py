from sys import platform as pltm
import os, platform
from ctypes import CDLL, c_int, c_double, c_char_p, POINTER
import numpy as np
import json
import _ctypes

class ASRE_2D_frame_model:
    def __init__(self, opensees_model, footing_nodes_ind, footing_coord_x, footing_coord_y,
                 footing_coord_z, footing_ele_length, footing_ele_width, external_loads,
                 solver = 'elasto-plastic'):
        self._create_frame_stiffness(opensees_model)
        if footing_nodes_ind.dtype != np.int32:
            footing_nodes_ind = footing_nodes_ind.astype(np.int32)
        self.footing_nodes_ind = footing_nodes_ind
        self.footing_coord_x = footing_coord_x
        self.footing_coord_y = footing_coord_y
        self.footing_coord_z = footing_coord_z
        self.footing_ele_length = footing_ele_length
        self.footing_ele_width = footing_ele_width
        self.external_loads = external_loads
        self.solver = solver
        self.asre_dll = self._import_dll()

        
    
    def _create_frame_stiffness(self, opensees_model):
        # opensees_model.timeSeries('Linear', 1)
        # opensees_model.pattern('Plain', 1, 1)
        opensees_model.system("FullGeneral")
        opensees_model.numberer("Plain")
        opensees_model.integrator("LoadControl", 1)
        opensees_model.algorithm("Linear")
        opensees_model.analysis("Static")
        _ = opensees_model.analyze(1)
        N = opensees_model.systemSize()
        K = opensees_model.printA('-ret')
        K = np.array(K)
        self.frame_stiffness = K
        self.frame_system_size = N

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
                                    "ASREcpp", "bin", "macOS_arm", "libASRElib2DFrame.so")
            if os.path.exists(lib_path):
                c_lib = CDLL(lib_path)
            else:
                c_lib = None
                message = f'ASRE is not precompiled for {pltm}, please compile the ASRE cpp library'
        elif pltm == "darwin":
            if platform.processor() == 'arm':
                lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "ASREcpp", "bin", "macOS_arm", "libASRElib2DFrame.dylib")
                if os.path.exists(lib_path):
                    c_lib = CDLL(lib_path)
                else:
                    c_lib = None
                    message = f'ASRE is not precompiled for {pltm} {platform.processor()}, please compile the ASRE cpp library'
            else:
                lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        "ASREcpp", "bin", "macOS", "libASRElib2DFrame.dylib")
                if os.path.exists(lib_path):
                    c_lib = CDLL(lib_path)
                else:
                    c_lib = None
                    message = f'ASRE is not precompiled for {pltm} {platform.processor()}, please compile the ASRE cpp library'
        elif pltm == "win32":
            lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "ASREcpp", "bin", "win32", "ASRElib2DFrame.dll")
            if os.path.exists(lib_path):
                c_lib = CDLL(lib_path)
            else:
                c_lib = None
                message = f'ASRE is not precompiled for {pltm}, please compile the ASRE cpp library'
            # c_lib = CDLL(pkg_resources.resource_filename('ASREpy', 'ASREcpp//bin//win32//ASRElib.dll'))
            # c_lib.printName()
        if c_lib is None:
            raise ImportError(message)
        c_lib.run.argtypes = [
            np.ctypeslib.ndpointer(dtype=np.float64), # frame_stiffness
            c_int, # frame_system_size
            np.ctypeslib.ndpointer(dtype=np.int32), # footing_nodes_ind
            c_int, # footing_nodes_size
            np.ctypeslib.ndpointer(dtype=np.float64), # footing_coord_x
            np.ctypeslib.ndpointer(dtype=np.float64), # footing_coord_y
            np.ctypeslib.ndpointer(dtype=np.float64), # footing_coord_z
            np.ctypeslib.ndpointer(dtype=np.float64), # footing_ele_length
            np.ctypeslib.ndpointer(dtype=np.float64), # footing_ele_width
            c_double, # EsNominal
            c_double, # nis
            c_double, # mu_int
            np.ctypeslib.ndpointer(dtype=np.float64), # dispV
            np.ctypeslib.ndpointer(dtype=np.float64), # dispL
            np.ctypeslib.ndpointer(dtype=np.float64), # dispT
            np.ctypeslib.ndpointer(dtype=np.float64), # external_loads
            c_char_p, # solver
            POINTER(c_double), # result
            c_int # result_size
        ]
        c_lib.run.restype = c_int

        return c_lib

    def updata_frame_opensees(self, opensees_model, footing_nodes_ind=None, 
                              footing_coord_x = None, footing_coord_y = None,
                              footing_coord_z = None, footing_ele_size = None,
                              footing_width = None):
        self._create_frame_stiffness(opensees_model)
        if footing_nodes_ind is not None:
            self.footing_nodes_ind = footing_nodes_ind
        if footing_coord_x is not None:
            self.footing_coord_x = footing_coord_x
        if footing_coord_y is not None:
            self.footing_coord_y = footing_coord_y
        if footing_coord_z is not None:
            self.footing_coord_z = footing_coord_z
        if footing_ele_size is not None:
            self.footing_ele_size = footing_ele_size
        if footing_width is not None:
            self.footing_width = footing_width

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
        if self.ouput in ['disp', 'strain', 'strain+disp']:
            result_size = self.frame_system_size
            self.result_array_ptr = (c_double * result_size)(*([0]*result_size))
        else:
            raise ValueError(f'output value {output} is not permitted in ASRE_Timoshenko_model')
        
        if isinstance(self.solver, str):
            self.solver = self.solver.encode('utf-8')
        try:
            result = self.asre_dll.run(
                self.frame_stiffness, self.frame_system_size, self.footing_nodes_ind,
                len(self.footing_nodes_ind), self.footing_coord_x, self.footing_coord_y,
                self.footing_coord_z, self.footing_ele_length, self.footing_ele_width,
                self.EsNominal, self.nis, self.mu_int, dispV, dispL, dispT,
                self.external_loads, self.solver, self.result_array_ptr, result_size)

            self.result = result
            self.result_array_ptr = np.array(list(self.result_array_ptr))
            self.beam_DispL = self.result_array_ptr[0::6]
            self.beam_DispT = self.result_array_ptr[1::6]
            self.beam_DispV = self.result_array_ptr[2::6]
            self.beam_RotaL = self.result_array_ptr[3::6]
            self.beam_RotaT = self.result_array_ptr[4::6]
            self.beam_RotaV = self.result_array_ptr[5::6]
            if self.ouput == 'disp':
                pass
            elif self.ouput == 'strain':
                # TODO: add strain calculation
                pass
            elif self.ouput == 'strain+disp':
                # TODO: add strain calculation
                pass
            return True
        except:
            self.release_cdll_handle()
            raise RuntimeError('ASRE_Timoshenko_model failed to run the ASRE cpp library')
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
 
