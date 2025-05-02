import pandas as pd
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go

from htmltools import HTML, div
from functools import partial


from shiny.express import ui, input, render
from shiny.ui import page_navbar
from shinywidgets import render_widget, render_plotly  

import shinyswatch
from shinyswatch import theme

from STATE_CHOICES_LONG import STATE_CHOICES_LONG

import faicons
from faicons import icon_svg

from ipyleaflet import Map, FullScreenControl, Marker, AwesomeIcon

######################################################### GATHERING & PREPPING DATA (IPEDS 2023) #########################################################
ipeds = pd.read_csv(Path(__file__).parent/ 'hd2023.csv', encoding='latin-1',  
                 usecols=['INSTNM', 'CITY', 'STABBR', 'SECTOR', 'ICLEVEL', 'CONTROL', 'HDEGOFR1', 'DEGGRANT', 'HBCU', 'HOSPITAL', 'MEDICAL', 'LOCALE', 'LANDGRNT', 'INSTSIZE', 'CYACTIVE', 'LONGITUD', 'LATITUDE'])

ipeds = ipeds.rename(columns={'STABBR': 'STATE', 'LONGITUD': 'LONGITUDE', 'INSTNM':'INSTITUTION'})

# active institutions
ipeds_active = ipeds[(ipeds['CYACTIVE'] == 1)]

# recoding for ease of use
ipeds_active['SECTOR_R'] = ipeds_active['SECTOR'].replace({0: 'Administrative Unit', 1: 'Public, 4-year or above', 2: 'Private not-for-profit, 4-year or above', 
                                                               3: 'Private for-profit, 4-year or above', 4: 'Public, 2-year', 5: 'Private not-for-profit, 2-year',
                                                               6: 'Private for-profit, 2-year', 7: 'Public, less-than 2-year', 8: 'Private not-for-profit, less-than 2-year', 
                                                               9: 'Private for-profit, less-than 2-year', 99: 'Sector unknown (not active)'})

ipeds_active['ICLEVEL_R'] = ipeds_active['ICLEVEL'].replace({1: 'Four or more years', 2: 'At least 2 but less than 4 years', 3: 'Less than 2 years (below associate)', 
                                                          -3: '{Not available}'})

ipeds_active['CONTROL_R'] = ipeds_active['CONTROL'].replace({1: 'Public', 2: 'Private not-for-profit', 3: 'Private for-profit', -3: '{Not available}'})

ipeds_active['HDEGOFR1_R'] = ipeds_active['HDEGOFR1'].replace({11: "Doctor's degree", 12: "Doctor's degree", 
                                                               13: "Doctor's degree", 14: "Doctor's degree", 20: "Master's degree", 
                                                               30: "Bachelor's degree", 40: "Associate's degree", 0: "Non-degree granting", -3: '{Not available}'})

ipeds_active['DEGGRANT_R'] = ipeds_active['DEGGRANT'].replace({1: 'Degree-granting', 2: 'Nondegree-granting, primarily postsecondary', -3: '{Not available}'})

ipeds_active['HBCU_R'] = ipeds_active['HBCU'].replace({1: 'Yes', 2: 'No'})

ipeds_active['HOSPITAL_R'] = ipeds_active['HOSPITAL'].replace({1: 'Yes', 2: 'No', -1: 'Not reported', -2: 'Not applicable'})

ipeds_active['MEDICAL_R'] = ipeds_active['MEDICAL'].replace({1: 'Yes', 2: 'No', -1: 'Not reported', -2: 'Not applicable'})

ipeds_active['LOCALE_R'] = ipeds_active['LOCALE'].replace({11: 'City: Large', 12: 'City: Midsize',  13: 'City: Small',  21: 'Suburb: Large',  22: 'Suburb: Midsize',  
                                                           23: 'Suburb: Small',  31: 'Town: Fringe', 32: 'Town: Distant', 33: 'Town: Remote', 41: 'Rural: Fringe', 
                                                           42: 'Rural: Distant', 43: 'Rural: Remote', -3: '{Not available}'})

ipeds_active['LANDGRNT_R'] = ipeds_active['LANDGRNT'].replace({1: 'Land Grant Institution', 2: 'Not a Land Grant Institution'})

ipeds_active['INSTSIZE_R'] = ipeds_active['INSTSIZE'].replace({1: 'Under 1,000', 2: '1,000 - 4,999', 3: '5,000 - 9,999', 4: '10,000 - 19,999', 5: '20,000 and above', 
                                                               -1: '{Not available}', -2: '{Not available}'})

ipeds_active.drop(columns=['SECTOR', 'ICLEVEL', 'CONTROL', 'HDEGOFR1', 'DEGGRANT', 'HBCU', 'HOSPITAL', 'MEDICAL', 'LOCALE', 'LANDGRNT', 'INSTSIZE'], inplace=True)
ipeds_active = ipeds_active.rename(columns={'SECTOR_R':'SECTOR', 'ICLEVEL_R':'ICLEVEL', 'CONTROL_R':'CONTROL', 'HDEGOFR1_R':'HDEGOFR1', 'DEGGRANT_R':'DEGGRANT', 'HBCU_R':'HBCU', 'HOSPITAL_R':'HOSPITAL', 'MEDICAL_R':'MEDICAL', 'LOCALE_R':'LOCALE', 'LANDGRNT_R':'LANDGRNT', 'INSTSIZE_R':'INSTSIZE'})
#state lat/lons
state_coords = pd.read_csv ('state_centers.csv')
state_coords['COORDINATES'] = list(zip(state_coords['LATITUDE'], state_coords['LONGITUDE'])) #paring up lat/lon

# get long state names on main file for drop down
ipeds_active = pd.merge(ipeds_active, state_coords[['STATE_LONG', 'STATE']], on='STATE', how='left')

states = ['United States', 'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'District of Columbia', 'Florida', 'Georgia', 'Hawaii', 
    'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 
    'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 
    'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming']

total = pd.DataFrame(ipeds_active.groupby(['STATE_LONG']).size().rename('Count').reset_index())
state_counts = total.loc[total['STATE_LONG'].isin(states)] #removing territories
state_counts['Percent'] = (state_counts['Count']/ state_counts['Count'].sum())*100

# Calculate column sums
column_sums = state_counts.sum(numeric_only=True)
# Add the sums as a new row
state_counts.loc['Total'] = column_sums
state_counts.loc['Total', 'STATE_LONG'] = 'United States' #update value based on row index

# compiling state data
i_SECTOR = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'SECTOR']).size().rename('SectorCount').reset_index())
i_ICLEVEL = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'ICLEVEL']).size().rename('ICLevelCount').reset_index())
i_CONTROL = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'CONTROL']).size().rename('ControlCount').reset_index())
i_HDEGOFR1 = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'HDEGOFR1']).size().rename('HDEGOFR1Count').reset_index())
i_DEGGRANT = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'DEGGRANT']).size().rename('DEGGRANTCount').reset_index())
i_HBCU = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'HBCU']).size().rename('HBCUCount').reset_index())
i_HOSPITAL = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'HOSPITAL']).size().rename('HOSPITALCount').reset_index())
i_MEDICAL = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'MEDICAL']).size().rename('MEDICALCount').reset_index())
i_LOCALE = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'LOCALE']).size().rename('LOCALECount').reset_index())
i_LANDGRNT = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'LANDGRNT']).size().rename('LANDGRNTCount').reset_index())
i_INSTSIZE = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'INSTSIZE']).size().rename('INSTSIZECount').reset_index())

i_CONTROL_DEGREE = pd.DataFrame(ipeds_active.groupby(['STATE_LONG', 'CONTROL','HDEGOFR1']).size().rename('Count').reset_index())

# data table for viewing in app (less variables)
ipeds_data_table = ipeds_active[['INSTITUTION', 'CITY', 'STATE_LONG' , 'SECTOR', 'HDEGOFR1', 'LOCALE', 'INSTSIZE']]
ipeds_data_table = ipeds_data_table.rename(columns={'INSTITUTION': 'Institution', 'CITY': 'City', 'STATE_LONG': 'State', 'SECTOR': 'Type of Institution', 'HDEGOFR1': 'Highest Degree Offered', 
                                                    'LOCALE': 'Locale', 'INSTSIZE': 'Institution Size'})


######################################################### APP START #########################################################

ui.tags.style(
    """
    .value-box { 
        color:white !important;  
        background-color:#7F6565 !important; 
    }
    #inst_df, #size_df, #deg_df{
        font-size: 12px;
    }
    """
)
ui.page_opts(title="Colleges & Universities in the United States | 2023")

div(HTML("<br>"))

div(HTML("In 2023, there were <b>5,920</b> colleges and universities that were <i>actively open and operational</i> in the United States. The data for this application come from the Integrated Postsecondary Education Data System (IPEDS), " \
    "which gathers data annually for institutions participating in federal student financial aid programs. At the national level, the most common type of college or university is <b><i>private for-profit</i></b> (37%), <b><i>has less than 1,000 students</b></i> (57%), "
    "and is <b><i>non-degree granting</b></i> (32%). " ))

div(HTML("<br>How does your state stack up? Select a state below to learn more."))

div(HTML("<br>"))
ui.input_select("state", "Choose a State", choices=STATE_CHOICES_LONG)
ui.hr(style="border-top: 1px solid #000000;")

# adding value boxes for region, number/percentage of schools
with ui.layout_column_wrap():

    with ui.value_box(class_="value-box", showcase=icon_svg("graduation-cap"), showcase_layout= 'top right', theme="white"):
        "Number of Institutions"
        @render.ui
        def num_schools():
            df = state_counts[state_counts['STATE_LONG']== input.state()]
            count = df.iloc[0, 1]
            return f"{count:,.0f}"

    with ui.value_box(class_="value-box", showcase=icon_svg("chart-pie"), showcase_layout= 'top right', theme="white"):
        "Percentage of all US Institutions"
        @render.ui
        def pct_schools():
            df = state_counts[state_counts['STATE_LONG']== input.state()]
            pct = df.iloc[0, 2]
            return f"{pct:,.0f}%"

with ui.navset_card_underline(title="Characteristics of Colleges & Universities"):
    with ui.nav_panel("Charts", icon = icon_svg("chart-pie")):
        # donut charts
        with ui.layout_column_wrap():
            with ui.card():
                ui.card_header("Type of Institution", style="color:white; background:#543535 !important;")
                @render_plotly
                def type_pie():
                    if input.state() == "United States":
                        df = i_CONTROL
                    else:
                        df = i_CONTROL.loc[i_CONTROL['STATE_LONG'] == input.state()]

                    fig = px.pie(data_frame=df, 
                                values=df['ControlCount'], 
                                names=df['CONTROL'], 
                                color= df['CONTROL'], 
                                color_discrete_map = {'Private for-profit':'#543535', 'Private not-for-profit' : '#7D4F4F', 'Public': '#AC7C7C'}, 
                                hole= 0.7)
                    fig.update_layout(showlegend=False)
                    fig.update_traces(hovertemplate = "%{label} <br>Number of Institutions: %{value} </br>%{percent}<extra></extra>")
                    return fig
                div(HTML("<font size = '2'><b style='color:#AC7C7C;'>Public</b><br>" \
                        "<b style='color:#7D4F4F;'>Private not-for-profit</b><br>" \
                        "<b style='color:#543535;'>Private for-profit</b></font><br><br><br><br>"))

            with ui.card():
                ui.card_header("Institution Size", style="color:white; background:#543535 !important;")
                @render_plotly
                def size_pie():
                    if input.state() == "United States":
                        df = i_INSTSIZE
                    else:
                        df = i_INSTSIZE.loc[i_INSTSIZE['STATE_LONG'] == input.state()]

                    fig = px.pie(data_frame=df, 
                                values=df['INSTSIZECount'], 
                                names=df['INSTSIZE'], 
                                color= df['INSTSIZE'], 
                                color_discrete_map = {"Under 1,000":'#360000', "1,000 - 4,999" : '#700000', "5,000 - 9,999": '#B80000', "10,000 - 19,999":'#FF0D0D', 
                                                    "20,000 and above": '#FE8080', "{Not available}": '#BFBFBF'}, 
                                hole= 0.7)
                    fig.update_traces(hovertemplate = "Number of Students: %{label} <br>Number of Institutions: %{value} </br>%{percent}<extra></extra>")
                    fig.update_layout(showlegend=False)
                    return fig
                div(HTML("<font size = '2'><b style='color:#360000;'>Under 1,000</b><br>" \
                        "<b style='color:#700000;'>1,000 - 4,999</b><br>" \
                        "<b style='color:#B80000;'>5,000 - 9,999</b><br>" \
                        "<b style='color:#FF0D0D;'>10,000 - 19,999</b><br>" \
                        "<b style='color:#FE8080;'>20,000 and above</b><br>" \
                        "<b style='color:#BFBFBF;'>{Not available}</b></font>"))

            with ui.card():
                ui.card_header("Highest Degree Offered", style="color:white; background:#543535 !important;")
                @render_plotly
                def degree_pie():
                    if input.state() == "United States":
                        df = i_HDEGOFR1
                    else:
                        df = i_HDEGOFR1.loc[i_HDEGOFR1['STATE_LONG'] == input.state()]

                    fig = px.pie(data_frame=df, 
                                values=df['HDEGOFR1Count'], 
                                names=df['HDEGOFR1'], 
                                color= df['HDEGOFR1'], 
                                color_discrete_map = {"Doctor's degree":'#1C1616', "Master's degree" : '#382C2C', "Bachelor's degree": '#524040', 
                                                    "Associate's degree":'#B24444', "Non-degree granting": '#D48E8E', "{Not available}": '#BFBFBF'}, 
                                hole= 0.7)
                    fig.update_layout(showlegend=False)
                    fig.update_traces(hovertemplate = "%{label} <br>Number of Institutions: %{value} </br>%{percent}<extra></extra>") 
                    
                    fig.update_layout(showlegend=False)
                    return fig
                div(HTML("<font size = '2'><b style='color:#1C1616;'>Doctor's degree</b><br>"
                          "<b style='color:#382C2C;'>Master's degree</b><br>" 
                          "<b style='color:#524040;'>Bachelor's degree</b><br>" 
                          "<b style='color:#B24444;'>Associate's degree</b><br>" 
                          "<b style='color:#D48E8E;'>Non-degree granting</b><br>"
                          "<b style='color:#BFBFBF;'>{Not available}</b></font>"))           
   
    with ui.nav_panel("Data Tables", icon = icon_svg("table")):
        with ui.layout_column_wrap():
            with ui.card():
                ui.card_header("Type of Institution", style="color:white; background:#7F6565 !important;")
                @render.data_frame
                def inst_df():
                    df = i_CONTROL.loc[i_CONTROL['STATE_LONG'] == input.state()]
                    df_table = df[['CONTROL', 'ControlCount']]
                    df_table = df_table.rename(columns={'CONTROL': 'Type of Institution', 'ControlCount': 'Number of Institutions'})
                    return render.DataTable(df_table, height= '300px')

            with ui.card():
                ui.card_header("Institution Size", style="color:white; background:#7F6565 !important;")
                @render.data_frame
                def size_df():
                    df = i_INSTSIZE.loc[i_INSTSIZE['STATE_LONG'] == input.state()]
                    df['order'] = df['INSTSIZE'].replace({"Under 1,000": 1, "1,000 - 4,999" : 2, "5,000 - 9,999": 3, "10,000 - 19,999": 4, 
                                                    "20,000 and above": 5, "{Not available}": 6})
                    df2 = df.sort_values(['order'])
                    df_table = df2[['INSTSIZE', 'INSTSIZECount']]
                    df_table = df_table.rename(columns={'INSTSIZE': 'Number of Students', 'INSTSIZECount': 'Number of Institutions'})
                    return render.DataTable(df_table, height= '300px')

            with ui.card():
                ui.card_header("Highest Degree Offered", style="color:white; background:#7F6565 !important;")
                @render.data_frame
                def deg_df():
                    df = i_HDEGOFR1.loc[i_HDEGOFR1['STATE_LONG'] == input.state()]
                    df_table = df[['HDEGOFR1', 'HDEGOFR1Count']]
                    df_table = df_table.rename(columns={'HDEGOFR1': 'Highest Degree Offered', 'HDEGOFR1Count': 'Number of Institutions'})
                    return render.DataTable(df_table, height= '300px')            

#map
with ui.layout_columns():  
    with ui.card():
        ui.card_header("Locations of Colleges and Universities", style="color:white; background:#543535 !important;")
        @render_widget 
        #create map
        def map():
            m = Map(zoom=3, scroll_wheel_zoom =True)  
            m.layout_height = "600px"
            m.add_control(FullScreenControl())       
            icon1 = AwesomeIcon(name='book', marker_color='darkred')

            if input.state() == "United States":
                m.center = (40, -100)
            else:
                state_data = ipeds_active[ipeds_active['STATE_LONG']==input.state()]
                #college locations (get lat/lon) and add markers to map
                for (index, row) in state_data.iterrows():
                    map_markers = Marker(icon=icon1, draggable=False, location = [row.loc['LATITUDE'], row.loc['LONGITUDE']], title = row.loc['INSTITUTION'])
                    m.add_layer(map_markers)

                df = state_coords[state_coords['STATE_LONG']== input.state()]
                center = df.iat[0, 4]
                m.center = center 
                m.zoom = 7

            return m

# data table
with ui.layout_column_wrap():
    with ui.card():
        ui.card_header("Institution-Level Data", style="color:white; background:#543535 !important;")
        
        @render.data_frame
        def data_table():
            if input.state() == "United States":
                df = ipeds_data_table 
            else:    
                df = ipeds_data_table[ipeds_data_table["State"] == input.state()]
            return render.DataGrid(df)
        
        ui.card_footer("Data Source: 2023 IPEDS Institutional Characteristics, Directory Information")
