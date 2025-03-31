import streamlit as st
from streamlit import session_state as sst

import numpy as np
import pandas as pd
import uuid

# Initialize
if "reactions_df" not in sst:
    sst.reactions_df = pd.DataFrame(columns=["selected", "reaction_str", "stoic_coefs", "exponents", "kinectic_type", "powerlaw_k", "phi", "Ep0", "epsilon", "Abs", "l", "l_reator"])



reset_keys_list = ["create_reaction_df_key","powerlaw_k_key","phi_key","Ep0_key","epsilon_key","Abs_key","l_key","l_reator_key"]
for reset_key in reset_keys_list:
    if reset_key not in sst:
        sst[reset_key] = str(uuid.uuid4())


def get_stoic_dict():
    # PS: só é possível colocar valores positivos de coeficiente, por isso tem a opção "produto/reagente"
    stoic_dict = dict()
    for idx, row in sst.create_reaction_df.iterrows():
        if row["comp_id"] not in stoic_dict.keys():
            if row["product_reagent"] == "Reagente" and row["coefficient"] is not None:
                stoic_dict[row["comp_id"]] = - row["coefficient"]
            elif row["product_reagent"] == "Produto" and row["coefficient"] is not None:
                stoic_dict[row["comp_id"]] = row["coefficient"]
    return stoic_dict


def get_exp_dict():
    exp_dict = dict()
    for idx, row in sst.create_reaction_df.iterrows():
        if row["comp_id"] not in exp_dict.keys():
            exp_dict[row["comp_id"]] = row["exponent"]
    return exp_dict

def get_reaction_str(stoic_dict):
    reagents = []
    products = []
    for comp_id, coef in stoic_dict.items():
        if coef < 0:
            reagents.append(f"{-coef} {comp_id}")
        elif coef > 0:
            products.append(f"{coef} {comp_id}")
    
    return "+".join(reagents) + " → " + "+".join(products)

# Callbacks
def add_reaction_clicked():
    # add to reaction_df
    new_data = {
        "stoic_coefs": sst.stoic_dict,
        "exponents": sst.exp_dict,
        "kinectic_type": sst.kinect_type,
        "selected":True,
        "reaction_str": get_reaction_str(sst.stoic_dict)
    }
    
    if sst.kinect_type == "Powerlaw":
        new_data["powerlaw_k"] = sst.powerlaw_k
        for const in ["phi", "Ep0", "epsilon", "Abs", "l", "l_reator"]:
            new_data[const] = None
    
    elif sst.kinect_type == "Fotocatalítica":
        new_data["powerlaw_k"] = None
        for const in ["phi", "Ep0", "epsilon", "Abs", "l", "l_reator"]:
            new_data[const] = sst[const]
    
    sst.reactions_df = pd.concat([sst.reactions_df, pd.DataFrame([new_data])], ignore_index=True)


    # reset add_reaction data_editor
    sst.create_reaction_df_key = str(uuid.uuid4())
    
    # reset powerlaw
    sst.powerlaw_k_key =str(uuid.uuid4())

    # reset fotocatalitica
    sst.phi_key = str(uuid.uuid4())
    sst.Ep0_key = str(uuid.uuid4())
    sst.epsilon_key = str(uuid.uuid4())
    sst.Abs_key = str(uuid.uuid4())
    sst.l_key = str(uuid.uuid4())
    sst.l_reator_key = str(uuid.uuid4())





# Components
st.header("Componentes")

components_df = st.data_editor(
    pd.DataFrame(columns=["id", "name", "molar_mass"]),
    column_config={
        "id": st.column_config.TextColumn("ID"),
        "name": st.column_config.TextColumn("Nome"),
        "molar_mass": st.column_config.NumberColumn("Massa molar (g/mol)")
    },
    num_rows="dynamic",
    hide_index=True
)

# Reactions
st.header("Reações")
st.write("Monte a reação")



# Isso aqui deixa uma brecha pro cara selecionar o mesmo componente 2 vezes
sst.create_reaction_df = st.data_editor(
    pd.DataFrame(columns=["comp_id", "product_reagent", "coefficient", "exponent"]),
    column_config={
        "comp_id": st.column_config.SelectboxColumn("ID componente", options=components_df["id"].unique(), required=True),
        "product_reagent": st.column_config.SelectboxColumn("Produto/Reagente", options=["Reagente","Produto"], required=True),
        "coefficient": st.column_config.NumberColumn("Coeficiente estequiométrico", min_value=0, required=True),
        "exponent": st.column_config.NumberColumn("Expoente") 
    },
    num_rows="dynamic",
    hide_index=True,
    key = sst.create_reaction_df_key
)

sst.stoic_dict = get_stoic_dict()
print("stoic_dict", sst.stoic_dict)

sst.exp_dict = get_exp_dict()
sst.kinect_type = st.selectbox(
    "Selecione o tipo da cinética",
    options=["Powerlaw", "Fotocatalítica"],
    index=None,
    placeholder="Selecione",
    key="kinect_type_selectbox"
)

st.write("*Constante não preenchida indica que ela deverá ser encontrada com regressão dos dados experimentais")



# Reactions - Powerlaw
if sst.kinect_type == "Powerlaw":
    comp_exp_dict = dict() # {comp_id: exponent}

    for idx, row in sst.create_reaction_df.iterrows():
        if row["exponent"] is None:
            continue
        comp_exp_dict[row["comp_id"]] = row["exponent"]
    
    powerlaw_col1, powerlaw_col2 = st.columns(2)

    with powerlaw_col1:
        sst.powerlaw_k = st.number_input(
            "Constante k",
            value=None,
            placeholder=None,
            key=sst.powerlaw_k_key
        )
    
    with powerlaw_col2:
        # equation display
        equation_str = "k"
        for comp_id, exp in comp_exp_dict.items():
            if exp != 0:
                equation_str += "(C_{" + str(comp_id) + "})^{" + str(exp) + "}"
        
        if equation_str != "k":
            # Tem alguma equação pra mostrar
            st.latex(equation_str)




# Reactions - fotocatalítica
elif sst.kinect_type == "Fotocatalítica":
    st.write("Essa cinética permite apenas um reagente")
    comp_id = "C"
    latex_equation = fr"""
        \phi \cdot E_{{p,0}} \frac{{\varepsilon \cdot {comp_id} \cdot l}}{{Abs}} 
        \left(1 - 10^{{ \frac{{Abs}}{{l}} \cdot l_{{reator}} }}\right)
        """
    st.latex(latex_equation)

    fotocat_col1, fotocat_col2 = st.columns(2)
    with fotocat_col1:
        sst.phi = st.number_input("$\phi$",value=None,placeholder=None,key=sst.phi_key)
        sst.Ep0 = st.number_input("$E_{p,0}$",value=None,placeholder=None,key=sst.Ep0_key)
        sst.epsilon = st.number_input("$\\varepsilon$",value=None,placeholder=None,key=sst.epsilon_key)
    
    with fotocat_col2:
        sst.Abs = st.number_input("$Abs$",value=None,placeholder=None,key=sst.Abs_key)
        sst.l = st.number_input("$l$",value=None,placeholder=None,key=sst.l_key)
        sst.l_reator = st.number_input("$l_{reator}$",value=None,placeholder=None,key=sst.l_reator_key)

    


add_reaction = st.button("Adicionar Reação", on_click=add_reaction_clicked)

sst.reactions_data_editor = st.data_editor(
    sst.reactions_df,
    column_order=["selected", "reaction_str", "kinectic_type"],
    column_config={
        "selected": st.column_config.CheckboxColumn("Reação ativa"),
        "reaction_str": "Reação",
        "kinectic_type": "Cinética"
    },
    hide_index=True,
    num_rows="dynamic"
)

# Reactor
st.header("Reator")
reactor_col1, reactor_col2 = st.columns(2)
with reactor_col1:
    st.write("Componentes selecionados")
    selected_components = st.data_editor(
        pd.DataFrame({"comp_id": components_df["id"], "initial_conc": None}),
        hide_index=True,
        column_config={"comp_id": "ID componente","initial_conc": st.column_config.NumberColumn("Concentração inicial (mol/L)")}
    )

with reactor_col2:
    st.number_input("Volume do reator (L)")
    st.number_input("Intensidade Luminosa (cd)")
