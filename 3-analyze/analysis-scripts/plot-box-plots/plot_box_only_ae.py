# %%
import json
import pathlib as pl
import numpy as np
import matplotlib.pyplot as plt
import tabulate
import sys

import quantities_for_comparison as qc

EXPECTED_SCRIPT_VERSION = ['0.0.3','0.0.4']
DEFAULT_PREFACTOR = 100
DEFAULT_WB0 = 1.0 / 8.0
DEFAULT_WB01 = 1.0 / 64.0
REF_PLUGIN = "ae"

CAPPROPS = {
    'linewidth': 1,
    'color': 'tab:green'
}
BOXPROPS = {
    'linewidth': 1,
    'color': 'tab:green'
}
WHISKERPROPS = {
    'linewidth': 1,
    'color': 'tab:green'
}
MEDIANPROPS = {
    'linewidth': 1,
    'color': 'tab:blue'
}
FLIERPROPS = {
    'marker': '.',
    'linestyle': '',
    'markerfacecolor': 'tab:grey',
    'markeredgewidth': 0,
    'markersize': 3
}
# %%

quantity_for_comparison_map = {
    "delta_per_formula_unit": qc.delta,
    "% difference in B0": qc.B0_rel_diff,
    "% difference in V0": qc.V0_rel_diff,
    "% difference in B1": qc.B1_rel_diff,
    "rel_errors_vec_length": qc.rel_errors_vec_length,
    "epsilon": qc.epsilon
}

xlims = {
    "delta_per_formula_unit": [0,3],
    "% difference in B0": [-1.9,1.9],
    "% difference in V0": [-0.35,0.35],
    "% difference in B1": [-12,12],
    "rel_errors_vec_length": [0,15],
    "epsilon": [0,15]
}

quantity_names = ["% difference in V0","% difference in B0","% difference in B1"]
plugin_names = ['wien2k-dk_0.06', 'fleur'] # need them in reverse order for up to bottom in plot

if __name__ == "__main__":

    all_data = {}
    for quantity_name in quantity_names:
        out_data = {}
        for plugin_name in plugin_names:
            plugin_values = []
            plugin_big = 0
            plugin_small = 0
            out_data[plugin_name] = {}
            for SET_NAME in  ['unaries-verification-PBE-v1', 'oxides-verification-PBE-v1']:
    
                try:
                    data_dir = pl.Path(f'../../outputs')
                    with open(f'{data_dir}/results-{SET_NAME}-{REF_PLUGIN}.json') as fhandle:
                        ref_plugin_data = json.load(fhandle)
                        if not ref_plugin_data['script_version'] in EXPECTED_SCRIPT_VERSION:
                            raise ValueError(
                                f"This script only works with data generated at version {EXPECTED_SCRIPT_VERSION}. "
                                f"Please re-run ./get_results.py to update the data format for results-{SET_NAME}-{REF_PLUGIN}.json!"
                                )
                            sys.exit(1)
                except OSError:
                    print(f"No data found for {REF_PLUGIN} (set '{SET_NAME}'), {REF_PLUGIN} is the reference and must be present")
                    sys.exit(1)


                try:
                    data_dir = pl.Path(f'../../outputs')
                    with open(f'{data_dir}/results-{SET_NAME}-{plugin_name}.json') as fhandle:
                        plugin_data = json.load(fhandle)
                        if not ref_plugin_data['script_version'] in EXPECTED_SCRIPT_VERSION:
                            raise ValueError(
                                f"This script only works with data generated at version {EXPECTED_SCRIPT_VERSION}. "
                                f"Please re-run ./get_results.py to update the data format for results-{SET_NAME}-{REF_PLUGIN}.json!"
                                )
                            sys.exit(1)
                except OSError:
                    print(f"No data found for {REF_PLUGIN} (set '{SET_NAME}'), {REF_PLUGIN} is the reference and must be present")
                    sys.exit(1)

                ref_BM_fit_data = ref_plugin_data['BM_fit_data']
                # List the reference systems that have BM fit data
                ref_systems = set(
                    el_conf for el_conf in ref_BM_fit_data.keys()
                    if ref_BM_fit_data[el_conf] is not None
                )

                plugin_BM_fit_data = plugin_data['BM_fit_data']

                plugin_systems = set(
                    el_conf for el_conf in plugin_BM_fit_data.keys()
                    if plugin_BM_fit_data[el_conf] is not None
                )
                # Take the systems that are both in the reference and plugin sets
                plot_systems = plugin_systems.intersection(ref_systems)

                for element_and_configuration in plot_systems:
                    element, configuration = element_and_configuration.split('-')
                
                    ref_n_atoms = ref_plugin_data['num_atoms_in_sim_cell'][f'{element}-{configuration}']
                    ref_scaling_factor = qc.get_volume_scaling_to_formula_unit(
                        ref_n_atoms, element, configuration
                    )
                    ref_V0 = ref_BM_fit_data[f'{element}-{configuration}']['min_volume'] / ref_scaling_factor
                    ref_B0 = ref_BM_fit_data[f'{element}-{configuration}']['bulk_modulus_ev_ang3']
                    ref_B01 = ref_BM_fit_data[f'{element}-{configuration}']['bulk_deriv']

                    plugin_n_atoms = plugin_data['num_atoms_in_sim_cell'][f'{element}-{configuration}']
                    plugin_scaling_factor = qc.get_volume_scaling_to_formula_unit(
                        plugin_n_atoms, element, configuration
                    )
                    plugin_V0 = plugin_BM_fit_data[f'{element}-{configuration}']['min_volume'] / plugin_scaling_factor
                    plugin_B0 = plugin_BM_fit_data[f'{element}-{configuration}']['bulk_modulus_ev_ang3']
                    plugin_B01 = plugin_BM_fit_data[f'{element}-{configuration}']['bulk_deriv']

                    quantity_value = quantity_for_comparison_map[quantity_name](
                        ref_V0, ref_B0, ref_B01,
                        plugin_V0, plugin_B0, plugin_B01,
                        DEFAULT_PREFACTOR, DEFAULT_WB0, DEFAULT_WB01
                    )

                    plugin_values.append(quantity_value)
                    if quantity_value < xlims[quantity_name][0]:
                        plugin_big = plugin_big+1  
                    if quantity_value > xlims[quantity_name][1]:
                        plugin_small = plugin_small+1

            out_data[plugin_name]['values'] = plugin_values
            out_data[plugin_name]['big'] = plugin_big
            out_data[plugin_name]['small'] = plugin_small
        all_data[quantity_name] = out_data
    # %%
    # Set up the plot axes for each quantity
    for yy in quantity_names:
        for plugin_name in plugin_names:
            if all_data[yy][plugin_name]['small'] != 0:
                print(f'small {yy} {plugin_name}', all_data[yy][plugin_name]['small'])
    for yy in quantity_names:
        for plugin_name in plugin_names:
            if all_data[yy][plugin_name]['big'] != 0:
                print(f'big {yy} {plugin_name}', all_data[yy][plugin_name]['big'])
    
    n_quantities = len(quantity_names)
    fig, axes = plt.subplots(1, n_quantities, dpi=300, figsize=(4 * n_quantities, 3), sharey=True)
    axes = axes.flatten()

    for quantity_name, ax in zip(quantity_names, axes):
        quantity_values = [all_data[quantity_name][plugin_name]['values'] for plugin_name in plugin_names]
    
        #violin_parts = ax.violinplot(
        #    quantity_values,
        #    widths=0.75,
        #    points=1000,
        #    showextrema=False, showmedians=False,  # These are shown by the box plots
        #    vert=False
        #)
        #for part in violin_parts['bodies']:
        #    part.set_facecolor('tab:grey')
        #    part.set_alpha(0.50)
    
        ax.boxplot(
            quantity_values,
            flierprops=FLIERPROPS,
            boxprops=BOXPROPS,
            whiskerprops=WHISKERPROPS,
            medianprops=MEDIANPROPS,
            capprops=CAPPROPS,
            vert=False,
            labels=['WIEN2K', 'FLEUR']
        )
        ax.set_xlabel(quantity_name, fontsize=14)
        ax.set_xlim(xlims[quantity_name][0],xlims[quantity_name][1])

    fig.suptitle(f'Reference: all electron average.')
    fig.tight_layout()

    fig.savefig('boxplots.pdf')

    # %%
#    def make_quantity_table(function, quantity_data):
#        table = []
#        for plugin_name in plugin_names:
#            row = plugin_name
#            for quantity_name in quantity_names:
#                val = function(quantity_data[plugin_name][quantity_name])
#                row.append(val)
#            table.append(row)
#        table = table[::-1]
#
#        return tabulate.tabulate(
#            table, headers=['Plugin'] + [text_quantity_name_map[quantity_name] for quantity_name in quantity_names]
#        )
#
#    # %%
#    table = make_quantity_table(lambda x: np.median(x), quantity_data)
#    print('MEDIAN\n' + table)
#    # %%
#    table = make_quantity_table(lambda x: np.mean(x), quantity_data)
#    print('MEAN\n' + table)
#    # %%
#    table = make_quantity_table(lambda x: np.quantile(x, 0.75) - np.quantile(x, 0.25), quantity_data)
#    print('IQR\n' + table)
