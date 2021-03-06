from Mediumrare import predictor_model, gensim_nlp
import pandas as pd
import numpy as np
import re
from itertools import chain
embedder = gensim_nlp.DocEmbedder()
embedder.load_model()
_, _, labelencoder, channeldf = predictor_model.reorg_for_training(embedder.model, min_blogs=25)
bad_idx = channeldf['pub_date'].map(lambda x: len(x))<10
channeldf = channeldf.drop(channeldf.index[bad_idx])
channeldf['pub_date'] = pd.to_datetime(channeldf['pub_date'], format='%b %d, %Y')

remove_bad_chars = lambda word: re.sub('[{}"]', '', word)
channeldf['tags'] = channeldf['tags'].map(remove_bad_chars)

# %%
def most_recent_pubs(channeldf, channel, npub=3):
    meaningful_cols = ['title', 'url', 'author', 'pub_date']
    nodup_df = channeldf.drop_duplicates(subset='title')
    nodup_df['chan_title'] = nodup_df['channel'].map(lambda x: x.title().replace('-',' '))
    # nodup_df.loc[nodup_df.chan_title.isin(['thewashingtonpost']), 'chan_title'] = 'The Washington Post'
    channel_idx = nodup_df['channel'] == channel
    most_recent_idx = nodup_df.loc[channel_idx, 'pub_date'].sort_values(ascending=False)[:npub].index
    recent_pubs = nodup_df.loc[most_recent_idx, meaningful_cols]
    return list(recent_pubs.itertuples(index=False, name=None))

def mean_channel_claps(channeldf, channel):
    channel_idx = channeldf['channel'] == channel
    avg_claps = channeldf.loc[channel_idx, 'claps'].mean()
    return round(avg_claps*10)/10

def most_common_tags(channeldf, channel, ntags=3):
    channel_idx = channeldf['channel'] == channel
    tags = list(chain(*channeldf.loc[channel_idx, 'tags'].map(lambda x: x.split(',')).values))
    common_tags = pd.Series(tags).value_counts()[:ntags]
    return common_tags.index.tolist()
# %%
def most_similar_doc(channeldf, channel, newvec, d2vmodel=embedder.model):
    channel_idx = np.where(channeldf.channel==channel)[0]
    ndocs = len(d2vmodel.docvecs)
    channel_sim = d2vmodel.docvecs.most_similar(newvec, topn=ndocs)
    docid = [x[0] for x in channel_sim]
    most_similar_idx = []
    for chanid in docid:
        if chanid in channel_idx:
            most_similar_idx = chanid
            break
    similar_doc = channeldf.iloc[most_similar_idx,:].loc[['title','url']].values
    return similar_doc
