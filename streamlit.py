import streamlit as st
import pandas as pd
from urllib.parse import urljoin

st.set_page_config(layout='wide')

st.subheader('HSR Relic Filter Tool')

instruction_text = (
    '''
    (1) Select a relic set.
    (2) Select a relic piece.
    (3) Select a main stat.
    (4) (Optional) Filter by substats. Select "False" to ignore this option.
        Characters will be returned if they have a selected substat as their preferred substat.
    (5) Characters are retrieved if they use this relic, according to prydwen.
        Click the character image icon to be redirected to the prydwen page for that character.
    '''
)

with st.expander("See Instructions:"):
    st.text(instruction_text)

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
    characters_to_substat_desc = pd.read_csv(f'{TABLE_FOLDER}characters_to_substat_desc.csv')

    characters_to_imgs.index = characters_to_imgs['Character']
    characters_to_imgs = characters_to_imgs['IMG']

    characters_to_urls.index = characters_to_urls['Character']
    characters_to_urls = characters_to_urls['URL']

    characters_to_substat_desc.index = characters_to_substat_desc['Character']
    characters_to_substat_desc = characters_to_substat_desc['Substat INFO']

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
        piece_to_main_stat, # pd.DataFrame
        characters_to_substat_desc # pd.Series
    )

(
    characters_to_imgs, characters_to_urls,
    characters_to_substats, characters_to_main_stats,
    characters_to_relics,
    relics_to_imgs, relics_to_desc,
    piece_to_main_stat,
    characters_to_substat_desc
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
    relic_desc = relics_to_desc[relic].split('\n')
    for relic_info_text in relic_desc:
        st.markdown(relic_info_text)
    
    if len(relic_desc) == 1: # Planar ornaments
        possible_pieces = ['Planar Sphere', 'Link Rope', 'Any']
    elif len(relic_desc) == 2: # Cavern relics
        possible_pieces = ['Body', 'Feet', 'Head', 'Hands', 'Any']
    else:
        possible_pieces = ['Body', 'Feet', 'Planar Sphere', 'Link Rope', 'Head', 'Hands', 'Any']
    relic_piece = st.radio('Select a relic piece:', possible_pieces, index=len(possible_pieces)-1)

    main_stat = None
    if relic_piece == 'Any':
        piece_to_main_stat_filter = slice(None)
    elif relic_piece == 'Head':
        main_stat = 'HP'
    elif relic_piece == 'Hands':
        main_stat = 'ATK'
    else:
        piece_to_main_stat_filter = (piece_to_main_stat['Relic Piece'] == relic_piece)

    if main_stat is None:
        possible_main_stats = [
            main_stat
            for main_stat in piece_to_main_stat[piece_to_main_stat_filter]['Main Stat'].unique()
        ]
        main_stat = st.radio('Select a main stat:', possible_main_stats)
        character_to_main_stat_filter = (characters_to_main_stats['Main Stat'] == main_stat)
    else:
        st.write(f'The main stat is {main_stat}.')
        character_to_main_stat_filter = slice(None)

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
        st.write('Selected more than 4 substats!')
    if main_stat in substat_set:
        st.write('You cannot have a substat that is the same as the main stat!')

with col4:
    if filter_substat and isinstance(character_to_main_stat_filter, pd.Series):
        character_to_main_stat_filter = character_to_main_stat_filter | (characters_to_main_stats['Main Stat'] == 'Anything')
    if relic_piece in {'Head', 'Hands', 'Any'}:
        filtered_characters = characters_to_main_stats[character_to_main_stat_filter]['Character']
    else:
        character_to_piece_filter = (characters_to_main_stats['Relic Piece'] == relic_piece)
        filtered_characters = characters_to_main_stats[character_to_main_stat_filter & character_to_piece_filter]['Character']
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
        st.markdown(f'<a href="{character_url}"><img src="{character_img_url}" width="100" height="100"></a>', unsafe_allow_html=True)
        st.text(f'Substats: {characters_to_substat_desc[character]}')