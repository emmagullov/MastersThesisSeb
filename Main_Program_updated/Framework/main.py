# %% Imports

import sys

sys.path.append('FunctionScripts')
from Input_general import *  # import * = import all
# from Input_General_TUST import *
from Wall_deflection_v_38 import wall_deflection, wall_deflection_direct
from strain_analysis import *
from FEA_LTS import categorize_damage, compute_tensile_strain, generate_output
from localStiff3D import *
from Output_uncertainty_analysis import *
import os

# from plotDisp import *

plot_var = "yes"  # "yes" or "no" to define if plot wanted or not
"""
ASREpy_dir = os.path.join(os.path.dirname(__file__), "..", "ASREpy-main")
sys.path.append(ASREpy_dir)
sys.path.append("D:\Main_Program_updated\ASREpy-main")
sys.path.append("S:\Main_Program_updated\ASREpy-main")
"""

project_dir = Path(__file__).resolve().parents[1]
asrepy_dir = project_dir / "ASREpy-main"

if not asrepy_dir.is_dir():
    raise FileNotFoundError(f"ASREpy directory not found: {asrepy_dir}")

sys.path.insert(0, str(asrepy_dir))


Error_Variable = 0  # False

import ASREpy

# %% IF WALL
if input_type == 'WALL':
    if avg_wall_disp_construction <= 0:
        avg_wall_disp_construction = 0
    if avg_wall_disp_installation <= 0:
        avg_wall_disp_installation = 0
    if avg_wall_disp_construction == 0 and avg_wall_disp_installation == 0 and integration_mode == 'CValues':
        Error_Variable = 1
        if mode == 'SA':
            if output == 'quoFEM':
                generate_output(output_fields, 0, output_fields, error_flag=Error_Variable)
                sys.exit()
            elif output == 'OLDquoFEM':
                with open("results.out", "w") as f:
                    str1 = " ".join(map(str, 0 * np.zeros([num_nodes])))  # Converts numpy array to string
                    # highest_damage_greenfield
                    # max_tensile_eps_gf
                    # Error_Variable
                    f.write("{} {} {} {} {} {} {} {}".format(Error_Variable, 0, 0, str1, str1, str1, str1, str1))
                sys.exit()
            else:
                sys.exit('Error: output field must be either "quoFEM" or "OLDquoFEM')
        elif mode == 'SSI':
            if output == 'quoFEM':
                generate_output(output_fields, 0, output_fields, error_flag=1)
                sys.exit()
            elif output == 'OLDquoFEM':
                with open("results.out", "w") as f:
                    str1 = " ".join(map(str, np.zeros([num_nodes])))  # Converts numpy array to string
                    str2 = " ".join(map(str, np.zeros([num_elements * 2])))  # Converts numpy array to string
                    # highest_damage_greenfield
                    # max_tensile_eps_gf
                    # highest_damage_SSI
                    # max_tensile_eps_SSI
                    # Error_Variable
                    f.write("{} {} {} {} {} {} {} {} {} {} {} {} {} {} {}".format(Error_Variable, 0, 0, 0, 0,
                                                                                  str1, str1, str1, str1, str1, str1,
                                                                                  str2, str2, str2, str2))
                sys.exit()
            else:
                sys.exit('Error: output field must be either "quoFEM" or "OLDquoFEM')
        else:
            sys.exit("Error: mode must be either 'SA' or 'SSI'")

    # %% Direct integration:
    if integration_mode == 'Direct':
        delta_wall = data_wall["delta_wall"].flatten() / 1000
        # Flatten to remove unnecessary dimensions + CONVERT TO [M]
        depth_w = data_wall["depth_w"].flatten()

        horizontal_displacement_ground_building, vertical_displacement_ground_building, dvec, dw = wall_deflection_direct(
            retaining_wall_depth, soil_ovalization, volumetric, delta_wall, depth_w,
            x_coords=building_coords, foundation_depth=foundation_depth)

        # This next section is for validation only
        '''
        import matplotlib.pyplot as plt
        # Create the plot
        plt.figure(figsize=(8, 6))

        # Plot first dataset (dvec vs dw)
        plt.plot(dw*1000, -dvec, label="dvec vs dw", color='blue', marker='o', linestyle='-')

        # Plot second dataset (delta_wall vs depth_w)
        plt.plot(delta_wall*1000, -depth_w, label="delta_wall vs depth_w", color='red', marker='s', linestyle='--')

        # Add labels and title
        plt.xlabel("Displacement in [mm]")
        plt.ylabel("Depth below surface [m]")
        plt.title("Comparison of Ground Displacement and Wall Deflection")
        plt.legend()
        plt.grid(True)

        # Show the plot
        plt.show()
        '''


    # %% INSTALLATION EFFECTS
    elif integration_mode == 'CValues':
        shape_wall_deflection = shape_wall_deflection_i  # [-] Shape of wall deflection M0-M4 | 0 = Uniform, 1 = Cantilever,
        #     2 = Parabola type, 3 = Composite type, 4 = Kick-in type, 5 custom

        if avg_wall_disp_installation == 0:  # Do not allow values below 0
            vertical_displacement_installation = np.zeros(
                [1, num_nodes])  # Installation effects vertical settlement at building
            horizontal_displacement_installation = np.zeros(
                [1, num_nodes])  # Installation effects horizontal movement at building
        else:
            Sx, Sz, Deltaw_all, VLW, Deltaw_max, check_ratio, VLS, ratiovol = wall_deflection(retaining_wall_depth,
                                                                                              avg_wall_disp_installation,
                                                                                              shape_wall_deflection_i,
                                                                                              soil_ovalization,
                                                                                              volumetric,
                                                                                              x_coords=building_coords,
                                                                                              C1_val=C1, C2_val=C2,
                                                                                              foundation_depth=foundation_depth)

            vertical_displacement_installation = Sz  # Installation effects vertical settlement at building
            horizontal_displacement_installation = Sx  # Installation effects horizontal movement at building

        # DISPLACEMENTS ARE COMBINED VIA SUPERPOSITION (ELASTIC SOIL BEHAVIOUR ASSUMED)
        combined_vertical_displacement = vertical_displacement_installation
        combined_horizontal_displacement = horizontal_displacement_installation

        # If we want to include the plot, just call the wall_deflection function here with the full x span
        """
        Sx, Sz, Deltaw_all, VLW, Deltaw_max, check_ratio, VLS, ratiovol = wall_deflection(retaining_wall_depth,
                                                                                          average_wall_displacement_normalized,
                                                                                          shape_wall_deflection,
                                                                                          soil_ovalization, volumetric,
                                                                                          C1, C2,
                                                                                          x_coords = input)
        delta_v_x_ins_plot = Sx    # Installation effects 
        delta_v_z_ins_plot = Sz    # Installation effects
        """

        # %% Greenfield Settlements based on Wall Deflection Shape Functions
        average_wall_displacement_normalized = avg_wall_disp_construction  # [-] Average wall displacement normalized by the wall height (as pure number)
        shape_wall_deflection = shape_wall_deflection_c  # [-] Shape of wall deflection M0-M4 | 0 = Uniform, 1 = Cantilever,
        #     2 = Parabola type, 3 = Composite type, 4 = Kick-in type, 5 custom

        if avg_wall_disp_construction == 0:  # Do not allow values below 0
            print(
                f"Average wall displacement (construction) is {avg_wall_disp_construction} and is therefore set to 0")
            vertical_displacement_construction = np.zeros(
                [1, num_nodes])  # Installation effects vertical settlement at building
            horizontal_displacement_construction = np.zeros(
                [1, num_nodes])  # Installation effects horizontal movement at building
        else:
            if integration_mode == 'CValues':
                Sx, Sz, Deltaw_all, VLW, Deltaw_max, check_ratio, VLS, ratiovol = wall_deflection(retaining_wall_depth,
                                                                                                  avg_wall_disp_construction,
                                                                                                  shape_wall_deflection,
                                                                                                  soil_ovalization,
                                                                                                  volumetric,
                                                                                                  x_coords=building_coords,
                                                                                                  C1_val=C1, C2_val=C2,
                                                                                                  foundation_depth=foundation_depth)
            vertical_displacement_construction = Sz  # Installation effects vertical settlement at building
            horizontal_displacement_construction = Sx  # Installation effects horizontal movement at building

        # DISPLACEMENTS ARE COMBINED VIA SUPERPOSITION (ELASTIC SOIL BEHAVIOUR ASSUMED)
        combined_vertical_displacement += vertical_displacement_construction
        combined_horizontal_displacement += horizontal_displacement_construction

        # Rewrite here:
        vertical_displacement_ground_building = combined_vertical_displacement
        horizontal_displacement_ground_building = combined_horizontal_displacement
    else:
        sys.exit('Invalid integration mode')

# %% IF TUNNEL
elif input_type == 'TUNNEL':
        if vlt <= 0:  # If volume loss is negative:
            Error_Variable = 1
            if mode == 'SA':
                if output == 'quoFEM':
                    generate_output(output_fields, 0, output_fields, error_flag=Error_Variable)
                    sys.exit()
                elif output == 'OLDquoFEM':
                    with open("results.out", "w") as f:
                        str1 = " ".join(map(str, np.zeros([num_nodes])))  # Converts numpy array to string
                        # highest_damage_greenfield
                        # max_tensile_eps_gf
                        # Error_Variable
                        f.write("{} {} {} {} {} {} {} {}".format(Error_Variable, 0, 0, str1, str1, str1, str1,
                                                                 str1))
                    sys.exit()
                else:
                    sys.exit('Error: output field must be either "quoFEM" or "OLDquoFEM')
            elif mode == 'SSI':
                if output == 'quoFEM':
                    generate_output(output_fields, 0, output_fields, error_flag=1)
                    sys.exit()
                elif output == 'OLDquoFEM':
                    with open("results.out", "w") as f:
                        str1 = " ".join(map(str, np.zeros([num_nodes])))  # Converts numpy array to string
                        str2 = " ".join(map(str, np.zeros([num_elements * 2])))  # Converts numpy array to string
                        # highest_damage_greenfield
                        # max_tensile_eps_gf
                        # highest_damage_SSI
                        # max_tensile_eps_SSI
                        # Error_Variable
                        f.write("{} {} {} {} {} {} {} {} {} {} {} {} {} {} {}".format(Error_Variable, 0, 0, 0, 0,
                                                                                      str1, str1, str1, str1, str1,
                                                                                      str1, str2, str2, str2, str2))
                    sys.exit()
                else:
                    sys.exit('Error: output field must be either "quoFEM" or "OLDquoFEM')
            else:
                sys.exit("Error: mode must be either 'SA' or 'SSI'")

        else:  # So if volume loss isn't negative:
            from prepare_greenfield_disp_file import prepare_greenfield

            (vertical_displacement_ground_building, horizontal_displacement_ground_building,
             building_coords) = prepare_greenfield(z_t, vlt, Kt, D_t, length_beam, eccentricity, num_nodes)

            # %Update
            vertical_displacement_ground_building = -1 * np.array(
                vertical_displacement_ground_building)  # Update coordinates
            horizontal_displacement_ground_building = np.array(horizontal_displacement_ground_building)


else:
    sys.exit("Invalid input_type, either 'TUNNEL' or 'WALL'")

# %% LIMITING TENSILE STRAIN | GREENFIELD

# Green-field analysis for Limiting Tensile Strain method:
print('--------- TENSILE STRAIN OUTPUT INFORMATION ---------')
dataSA = strain_analysis_greenfield(vertical_displacement_ground_building, horizontal_displacement_ground_building,
                                    length_beam_element, length_beam, building_height, neutral_line, poissons_ratio,
                                    input_type, def_mode)

print("Tensile strain calculation for Greenfield analysis")
highest_damage_greenfield, max_tensile_eps_gf = categorize_damage(dataSA['eps_t_max'])  # Highest damage category

if mode == 'SA':
    if output == 'quoFEM':
        generate_output(output_fields, 0, output_fields, error_flag=1)
        sys.exit()
    elif output == 'OLDquoFEM':
        with open("results.out", "w") as f:
            string1 = " ".join(map(str, dataSA['eps_t']))  # Converts numpy array to string
            string2 = " ".join(map(str, dataSA['beta_d']))
            string3 = " ".join(map(str, dataSA['eps_h']))
            string4 = " ".join(map(str, combined_horizontal_displacement))
            string5 = " ".join(map(str, combined_vertical_displacement))
            print('vector_length = ', len(dataSA['eps_t']))
            # highest_damage_greenfield
            # max_tensile_eps_gf
            # Error_Variable
            f.write("{} {} {} {} {} {} {} {}".format(Error_Variable, highest_damage_greenfield, max_tensile_eps_gf,
                                               string1, string2, string3, string4, string5))
            sys.exit()
    else:
        sys.exit('Error: output field must be either "quoFEM" or "OLDquoFEM')
elif mode != 'SSI':
    sys.exit("Error: mode must be either 'SA' or 'SSI'")

# %% Jinyan model displacements
combined_vertical_displacement = -np.array(vertical_displacement_ground_building).flatten()  # STD: FEM CONVENTION
combined_horizontal_displacement = np.array(horizontal_displacement_ground_building).flatten()

# UPWARDS POSITIVE, TOWARDS RIGHT POSITIVE AND COUNTERCLOCKWISE POSITIVE


## Jinyan model inputs
beamY = np.zeros_like(building_coords)
beamZ = np.zeros_like(building_coords)
if 'qfoot' not in globals():
    qfoot = 0  # [N/m] The uniform weight applied on the beam. Unit: N/m (Weight along unit length in the longitudinal direction)
    print('qfoot Not in Globals()')

# %% Jinyan / Peter & Seb modified elastic model

# print("-----------START VALIDATION-------------")
# print("combined_vertical_displacement = ", combined_vertical_displacement)
# print("-----------END VALIDATION-------------")

if solver == 'EL':
    model_el = ASREpy.ASRE_Timoshenko_model_ps(building_coords.size, building_coords, beamY, beamZ, building_height,
                                               building_width, solver='elastic')
    model_el.set_soil_properties(Es_isotropic, soil_poisson, mu_int=0)
elif solver == 'EP':
    model_el = ASREpy.ASRE_Timoshenko_model_ps(building_coords.size, building_coords, beamY, beamZ, building_height,
                                               building_width, solver='elasto-plastic')
    model_el.set_soil_properties(Es_isotropic, soil_poisson, mu_int=mu_int)
else:
    sys.exit('Error: string solver must be EL or EP')

# %% SET BEAM PROPERTIES
model_el.set_beam_properties(Eb, Eb / Gb, qfoot, d_a=dist_a)

model_el.run_model(combined_horizontal_displacement, np.zeros_like(combined_horizontal_displacement),
                   combined_vertical_displacement, 'strain+disp+force')

model_properties = np.array([EA, EI, Gb, Ab, poissons_ratio, shear_factor_midpoint, building_height,
                             dist_a, neutral_line])

# %% Convert forces if d_NA != 0
# print('before conversion', model_el.axialForce)
if dist_a != 0:
    model_el, total_disp = moveResultLocation(model_el, dist_a, num_nodes)
    F_M_deltaT_el, F_N_deltaT_el, F_S_deltaT_el = compute_internal_forces(EA, EI, EI, GAs, GAs, length_beam_element,
                                                                          Gb, 1, total_disp, num_nodes)
    # Use updated axial force
    model_el.axialForce = F_N_deltaT_el

# print('after conversion', model_el.axialForce)
'''
# %% Jinyan model forces
data = {  # Make a DATA struct for all models run
    'model_elastic': {
        'x_coordinate': building_coords,
        'beam_strain_top': model_el.beam_strain_top,
        'beam_strain_bottom': model_el.beam_strain_bottom,
        'beam_strain_diagonal': model_el.beam_strain_diagonal,
        'beam_strain_axial': model_el.axialForce / EA,
        'moment': model_el.moment,
        'axialForce': model_el.axialForce,
        'shearForce': model_el.shearForce,
        'dispVertical': model_el.beam_DispV,  # z coordinate (Displacements at soil surface)
        'dispLongitudinal': model_el.beam_DispL  # x coordinate (Displacements at soil surface)
        # Note to self, recalculate displacements at beam axis.
    }
}
'''

# %% Recalculate strains to ensure strains are correct
dataReturn = compute_tensile_strain(model_el, model_properties)  # Call function to calculate new strains

# Calculate maximum tensile strains
print('Tensile strain calculation for Interaction analysis analysis')
highest_damage_SSI, max_eps_t_ssi = categorize_damage(dataReturn['max_e_t'])

# %% CALCULATIONS DONE, SAVE RESULTS
# Keep strains without units [-]
if input_type == 'TUNNEL':
    if output == 'quoFEM':
        generate_output(dataReturn, max_eps_t_ssi, output_fields, error_flag=0)

    elif output == 'OLDquoFEM':
        with open("results.out", "w") as f:
            with open("results.out", "w") as f:
                # f.write("{} {} {} {} {} {} {}".format(max(dataReturn['axial_strain_exx']), dataReturn['e_t_b'],
                #                                    dataReturn['max_e_xy'], dataReturn['max_e_t_mid'], dataReturn['max_e_t'],
                #                                    max_eps_t_ssi[0], 0))
                # f.write("{} {} {} {} {} {} {}".format(beamZ.flatten(), dataReturn['e_t_b'],
                #                                       dataReturn['max_e_xy'], dataReturn['max_e_t_mid'], dataReturn['max_e_t'],
                #                                       max_eps_t_ssi[0], 0))
                print(' ')
                print('--------- OUTPUT INFORMATION ---------')
                print('Total number of QoI = 15')
                # Error_Variable
                # highest_damage_greenfield
                # max_tensile_eps_gf
                # highest_damage_SSI
                # max_eps_t_SSI
                # Greenfield Strain analysis
                print(
                    'There are 5 scalars: Error_Variable, highest_damage_greenfield, max_tensile_eps_gf, highest_damage_SSI,'
                    ' max_eps_t_SSI')
                str1 = " ".join(map(str, dataSA['eps_t']))  # Converts numpy array to string
                str2 = " ".join(map(str, dataSA['beta_d']))
                str3 = " ".join(map(str, dataSA['eps_h']))
                str4 = " ".join(map(str, combined_horizontal_displacement))
                str5 = " ".join(map(str, combined_vertical_displacement))
                str6 = " ".join(map(str, building_coords))
                print('vector_length (Str1)  = ', len(dataSA['eps_t']), ', vector_length (Str2)  = ',
                      len(dataSA['beta_d']),
                      ', vector_length (Str3)  = ', len(dataSA['eps_h']), ', vector_length (Str4)  = ',
                      len(combined_horizontal_displacement), ', vector_length (Str5)  = ',
                      len(combined_vertical_displacement), ', vector_length (Str6)  = ', len(building_coords))
                # Interaction analysis
                str7 = " ".join(map(str, dataReturn['eps_t']))  # Converts numpy array to string
                str8 = " ".join(map(str, dataReturn['strain_axial_bending_top_exx,b']))
                str9 = " ".join(map(str, dataReturn['strain_axial_bending_bottom_exx,b']))
                str10 = " ".join(map(str, dataReturn['tensile_strain_midpoint']))
                # print(len(dataReturn['eps_t']), len(dataReturn['strain_axial_bending_top_exx,b']),
                #       len(dataReturn['strain_axial_bending_bottom_exx,b']), len(dataReturn['tensile_strain_midpoint']))
                # print('vector_length = ', len(dataReturn['tensile_strain_midpoint']))
                print('vector_length (Str7)  = ', len(dataReturn['tensile_strain_midpoint']),
                      ', vector_length (Str8)  = ',
                      len(dataReturn['strain_axial_bending_bottom_exx,b']), ', vector_length (Str9)  = ',
                      len(dataReturn['strain_axial_bending_bottom_exx,b']), ', vector_length (Str10)  = ',
                      len(dataReturn['tensile_strain_midpoint']))

                f.write("{} {} {} {} {} {} {} {} {} {} {} {} {} {} {}".format(Error_Variable,
                                                                              highest_damage_greenfield,
                                                                              max_tensile_eps_gf, highest_damage_SSI,
                                                                              max_eps_t_ssi, str1, str2, str3, str4,
                                                                              str5,
                                                                              str6, str7, str8, str9, str10))
                print(' ')
                print('--------- SCRIPT DONE ---------')
    else:
        print('this-> is an error')

elif input_type == 'WALL':
    if output == 'quoFEM':
        generate_output(dataReturn, max_eps_t_ssi, output_fields, error_flag=0)

    elif output == 'OLDquoFEM':
        with open("results.out", "w") as f:
            # f.write("{} {} {} {} {} {} {}".format(max(dataReturn['axial_strain_exx']), dataReturn['e_t_b'],
            #                                    dataReturn['max_e_xy'], dataReturn['max_e_t_mid'], dataReturn['max_e_t'],
            #                                    max_eps_t_ssi[0], 0))
            # f.write("{} {} {} {} {} {} {}".format(beamZ.flatten(), dataReturn['e_t_b'],
            #                                       dataReturn['max_e_xy'], dataReturn['max_e_t_mid'], dataReturn['max_e_t'],
            #                                       max_eps_t_ssi[0], 0))
            print(' ')
            print('--------- OUTPUT INFORMATION ---------')
            print('Total number of QoI = 15')
            # Error_Variable
            # highest_damage_greenfield
            # max_tensile_eps_gf
            # highest_damage_SSI
            # max_eps_t_SSI
            # Greenfield Strain analysis
            print(
                'There are 5 scalars: Error_Variable, highest_damage_greenfield, max_tensile_eps_gf, highest_damage_SSI,'
                ' max_eps_t_SSI')
            str1 = " ".join(map(str, dataSA['eps_t']))  # Converts numpy array to string
            str2 = " ".join(map(str, dataSA['beta_d']))
            str3 = " ".join(map(str, dataSA['eps_h']))
            str4 = " ".join(map(str, combined_horizontal_displacement))
            str5 = " ".join(map(str, combined_vertical_displacement))
            str6 = " ".join(map(str, building_coords))
            print('vector_length (Str1)  = ', len(dataSA['eps_t']), ', vector_length (Str2)  = ', len(dataSA['beta_d']),
                  ', vector_length (Str3)  = ', len(dataSA['eps_h']), ', vector_length (Str4)  = ',
                  len(combined_horizontal_displacement), ', vector_length (Str5)  = ',
                  len(combined_vertical_displacement), ', vector_length (Str6)  = ', len(building_coords))
            # Interaction analysis
            str7 = " ".join(map(str, dataReturn['eps_t']))  # Converts numpy array to string
            str8 = " ".join(map(str, dataReturn['strain_axial_bending_top_exx,b']))
            str9 = " ".join(map(str, dataReturn['strain_axial_bending_bottom_exx,b']))
            str10 = " ".join(map(str, dataReturn['tensile_strain_midpoint']))
            # print(len(dataReturn['eps_t']), len(dataReturn['strain_axial_bending_top_exx,b']),
            #       len(dataReturn['strain_axial_bending_bottom_exx,b']), len(dataReturn['tensile_strain_midpoint']))
            # print('vector_length = ', len(dataReturn['tensile_strain_midpoint']))
            print('vector_length (Str7)  = ', len(dataReturn['tensile_strain_midpoint']), ', vector_length (Str8)  = ',
                  len(dataReturn['strain_axial_bending_bottom_exx,b']), ', vector_length (Str9)  = ',
                  len(dataReturn['strain_axial_bending_bottom_exx,b']), ', vector_length (Str10)  = ',
                  len(dataReturn['tensile_strain_midpoint']))

            f.write("{} {} {} {} {} {} {} {} {} {} {} {} {} {} {}".format(Error_Variable,
                                                                          highest_damage_greenfield,
                                                                          max_tensile_eps_gf, highest_damage_SSI,
                                                                          max_eps_t_ssi, str1, str2, str3, str4, str5,
                                                                          str6, str7, str8, str9, str10))
            print(' ')
            print('--------- SCRIPT DONE ---------')
    else:
        print('this-> is an error')
else:
    sys.exit("Input_type must be either 'WALL' or 'TUNNEL'")
# """
import scipy.io
# Combine all data into a single dictionary
data = {
    'model': {
        'type': f"{solver}, d_a = {dist_a}",
        'x_coordinate': building_coords,
        'greenfield_x': combined_horizontal_displacement,
        'greenfield_z': combined_vertical_displacement,
        #'interface_angle_in_degrees': mu,
        'd_a': dist_a,
        'disp_beam_x': model_el.beam_DispL,
        'disp_beam_z': model_el.beam_DispV,
        'axialForce': model_el.axialForce,
        'shearForce': model_el.shearForce,
        'moment': model_el.moment,
        'beam_strain_top': model_el.beam_strain_top,
        'beam_strain_bottom': model_el.beam_strain_bottom,
        'beam_strain_diagonal': model_el.beam_strain_diagonal,
        'beam_strain_top_recal': dataReturn['strain_axial_bending_top_exx,b'],
        'beam_strain_bottom_recal': dataReturn['strain_axial_bending_bottom_exx,b'],
        'beam_strain_diagonal_recal': dataReturn['tensile_strain_midpoint'],  # Maximum tensile strain from shear + axl
        'eps_t_recal': dataReturn['eps_t'],
        'TS_bending': dataReturn['TS_bending'],  # Maximum tensile strain from bending + axial
    }
}

scipy.io.savemat(f"model_{solver}_da{str(dist_a).replace('.', 'p')}.mat", data)
# """
