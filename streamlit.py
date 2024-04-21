import streamlit as st
import pandas as pd

from urllib.parse import urljoin

st.set_page_config(layout='wide')

st.subheader('HSR Relic Filter Tool')

st.text('''Instructions:
         
    (1) Select a relic set.
    (2) Select a main stat.
    (3) (Optional) Filter by substats. Select "False" to ignore this option.
        Characters will be returned if they have a selected substat as their preferred substat.
    (4) Characters are retrieved if they use this relic, according to prydwen.
        Click the character image icon to be redirected to the prydwen page for that character.
        ''')

TABLE_FOLDER = 'tables/'

@st.cache_data
def load_tables():
    characters_to_imgs = pd.read_csv(f'{TABLE_FOLDER}characters_to_imgs.csv')
    characters_to_urls = pd.read_csv(f'{TABLE_FOLDER}characters_to_urls.csv')
    characters_to_substats = pd.read_csv(f'{TABLE_FOLDER}characters_to_substats.csv')
    characters_to_main_stats = pd.read_csv(f'{TABLE_FOLDER}characters_to_main_stats.csv')
    characters_to_relics = pd.read_csv(f'{TABLE_FOLDER}characters_to_relics.csv')
    relics_to_imgs = pd.read_csv(f'{TABLE_FOLDER}relics_to_imgs.csv')
    relics_to_desc = pd.read_csv(f'{TABLE_FOLDER}relics_to_desc.csv')
    piece_to_main_stat = pd.read_csv(f'{TABLE_FOLDER}piece_to_main_stat.csv')

    characters_to_imgs.index = characters_to_imgs['Character']
    characters_to_imgs = characters_to_imgs['IMG']

    characters_to_urls.index = characters_to_urls['Character']
    characters_to_urls = characters_to_urls['URL']

    relics_to_imgs.index = relics_to_imgs['Relic Set']
    relics_to_imgs = relics_to_imgs['IMG']

    relics_to_desc.index = relics_to_desc['Relic Set']
    relics_to_desc = relics_to_desc['DESCRIPTION']

    return (
        characters_to_imgs, # pd.Series
        characters_to_urls, # pd.Series
        characters_to_substats, # pd.DataFrame
        characters_to_main_stats, # pd.DataFrame
        characters_to_relics, # pd.DataFrame
        relics_to_imgs, # pd.Series
        relics_to_desc, # pd.Series
        piece_to_main_stat # pd.DataFrame
    )

(
    characters_to_imgs, characters_to_urls,
    characters_to_substats, characters_to_main_stats,
    characters_to_relics,
    relics_to_imgs, relics_to_desc,
    piece_to_main_stat
) = load_tables()

col1, col2, col3, col4 = st.columns(4)
url = 'https://www.prydwen.gg/'

with col1:
    ignore_set = st.checkbox("I don't care about relic sets.")
    relic = st.radio('Select a relic set:', sorted(set(relics_to_imgs.index)))

with col2:
    st.subheader(relic)
    relic_img_url = f'{urljoin(url, relics_to_imgs[relic])}'
    st.markdown(f'![{relic}]({relic_img_url})')
    for relic_desc in relics_to_desc[relic].split('\n'):
        st.markdown(relic_desc)
    
    all_main_stats = [main_stat for main_stat in piece_to_main_stat['Main Stat'].unique() if main_stat not in ['HP', 'ATK']]
    main_stat = st.radio('Select a main stat:', all_main_stats)

with col3:
    filter_substat = st.radio('Filter by substats:', [True, False], index=1)
    possible_substats = sorted(set(characters_to_substats['Substat'].unique()))
    # st.multiselect('Select substats:', possible_substats)
    st.write('Select substats:')
    substat_set = set()
    for substat in possible_substats:
        allow_substat = st.checkbox(substat)
        if allow_substat:
            substat_set.add(substat)
    if len(substat_set) > 4:
        st.text('Selected more than 4 substats!')

with col4:
    filtered_characters = characters_to_main_stats[characters_to_main_stats['Main Stat'] == main_stat]['Character']
    if not ignore_set:
        filtered_characters = filtered_characters[
            filtered_characters.isin(
                set(
                    characters_to_relics[characters_to_relics['Relic Set'] == relic]['Character']
                )
            )
        ]
    if filter_substat:
        filtered_characters = filtered_characters[
            filtered_characters.isin(
                set(
                    characters_to_substats[characters_to_substats['Substat'].isin(substat_set)]['Character']
                )
            )
        ]
    retrieved_characters = filtered_characters.unique()
    if len(retrieved_characters) == 0:
        st.write('There are no characters that have been found to want this relic.')
    for character in retrieved_characters:
        st.subheader(character)
        character_img_url = f'{urljoin(url, characters_to_imgs[character])}'
        character_url = f'{urljoin(url, characters_to_urls[character])}'
        st.markdown(f'<a href={character_url}><img src="{character_img_url}" width="100" height="100"></a>', unsafe_allow_html=True)
        st.text('\n')