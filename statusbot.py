import requests
import os
import logging
from credentials import telegram_token, telegram_chatid
import pandas as pd
import datetime

filename = os.path.basename(__file__)
# Import the script directory, if not defined use the current directory
try:
    from credentials import script_directory
    directory = script_directory
except:
    directory = os.path.dirname(__file__)

SUBDIR = "/statusbot"

# If subdirectory for logfile and historical listmasternodes does not exists -> create one
if not os.path.exists(directory+SUBDIR):
    os.makedirs(directory+SUBDIR)

logfile = os.path.dirname(__file__)+SUBDIR+"/"+filename.split(".")[0]+".log"

# get the current number of masternodes run by nodehub
def get_nodehub_nodes_count(source):
    for i in requests.get(source).json():
        if i["ticker"] == "DFI":
            logging.info(f"masternodes in nodehub API {i['amount']}")
            return (i["amount"])
    return 0

#get the current owneraddresses of the masternodes run by Cakedefi
def get_cake_nodes(source):
    cakenodes = []
    try:
        for i in requests.get(source).json():
            # just the DFI masternodes, not the Dash ones
            if i["coin"] == "DeFi":
                cakenodes.append(i["address"])
        logging.info(f"masternodes in Cake API {len(cakenodes)}")
        return pd.DataFrame(cakenodes,columns =['ownerAuthAddress'])

    except Exception as e:
        print (e)
        return (0)

#get all the prepared operatoraddresses from the mydefichain servers
def get_mydefichain_nodes(filename):
    mydefichainnodes = []
    try:
        with open(directory+SUBDIR+"/"+filename) as f:
            for i in f.read().split('\n'):
                mydefichainnodes.append(i)
        logging.info(f"masternodes in mydefichainlist {len(mydefichainnodes)}")
    except:
        logging.info(f"mydefichain file not found")
    return pd.DataFrame(mydefichainnodes,columns =['operatorAuthAddress'])

# get the listmasternodes from the directory at the given date
def get_listmasternodes_old(day):
    listmasternodes = pd.read_json(directory+SUBDIR+"/"+day+"-listmasternodes.json").transpose()
    logging.info(f"masternodes old listmasternodes.json {len(listmasternodes)}")
    return listmasternodes

# save the listmasternodes to the directory with current date
def set_listmasternodes_old(listmasternodes_new):
    today = datetime.datetime.now().strftime('%Y%m%d')
    listmasternodes_new.transpose().to_json(directory+SUBDIR+"/"+today+"-listmasternodes.json")

# get the actual listmasternodes from the API
def get_listmasternodes_new(source):
    try:
        listmasternodes = pd.DataFrame(requests.get(source).json()).transpose()
        logging.info(f"masternodes new listmasternodes API {len(listmasternodes)}")
        return listmasternodes
    except:
        return 0

logging.basicConfig(filename=logfile, format='%(asctime)s - %(message)s', level=logging.INFO)
logging.info("######################################")
logging.info(f"Start {filename}")

try:
    # get the actual listmasternodes
    listmasternodes_new = get_listmasternodes_new("https://api.mydeficha.in/v1/listmasternodes")
    # drop not neccesary columns
    listmasternodes = listmasternodes_new.drop(["creationHeight","resignHeight","resignTx","localMasternode","banHeight","banTx","operatorIsMine","ownerIsMine"], axis=1)

    # save the listmasternodes to the directory
    set_listmasternodes_old (listmasternodes)

    # get the listmasternodes from yesterday
    yesterday = (datetime.datetime.now()-datetime.timedelta(days=1)).strftime('%Y%m%d')
    listmasternodes_old = get_listmasternodes_old(yesterday)
    # strip the listmasternodes, only operator and minted blocks are needed
    listmasternodes_old_stripped = listmasternodes_old[['operatorAuthAddress', 'mintedBlocks']]
    # rename mintedBlocks to prevent later problems with duplicate columns
    listmasternodes_old_stripped.rename({'mintedBlocks': 'mintedBlocks_old'}, axis=1, inplace=True)

    # get cake nodes and mark with new column "cakedefi"
    cakenodes = get_cake_nodes("https://api.cakedefi.com/nodes?order=status&orderBy=DESC")
    cakenodes["cakedefi"] = True
    # get mydefichain nodes and mark with new column "mydefichain"
    mydefichain = get_mydefichain_nodes("mydefichainnodes.txt") # ToDo change to public API of masternodes which are running at mydefichain
    mydefichain["mydefichain"] = True

    # merge the old listmasternodes, the cakenodes and the mydefichain nodes to the current listmasternode
    listmasternodes = listmasternodes.merge(mydefichain,how='left').merge(cakenodes,how='left').merge(listmasternodes_old_stripped,how='left').fillna(False)

    # extract the values for easier access in the telegrammessage
    blocks_minted = {}
    blocks_minted["old_all"] = listmasternodes['mintedBlocks_old'].sum()
    blocks_minted["old_mydefichain"] = listmasternodes.loc[(listmasternodes.mydefichain == True)]['mintedBlocks_old'].sum()
    blocks_minted["old_cake"] = listmasternodes.loc[(listmasternodes.cakedefi == True)]['mintedBlocks_old'].sum()
    blocks_minted["old_unassigned"] = blocks_minted["old_all"] - blocks_minted["old_mydefichain"] - blocks_minted["old_cake"]

    blocks_minted["new_all"] = listmasternodes['mintedBlocks'].sum()
    blocks_minted["new_mydefichain"] = listmasternodes.loc[(listmasternodes.mydefichain == True)]['mintedBlocks'].sum()
    blocks_minted["new_cake"] = listmasternodes.loc[(listmasternodes.cakedefi == True)]['mintedBlocks'].sum()
    blocks_minted["new_unassigned"] = blocks_minted["new_all"] - blocks_minted["new_mydefichain"] - blocks_minted["new_cake"]

    blocks_minted["diff_all"] = blocks_minted["new_all"] - blocks_minted["old_all"]
    blocks_minted["diff_mydefichain"] = blocks_minted["new_mydefichain"] - blocks_minted["old_mydefichain"]
    blocks_minted["diff_cake"] = blocks_minted["new_cake"] - blocks_minted["old_cake"]
    blocks_minted["diff_unassigned"] = blocks_minted["new_unassigned"] - blocks_minted["old_unassigned"]

    mn_count = {}
    mn_count["new_all"] = listmasternodes.loc[(listmasternodes.state == "ENABLED")]['mintedBlocks'].count()
    mn_count["new_mydefichain"] = listmasternodes.loc[(listmasternodes.state == "ENABLED") & (listmasternodes.mydefichain == True)]['mintedBlocks'].count()
    mn_count["new_cake"] = listmasternodes.loc[(listmasternodes.state == "ENABLED") & (listmasternodes.cakedefi == True)]['mintedBlocks'].count()
    mn_count["new_nodehub"] = get_nodehub_nodes_count("https://nodehub.io/public_api/coins")
    mn_count["new_unassigned"] = mn_count["new_all"] - mn_count["new_mydefichain"] - mn_count["new_cake"] - mn_count["new_nodehub"]

    # formatted telegramtext with html Tags for "code"
    telegramtext = f"""<code>Count masternodes
24h blocks (mean searchtime)
------------------
total       {mn_count["new_all"]:4}
{blocks_minted["diff_all"]:4} ({mn_count["new_all"]/blocks_minted["diff_all"]:4.1f} days)
------------------
cakedefi    {mn_count["new_cake"]:4}
{blocks_minted["diff_cake"]:4} ({mn_count["new_cake"]/blocks_minted["diff_cake"]:4.1f} days)
community   {mn_count["new_unassigned"]:4}
{blocks_minted["diff_unassigned"]:4} ({mn_count["new_unassigned"]/blocks_minted["diff_unassigned"]:4.1f} days)
mydefichain {mn_count["new_mydefichain"]:4}
{blocks_minted["diff_mydefichain"]:4} ({mn_count["new_mydefichain"]/blocks_minted["diff_mydefichain"]:4.1f} days)
Nodehub     {mn_count["new_nodehub"]:4}
 n/a ( inf days)
------------------</code>
<a href="https://mydeficha.in/">mydefichain - Make DefiChain decentralized!</a>"""

    # send the message to the telegrambot with the given chatid
    print(telegramtext)
    requests.get(f'https://api.telegram.org/{telegram_token_statusbot}/sendMessage?chat_id={telegram_chatid_mydefichain}&parse_mode=HTML&text={telegramtext}')

except Exception as e:
    print (f"Error while fetching data {e}")
    logging.info(f"Error while fetching data {e}")

logging.info(f"End {filename}")
